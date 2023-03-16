#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import glob
import pandas as pd
import pickle
import sys

from tqdm import tqdm
from typing import Optional, Union
from omop2obo.utils import *


class UMLSDataProcessor(object):
    """Class is designed to process and prepare specific UMLS data tables needed to support mapping. This class assumes
    that at minimum, there is a directory of UMLS data files (i.e., MRCONSO.RRF, MRDEF.RRF, MRSTY.RRF, MRMAP.RRF,
    MRSAB.RRF, and MRHIER.RRF) stored in the resources/umls_data directory. Similar to the processes performed on
    ontology data by the OntologyInfoExtractor() class, this class processes the clinical data to create a Pandas
    DataFrame and dictionaries which contain the ancestor and descendant concepts for all concepts.

    Raises:
        IndexError:
            If umls_data directory is empty.
        FileNotFoundError:
            If the MRCONSO.RRF file is not in the resources/umls_data directory.
            If the MRDEF.RRF file is not in the resources/umls_data directory.
            If the MRSTY.RRF file is not in the resources/umls_data directory.
            If the MRMAP.RRF file is not in the resources/umls_data directory.
            If the MRSAB.RRF file is not in the resources/umls_data directory.
            If the MRHIER.RRF file is not in the resources/umls_data directory.
    """

    def __init__(self) -> None:
        self.umls_data_files: list = glob.glob('resources/umls_data/*AA/META/*.RRF', recursive=True)
        self.umls_merged: Optional[pd.DataFrame] = None

        # check umls data directory for needed mapping files
        if len(self.umls_data_files) == 0: raise IndexError('The "resources/umls_data" directory is empty')
        else:
            if len(self.umls_data_files) == 0:
                raise FileNotFoundError('MRCONSO.RRF missing from "resources/umls_data/"')
            else:
                self.mrconso: Union[str, pd.DataFrame] = [x for x in self.umls_data_files if 'MRCONSO' in x][0]
            if len(self.umls_data_files) == 0:
                raise FileNotFoundError('MRDEF.RRF missing from "resources/umls_data/"')
            else:
                self.mrdef: Union[str, pd.DataFrame] = [x for x in self.umls_data_files if 'MRDEF' in x][0]
            if len(self.umls_data_files) == 0:
                raise FileNotFoundError('MRSTY.RRF missing from "resources/umls_data/"')
            else:
                self.mrsty: Union[str, pd.DataFrame] = [x for x in self.umls_data_files if 'MRSTY' in x][0]
            if len(self.umls_data_files) == 0:
                raise FileNotFoundError('MRCONSO.RRF missing from "resources/umls_data/"')
            else:
                self.mrmap: Union[str, pd.DataFrame] = [x for x in self.umls_data_files if 'MRMAP' in x][0]
            if len(self.umls_data_files) == 0:
                raise FileNotFoundError('MRSAB.RRF missing from "resources/umls_data/"')
            else:
                self.mrsab: Union[str, pd.DataFrame] = [x for x in self.umls_data_files if 'MRSAB' in x][0]
            if len(self.umls_data_files) == 0:
                raise FileNotFoundError('MRHIER.RRF missing from "resources/umls_data/"')
            else:
                self.mrhier: Union[str, pd.DataFrame] = [x for x in self.umls_data_files if 'MRHIER' in x][0]


    def _processes_mrconso(self) -> None:
        """Function reads in and processes data in the MRCONSO.RRF file. The data are filtered and output as a Pandas
        DataFrame. Example output is shown below.
            CUI        AUI        SAB        CODE      LABEL                                 TTY
            C0000005   A2663426   MSH        D012711   (131)I-Macroaggregated Albumin        Preferred entry term
            C0000005   A26634266  MSH        D012711   (131)I-MAA                            Entry term
            C0000039   A28315139  RXNORM     1926948   1,2-dipalmitoylphosphatidylcholine    Name for an ingredient

        Returns:
            None
        """

        headers = ['CUI', 'LANG', 'AUI', 'SAB', 'TTY', 'CODE', 'LABEL', 'SUPPRESS']
        self.mrconso = pd.read_csv(self.mrconso, sep='|', names=headers, low_memory=False, header=None,
                                   usecols=[0, 1, 7, 11, 12, 13, 14, 16]).drop_duplicates()
        self.mrconso = self.mrconso[
            (self.mrconso.CODE != 'NOCODE') & (self.mrconso.LANG == 'ENG') & (self.mrconso.SUPPRESS != 'O')]
        self.mrconso = self.mrconso.drop(['LANG', 'SUPPRESS'], axis=1).drop_duplicates()

        # add tty labels
        print('\t- Obtaining TTY Label Information')
        u = 'https://www.nlm.nih.gov/research/umls/knowledge_sources/metathesaurus/release/abbreviations.html#mrdoc_TTY'
        tty_table = pd.read_html(u)[-2]
        self.mrconso = self.mrconso.merge(tty_table, left_on='TTY', right_on='TTY (Term Type in Source)', how='left')
        self.mrconso = self.mrconso.drop(['TTY (Term Type in Source)', 'TTY'], axis=1).drop_duplicates()
        self.mrconso.rename(columns={'TTY Description': 'TTY'}, inplace=True)

        return None

    def _processes_mrdef(self) -> None:
        """Function reads in and processes data in the MRDEF.RRF file. The data are filtered and output as a Pandas
        DataFrame. The resulting Pandas DataFrame is then merged with other processed UMLS data. Example output is shown
        below.
            CUI          AUI            SAB        DEF
            C0002404     A19049381      NCI        The sulfate salt of amantadine, a synthetic tr...
            C0002395     A1702699       JABL       A disabling degenerative disease of the nervou...
            C0002386     A0022316       MSH        The thickest and spongiest part of the maxilla...

        Returns:
            None.
        """

        headers = ['CUI', 'AUI', 'SAB', 'DEF']
        self.mrdef = pd.read_csv(self.mrdef, sep='|', names=headers, low_memory=False, header=None,
                                 usecols=[0, 1, 4, 5]).drop_duplicates()
        self.umls_merged = self.mrconso.merge(self.mrdef, on=['CUI', 'AUI', 'SAB'], how='left')

        return None

    def _processes_mrsty(self) -> None:
        """Function reads in and processes data in the MRSTY.RRF file. The data are filtered and output as a Pandas
        DataFrame. The resulting Pandas DataFrame is then merged with other processed UMLS data. Example output is shown
        below.
              CUI              SEMANTIC_TYPE
              C0000005         Amino Acid, Peptide, or Protein|Pharmacologic ...
              C0000039         Organic Chemical|Pharmacologic Substance
              C0000052         Amino Acid, Peptide, or Protein|Enzyme

        Returns:
            None.
        """

        headers = ['CUI', 'SEMANTIC_TYPE']
        self.mrsty = pd.read_csv(self.mrsty, sep='|', names=headers, low_memory=False, header=None, usecols=[0, 3]).drop_duplicates()
        # aggregate semantic types by CUI
        mrsty_agg = aggregates_column_values(self.mrsty, 'CUI', ['SEMANTIC_TYPE'], '|')
        # merge data and aggregate semantic types by
        self.umls_merged = self.umls_merged.merge(mrsty_agg, on=['CUI'], how='left')

        return None

    def _processes_mrmap(self) -> None:
        """Function reads in and processes data in the MRMAP.RRF file. The data are filtered and output as a Pandas
        DataFrame. The resulting Pandas DataFrame is then merged with other processed UMLS data. Example output is shown
        below.
            MAP_CUI    SAB           FROMID      RELA        TO_CODE   STATUS
            C5441275   SNOMEDCT_US   31820007    mapped_to   E34.9     ALWAYS E34.9
            C5441275   SNOMEDCT_US   269476000   mapped_to   C85.80    ALWAYS C85.80
            C5441275   SNOMEDCT_US   424416009   mapped_to   H27.10    ALWAYS H27.10
            C5441275   SNOMEDCT_US   126517004   mapped_to   D49.2     ALWAYS D49.2

        Returns:
            None.
        """

        headers = ['MAP_CUI', 'SAB', 'FROMID', 'RELA', 'TO_CODE', 'STATUS']
        self.mrmap = pd.read_csv(self.mrmap, sep='|', names=headers, low_memory=False, header=None,
                                 usecols=[0, 1, 6, 13, 14, 21])
        self.mrmap = self.mrmap[self.mrmap['RELA'].isin(['mapped_to', 'same_as'])].drop_duplicates()
        self.mrmap = self.mrmap[(self.mrmap.STATUS == 'ALWAYS ' + self.mrmap.TO_CODE)]
        self.mrmap.rename(columns={'MAPSETSAB': 'SAB'}, inplace=True)
        # get TOID SAB type
        conso_map = self.mrmap.merge(self.mrconso[['CUI', 'LABEL']], left_on=['MAP_CUI'], right_on=['CUI'], how='left')
        conso_map['TO_CODE_SAB_NAME'] = conso_map['LABEL'].apply(lambda x: x.split('to ')[-1].strip(' Mappings'))
        conso_map = conso_map.drop(['STATUS', 'LABEL', 'MAP_CUI', 'CUI'], axis=1).drop_duplicates()
        # merge full mrconso with mrmap
        self.umls_merged = self.umls_merged.merge(conso_map, left_on=['CODE', 'SAB'], right_on=['FROMID', 'SAB'], how='left')
        self.umls_merged = self.umls_merged.drop(['FROMID'], axis=1).drop_duplicates()

        return None

    def _processes_mrsab(self) -> None:
        """Function reads in and processes data in the MRSAB.RRF file. The data are filtered and output as a Pandas
        DataFrame. The resulting Pandas DataFrame is then merged with other processed UMLS data. Example output is shown
        below.
               SAB     SAB_NAME
               AIR     AI/RHEUM, 1993
               CST     COSTART, 1995
               DXP     DXplain, 1994
               LCH     Library of Congress Subject Headings, 1990

        Returns:
            None.
        """

        headers = ['SAB_REF', 'SAB', 'SAB_NAME', 'LANG', 'CURVER']
        self.mrsab = pd.read_csv(self.mrsab, sep='|', names=headers, low_memory=False, header=None, usecols=[2, 3, 4, 19, 21])
        self.mrsab = self.mrsab[(self.mrsab.CURVER == 'Y') & (self.mrsab.LANG == 'ENG')]
        mrsab_filtered = self.mrsab.drop(['SAB_REF', 'LANG', 'CURVER'], axis=1).drop_duplicates()
        self.umls_merged = self.umls_merged.merge(mrsab_filtered, on='SAB', how='left')
        self.umls_merged = self.umls_merged.fillna('None').astype(str)

        return None

    def _processes_mrhier(self) -> None:
        """Function reads in and processes data in the MRHIER.RRF file. The data are filtered and output as a Pandas
        DataFrame. The resulting Pandas DataFrame is then processed into a dictionary to make it easier to identify a
        concept's ancestors. Example output is shown below.
            {'A32648871': {
                    'UMLS_CUI': 'C5441266',
                    'UMLS_SAB': 'SNOMEDCT_US',
                    'ANCS': {'3': 'A3684559', '2': 'A2895444', '1': 'A3647338', '0': 'A3253161'}}
            }

        Returns:
            None.
        """

        headers = ['CUI', 'AUI', 'CXN', 'SAB', 'RELA', 'PATH']
        self.mrhier = pd.read_csv(self.mrhier, sep='|', names=headers, low_memory=False, header=None,
                                  usecols=[0, 1, 2, 4, 5, 6]).drop_duplicates()
        mrhier_filtered = self.mrhier[(self.mrhier.CXN == 1) & (self.mrhier.RELA == 'isa')]
        mrhier_filtered = mrhier_filtered.drop(['CXN', 'RELA'], axis=1).drop_duplicates()

        # create an ancestor map (move from right to left)
        print('\t- Converting Ancestor Hierarchy DataFrame to Dictionary (this process takes several minutes)')
        aui_hier_map = dict()
        for idx, row in tqdm(mrhier_filtered.iterrows(), total=mrhier_filtered.shape[0]):
            path = row['PATH'].split('.')
            aui_hier_map[row['AUI']] = {'UMLS_CUI': row['CUI'], 'UMLS_SAB': row['SAB'],
                                        'ANCS': {str(path[::-1].index(x)): x for x in path}}
        # rename object
        self.mrhier = aui_hier_map

        return None

    def _tidy_and_filter(self) -> None:
        """Function performs the final steps needed to tidy the data, perform filtering to remove non-human vocabularies
        and reformat labels. An example row of the final output is shown below.
            UMLS_CUI                                                         C0000727
            UMLS_AUI                                                         A2988568
            CODE                                                              9209005
            STRING                                                      acute abdomen
            UMLS_STRING_TYPE                                Designated preferred name
            UMLS_SEMANTIC_TYPE                                        Sign or Symptom
            UMLS_SAB                                                      SNOMEDCT_US
            UMLS_SAB_NAME                         US Edition of SNOMED CT, 2021_03_01
            UMLS_DBXREF_TYPE                                                mapped_to
            DBXREF                                                              R10.0
            UMLS_DBXREF_SAB                                                   ICD10CM
            UMLS_DBXREF_SAB_NAME    International Classification of Diseases, 10th...

        Returns:
            None.
        """

        # subset data into better structure for mapping
        print('\nConverting Merged Data into Mapping Format')
        label_columns = self.umls_merged[['CUI', 'AUI', 'CODE', 'LABEL', 'TTY', 'SEMANTIC_TYPE', 'SAB', 'SAB_NAME']]
        label_columns.rename(columns={'LABEL': 'STRING', 'TTY': 'STRING_TYPE'}, inplace=True)
        def_columns = self.umls_merged[['CUI', 'AUI', 'CODE', 'DEF', 'SAB', 'SAB_NAME', 'SEMANTIC_TYPE']]
        def_columns['STRING_TYPE'] = 'Definition'
        def_columns.rename(columns={'DEF': 'STRING'}, inplace=True)
        dbxref_columns = self.umls_merged[['CUI', 'AUI', 'CODE', 'RELA', 'TO_CODE', 'TO_CODE_SAB_NAME', 'SEMANTIC_TYPE', 'SAB', 'SAB_NAME']]
        dbxref_columns.rename(columns={'TO_CODE': 'DBXREF', 'RELA': 'DBXREF_TYPE', 'TO_CODE_SAB_NAME': 'DBXREF_SAB_NAME'}, inplace=True)
        # merge them back together
        umls_map_df = label_columns.merge(def_columns, on=[
            'CUI', 'AUI', 'CODE', 'SEMANTIC_TYPE', 'SAB', 'SAB_NAME', 'STRING', 'STRING_TYPE'], how='left')
        umls_map_df = umls_map_df.merge(dbxref_columns, on=['CUI', 'AUI', 'CODE', 'SEMANTIC_TYPE', 'SAB', 'SAB_NAME'], how='left')
        umls_map_df['STRING'] = umls_map_df['STRING'].str.lower()
        # update column labels and values
        umls_map_df.rename(columns={'CUI': 'UMLS_CUI', 'AUI': 'UMLS_AUI', 'STRING_TYPE': 'UMLS_STRING_TYPE', 'SAB': 'UMLS_SAB',
                                    'SEMANTIC_TYPE': 'UMLS_SEMANTIC_TYPE', 'SAB_NAME': 'UMLS_SAB_NAME', 'DBXREF_TYPE': 'UMLS_DBXREF_TYPE',
                                    'DBXREF_SAB_NAME': 'UMLS_DBXREF_SAB_NAME'}, inplace=True)
        # remove veterinary concepts and remove codes that are a range of codes
        umls_map_df = umls_map_df[umls_map_df['UMLS_SAB'] != 'SNOMEDCT_VET']
        rm_codes = list(umls_map_df[(umls_map_df['CODE'].str.contains('-')) & (umls_map_df['CODE'].str.contains(':'))].index)
        rm_dbx = list(umls_map_df[(umls_map_df['DBXREF'].str.contains('-')) & (umls_map_df['DBXREF'].str.contains(':'))].index)
        umls_map_df = umls_map_df.drop(rm_codes + rm_dbx)
        # add back DBXREF vocab
        dbxref_codes = self.mrsab[['SAB_REF', 'SAB', 'SAB_NAME']]
        dbxref_codes.rename(columns={'SAB': 'UMLS_DBXREF_SAB', 'SAB_NAME': 'UMLS_DBXREF_SAB_NAME'}, inplace=True)
        umls_map_df.rename(columns={'UMLS_DBXREF_SAB_NAME': 'SAB_REF'}, inplace=True)
        self.umls_merged = umls_map_df.merge(dbxref_codes, on='SAB_REF', how='left')
        self.umls_merged = self.umls_merged.drop(['SAB_REF'], axis=1)
        self.umls_merged = self.umls_merged.fillna('None').drop_duplicates()

        return None

    def data_processor(self) -> dict:
        """Function operates as a main function that processes several UMLS data tables. Two data structures are created
        and output as a single data structure. The first object is a dictionary which is keyed by UMLS AUI (see the
        processes_mrhier function for more detail). The second object is a Pandas DataFrame that contains the remaining
        UMLS tables merged into a single object (see the tidy_and_filter function for more detail). These two objects
        are added to a dictionary and pickled to: resources/umls_data/UMLS_MAP_PANEL.pkl. The internal dictionary is
        stored using the following keys: {'conso_full': umls_merged, 'aui_ancestors': mrhier}.

        Returns:
            None.
        """

        # process umls data
        print('\n' + '===' * 15 + '\nPROCESSING UMLS DATA\n' + '===' * 15)
        print('--> Processing MRCONSO.RRF')
        self._processes_mrconso()
        print('--> Processing MRDEF.RRF')
        self._processes_mrdef()
        print('--> Processing MRSTY.RRF')
        self._processes_mrsty()
        print('--> Processing MRMAP.RRF')
        self._processes_mrmap()
        print('--> Processing MRSAB.RRF')
        self._processes_mrsab()
        print('--> Processing MRHIER.RRF')
        self._processes_mrhier()

        # clean up final data set
        self._tidy_and_filter()

        # write data to disc --  defensive way to write pickle.write, allowing for very large files on all platforms
        print('--> Saving UMLS Mapping Data')
        umls_data_dict = {'conso_full': self.umls_merged, 'aui_ancestors': self.mrhier}
        max_bytes, bytes_out = 2 ** 31 - 1, pickle.dumps(umls_data_dict); n_bytes = sys.getsizeof(bytes_out)
        with open('resources/umls_data/UMLS_MAP_PANEL.pkl', 'wb') as f_out:
            for idx in range(0, n_bytes, max_bytes):
                f_out.write(bytes_out[idx:idx + max_bytes])

        return umls_data_dict
