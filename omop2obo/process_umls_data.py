#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import glob
import pandas as pd

from tqdm import tqdm
from typing import Optional, Union
from omop2obo.utils import *


class UMLSDataProcessor(object):
    """Class is designed to process and prepare specific UMLS data tables needed to support mapping. This class assumes
    that at minimum, there is a directory of UMLS data files (i.e., MRCONSO.RRF, MRDEF.RRF, MRSTY.RRF, MRMAP.RRF,
    MRSAB.RRF, and MRHIER.RRF) stored in the resources/umls_data directory. Similar to the processes performed on
    ontology data by the OntologyInfoExtractor() class, this class processes the clinical data to create a Pandas
    DataFrame and dictionaries which contain the ancestor and descendant concepts for all concepts.

    Attributes:
        umls_data_files: A list of strings representing file names.
        umls_merge: A Pandas DataFrame containing merged and processed UMLS CUI data.
        mrconso: A Pandas DataFrame containing data from the UMLS MRCONSO table.
        mrdef: A Pandas DataFrame containing data from the UMLS MRDEF table.
        mrsty: A Pandas DataFrame containing data from the UMLS MRSTY table.
        mrmap: A Pandas DataFrame containing data from the UMLS MRMAP table.
        mrsab: A Pandas DataFrame containing data from the UMLS MRSAB table.
        mrhier: A Pandas DataFrame containing data from the UMLS MRHIER table.

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
        self.umls_merge: Optional[pd.DataFrame] = None

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
        DataFrame. An example row from the output DataFrame is shown below.
            CUI                                C0000783
            AUI                                A0092778
            SAB                                     MSH
            CODE                                D000020
            LABEL    Non-Steroidal Abortifacient Agents
            TTY                     Machine permutation

        Returns:
            None
        """

        print('\t- Creating DataFrame and Processing Data')
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
        DataFrame. TAn example row from the output DataFrame is shown below.
            CUI                                               C0000039
            AUI                                               A0016515
            SAB                                                    MSH
            CODE                                               D015060
            LABEL                   1,2-Dipalmitoylphosphatidylcholine
            TTY                                           Main heading
            DEF      Synthetic phospholipid used in liposomes and lipid bilayers to study biological membranes. It is
                     also a major constituent of PULMONARY SURFACTANTS.

        Returns:
            None.
        """

        print('\t- Creating DataFrame and Processing Data')
        headers = ['CUI', 'AUI', 'SAB', 'DEF']
        self.mrdef = pd.read_csv(self.mrdef, sep='|', names=headers, low_memory=False, header=None,
                                 usecols=[0, 1, 4, 5]).drop_duplicates()
        self.umls_merge = self.mrconso.merge(self.mrdef, on=['CUI', 'AUI', 'SAB'], how='left')
        self.umls_merge = self.umls_merge.fillna('None').astype(str)

        return None

    def _processes_mrsty(self) -> None:
        """Function reads in and processes data in the MRSTY.RRF file. The data are filtered and output as a Pandas
        DataFrame. An example row from the output DataFrame is shown below.
            CUI                                                       C0000005
            AUI                                                      A26634265
            SAB                                                            MSH
            CODE                                                       D012711
            LABEL                               (131)I-Macroaggregated Albumin
            TTY                                           Preferred entry term
            DEF                                                           None
            SEMANTIC_TYPE        Amino Acid, Peptide, or Protein|Pharmacologic
                                 Substance|Indicator, Reagent, or Diagnostic Aid

        Returns:
            None.
        """

        print('\t- Creating DataFrame and Processing Data')
        headers = ['CUI', 'SEMANTIC_TYPE']
        self.mrsty = pd.read_csv(self.mrsty, sep='|', names=headers, low_memory=False, header=None, usecols=[0, 3])
        self.mrsty = self.mrsty.drop_duplicates()
        # aggregate semantic types by CUI
        print('\t- Aggregating Semantic Types by CUI (this process takes several minutes)')
        mrsty_agg = aggregates_column_values(self.mrsty, 'CUI', ['SEMANTIC_TYPE'], '|')
        # merge data and aggregate semantic types by
        self.umls_merge = self.umls_merge.merge(mrsty_agg, on=['CUI'], how='left')
        self.umls_merge = self.umls_merge.fillna('None').astype(str)

        return None

    def _processes_mrmap(self) -> None:
        """Function reads in and processes data in the MRMAP.RRF file. The data are filtered and output as a Pandas
        DataFrame. An example row from the output DataFrame is shown below.
            CUI                                  C0000727
            AUI                                  A2988568
            SAB                               SNOMEDCT_US
            CODE                                  9209005
            LABEL                           Acute abdomen
            TTY                 Designated preferred name
            DEF                                      None
            SEMANTIC_TYPE                 Sign or Symptom
            RELA                                mapped_to
            TO_CODE                                 R10.0
            TO_CODE_SAB_NAME                 ICD10CM_2021

        Returns:
            None.
        """

        print('\t- Creating DataFrame and Processing Data')
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
        self.umls_merge = self.umls_merge.merge(conso_map, left_on=['CODE', 'SAB'], right_on=['FROMID', 'SAB'], how='left')
        self.umls_merge = self.umls_merge.drop(['FROMID'], axis=1).drop_duplicates()
        self.umls_merge = self.umls_merge.fillna('None').astype(str)

        return None

    def _processes_mrsab(self) -> None:
        """Function reads in and processes data in the MRSAB.RRF file. The data are filtered and output as a Pandas
        DataFrame. The resulting Pandas DataFrame is then merged with other processed UMLS data. An example row from the
        output DataFrame is shown below.
               SAB     SAB_NAME
               AIR     AI/RHEUM, 1993
               CST     COSTART, 1995
               DXP     DXplain, 1994
               LCH     Library of Congress Subject Headings, 1990

        Returns:
            None.
        """

        print('\t- Creating DataFrame and Processing Data')
        headers = ['SAB_REF', 'SAB', 'SAB_NAME', 'LANG', 'CURVER']
        self.mrsab = pd.read_csv(self.mrsab, sep='|', names=headers, low_memory=False, header=None, usecols=[2, 3, 4, 19, 21])
        self.mrsab = self.mrsab[(self.mrsab.CURVER == 'Y') & (self.mrsab.LANG == 'ENG')]
        mrsab_filtered = self.mrsab.drop(['SAB_REF', 'LANG', 'CURVER'], axis=1).drop_duplicates()
        self.umls_merge = self.umls_merge.merge(mrsab_filtered, on='SAB', how='left')
        self.umls_merge = self.umls_merge.fillna('None').astype(str)

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

        In the 'ANCS' dict, the keys are string-ints representing location in hierarchy where '0' is the immediate
        parent node of the AUI listed as the primary key. The largest number in the list is the root node.

        Returns:
            None.
        """

        print('\t- Creating DataFrame and Processing Data')
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
            UMLS_DBXREF_SAB_NAME       International Classification of Diseases, 10th
                                       Edition, Clinical Modification, 2021

        Returns:
            None.
        """

        # subset data into better structure for mapping
        label_columns = self.umls_merge[['CUI', 'AUI', 'CODE', 'LABEL', 'TTY', 'SEMANTIC_TYPE', 'SAB', 'SAB_NAME']]
        label_columns.rename(columns={'LABEL': 'STRING', 'TTY': 'STRING_TYPE'}, inplace=True)
        def_columns = self.umls_merge[['CUI', 'AUI', 'CODE', 'DEF', 'SAB', 'SAB_NAME', 'SEMANTIC_TYPE']]
        def_columns['STRING_TYPE'] = 'Definition'
        def_columns.rename(columns={'DEF': 'STRING'}, inplace=True)
        col_list = ['CUI', 'AUI', 'CODE', 'RELA', 'TO_CODE', 'TO_CODE_SAB_NAME', 'SEMANTIC_TYPE', 'SAB', 'SAB_NAME']
        dbxref_columns = self.umls_merge[col_list]
        col_v = {'TO_CODE': 'DBXREF', 'RELA': 'DBXREF_TYPE', 'TO_CODE_SAB_NAME': 'DBXREF_SAB_NAME'}
        dbxref_columns.rename(columns=col_v, inplace=True)
        # merge them back together
        col_list1 = ['CUI', 'AUI', 'CODE', 'SEMANTIC_TYPE', 'SAB', 'SAB_NAME', 'STRING', 'STRING_TYPE']
        col_list2 = ['CUI', 'AUI', 'CODE', 'SEMANTIC_TYPE', 'SAB', 'SAB_NAME']
        umls_map_df = label_columns.merge(def_columns, on=col_list1, how='left')
        umls_map_df = umls_map_df.merge(dbxref_columns, on=col_list2, how='left')
        umls_map_df['STRING'] = umls_map_df['STRING'].str.lower()
        # update column labels and values
        col_v1 = {'CUI': 'UMLS_CUI', 'AUI': 'UMLS_AUI', 'STRING_TYPE': 'UMLS_STRING_TYPE', 'SAB': 'UMLS_SAB',
                  'SEMANTIC_TYPE': 'UMLS_SEMANTIC_TYPE', 'SAB_NAME': 'UMLS_SAB_NAME', 'DBXREF_TYPE': 'UMLS_DBXREF_TYPE',
                  'DBXREF_SAB_NAME': 'UMLS_DBXREF_SAB_NAME'}
        umls_map_df.rename(columns=col_v1, inplace=True)
        # remove veterinary concepts and remove codes that are a range of codes
        umls_map_df = umls_map_df[umls_map_df['UMLS_SAB'] != 'SNOMEDCT_VET']
        rm_codes = list(umls_map_df[(umls_map_df['CODE'].str.contains('-')) & (umls_map_df['CODE'].str.contains(':'))].index)
        rm_dbx = list(umls_map_df[(umls_map_df['DBXREF'].str.contains('-')) & (umls_map_df['DBXREF'].str.contains(':'))].index)
        umls_map_df = umls_map_df.drop(rm_codes + rm_dbx)
        # add back DBXREF vocab
        dbxref_codes = self.mrsab[['SAB_REF', 'SAB', 'SAB_NAME']]
        dbxref_codes.rename(columns={'SAB': 'UMLS_DBXREF_SAB', 'SAB_NAME': 'UMLS_DBXREF_SAB_NAME'}, inplace=True)
        umls_map_df.rename(columns={'UMLS_DBXREF_SAB_NAME': 'SAB_REF'}, inplace=True)
        self.umls_merge = umls_map_df.merge(dbxref_codes, on='SAB_REF', how='left')
        self.umls_merge = self.umls_merge.drop(['SAB_REF'], axis=1)
        self.umls_merge = self.umls_merge.fillna('None').drop_duplicates()

        return None

    def data_processor(self) -> dict:
        """Function operates as a main function that processes several UMLS data tables. Two data structures are created
        and output as a single data structure. The first object is a dictionary which is keyed by UMLS AUI (see the
        processes_mrhier function for more detail). The second object is a Pandas DataFrame that contains the remaining
        UMLS tables merged into a single object (see the tidy_and_filter function for more detail). These two objects
        are pickled to: resources/umls_data/UMLS_MAP_PANEL.pkl (self.umls_merge) and
        resources/umls_data/UMLS_MAP_Ancestor_Dictionary.pkl (self.mrhier). These two objects are returned as a
        dictionary using the following keys: {'umls_full': umls_merge, 'aui_ancestors': mrhier}.

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
        print('--> Finalizing Processed Data')
        self._tidy_and_filter()

        # write data to disc --  defensive way to write pickle.write, allowing for very large files on all platforms
        print('--> Saving UMLS Mapping Data')
        filepath = 'resources/umls_data/'
        f1 = filepath + 'UMLS_MAP_PANEL.pkl'
        print('\t- Writing Pandas DataFrame Containing Processed UMLS CUIs: "{}"'.format(f1))
        pickle_large_data_structure(self.umls_merge, f1)
        f2 = filepath + 'UMLS_MAP_Ancestor_Dictionary.pkl'
        print('\t- Writing UMLS CUI Ancestor Dictionary: "{}"'.format(f2))
        pickle_large_data_structure(self.mrhier, f2)

        # combine objects into single dictionary
        umls_data_dict = {'umls_full': self.umls_merge, 'aui_ancestors': self.mrhier}

        return umls_data_dict
