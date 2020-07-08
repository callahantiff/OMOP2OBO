#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import os
import pandas as pd  # type: ignore

from abc import ABCMeta, abstractmethod
from pandas import errors
from tqdm import tqdm  # type: ignore
from typing import Dict, List, Optional

from omop2obo.utils import data_frame_subsetter, data_frame_supersetter, merge_dictionaries


class ConceptAnnotator(object):
    """An annotator to map clinical codes to ontology terms. This workflow consists of four steps that are performed
    on data from a single clinical domain:
        1 - UMLS CUI and Semantic Type Annotation
        2 - Ontology DbXRef Mapping
        3 - Exact String Mapping to concept labels and/or synonyms
        4 - Similarity distance mapping

    Attributes:
        clinical_data: A Pandas DataFrame containing clinical data.
        ontology_dictionary: A nested dictionary containing ontology data, where outer keys are ontology identifiers
            (e.g. "hp", "mondo"), inner keys are data types (e.g. "label", "definition", "dbxref", and "synonyms").
            For each inner key, there is a third dictionary keyed by a string of that item type and with values that
            are the ontology URI for that string type.
        umls_cui_data: A Pandas DataFrame containing UMLS CUI data from MRCONSO.RRF.
        umls_tui_data: A Pandas DataFrame containing UMLS CUI data from MRSTY.RRF.

    Raises:
        TypeError:
            If clinical_file is not type str or if clinical_file is empty.
            If ontology_dictionary is not type dict.
            If umls_mrconso_file is not type str or if umls_mrconso_file is empty.
            If umls_mrsty_file is not type str or if umls_mrsty_file is empty.
        OSError:
            If the clinical_file does not exist.
            If umls_mrconso_file does not exist.
            If umls_mrsty_file does not exist.
    """

    __metaclass__ = ABCMeta

    def __init__(self, clinical_file: str, ontology_dictionary: Dict, umls_mrconso_file: str = None,
                 umls_mrsty_file: str = None) -> None:

        # clinical_file
        if not isinstance(clinical_file, str):
            raise TypeError('clinical_file must be type str.')
        elif not os.path.exists(clinical_file):
            raise OSError('The {} file does not exist!'.format(clinical_file))
        elif os.stat(clinical_file).st_size == 0:
            raise TypeError('Input file: {} is empty'.format(clinical_file))
        else:
            print('**Loading {} **'.format(clinical_file))
            try:
                self.clinical_data: pd.DataFrame = pd.read_csv(clinical_file, header=0, low_memory=False).astype(str)
            except pd.errors.ParserError:
                self.clinical_data = pd.read_csv(clinical_file, header=0, sep='\t', low_memory=False).astype(str)

        # check ontology_dictionary
        if not isinstance(ontology_dictionary, Dict): raise TypeError('ontology_dictionary must be type dict.')
        else: self.ontology_dictionary: Dict = ontology_dictionary

        # check for UMLS MRCONSO file
        if not umls_mrconso_file: self.umls_data: Optional[pd.DataFrame] = None
        else:
            if not isinstance(umls_mrconso_file, str):
                raise TypeError('umls_mrconso_file must be type str.')
            elif not os.path.exists(umls_mrconso_file):
                raise OSError('The {} file does not exist!'.format(umls_mrconso_file))
            elif os.stat(umls_mrconso_file).st_size == 0:
                raise TypeError('Input file: {} is empty'.format(umls_mrconso_file))
            else:
                print('**Loading UMLS MRCONSO Data **')
                headers = ['CUI', 'SAB', 'CODE']
                self.umls_cui_data = pd.read_csv(umls_mrconso_file, header=None, sep='|', names=headers,
                                                 low_memory=False, usecols=[0, 11, 13]).drop_duplicates().astype(str)
                self.umls_cui_data = self.umls_cui_data[self.umls_cui_data.CODE != 'NOCODE'].drop_duplicates()

        # check for UMLS MRSTY file
        if not umls_mrsty_file: self.umls_tui_data: Optional[pd.DataFrame] = None
        else:
            if not isinstance(umls_mrsty_file, str):
                raise TypeError('umls_mrsty_file must be type str.')
            elif not os.path.exists(umls_mrsty_file):
                raise OSError('The {} file does not exist!'.format(umls_mrsty_file))
            elif os.stat(umls_mrsty_file).st_size == 0:
                raise TypeError('Input file: {} is empty'.format(umls_mrsty_file))
            else:
                print('**Loading UMLS MRSTY Data **')
                headers = ['CUI', 'STY']
                self.umls_tui_data = pd.read_csv(umls_mrsty_file, header=None, sep='|', names=headers,
                                                 low_memory=False, usecols=[0, 3]).drop_duplicates().astype(str)

    def umls_cui_annotator(self, primary_key: str, code_level: str) -> pd.DataFrame:
        """Method maps concepts in a clinical data file to UMLS concepts and semantic types from the umls_cui_data
        and umls_tui_data Pandas Data Frames.

        Args:
            primary_key: A string containing the name of the primary key (i.e. CONCEPT_ID).
            code_level: A string containing the name of the source code column (i.e. CONCEPT_SOURCE_CODE).

        Returns:
           umls_cui_semtype: A Pandas DataFrame containing clinical concept ids and source codes as well as UMLS
            CUIs, source codes, and semantic types.
        """

        # reduce data to only those columns needed for merging
        clinical_ids = self.clinical_data[[primary_key, code_level]].drop_duplicates()

        # merge reduced clinical concepts with umls concepts
        umls_cui = clinical_ids.merge(self.umls_cui_data, how='inner', left_on=code_level, right_on='CODE')
        umls_cui_semtype = umls_cui.merge(self.umls_tui_data, how='left', on='CUI').drop_duplicates()

        # update column names
        updated_cols = [primary_key, code_level, 'UMLS_CUI', 'UMLS_SAB', 'UMLS_CODE', 'UMLS_SEM_TYPE']
        umls_cui_semtype.columns = updated_cols

        return umls_cui_semtype

    def dbxref_mapper(self, data: pd.DataFrame) -> pd.DataFrame:
        """Takes a stacked Pandas DataFrame and merges it with a Pandas DataFrame version of the
        ontology_dictionary_object.

        Args:
            data: A stacked Pandas DataFrame containing output from the umls_cui_annotator method.

        Returns:
            merged_dbxrefs: A stacked
        """

        # prepare ontology data
        combined_dictionaries = merge_dictionaries(self.ontology_dictionary, 'dbxref')
        combo_dict_df = pd.DataFrame(combined_dictionaries.items(), columns=['dbxref', 'Ontology_URI'])
        combo_dict_df['CODE'] = combo_dict_df['dbxref'].apply(lambda x: x.split(':')[-1])

        # merge clinical data and combined ontology dict
        merged_dbxrefs = data.merge(combo_dict_df, how='inner', on='CODE').drop_duplicates()
        merged_dbxrefs['EVIDENCE'] = merged_dbxrefs['dbxref'].apply(lambda x: 'DbXRef_' + x.split(':')[0])

        return merged_dbxrefs.drop_duplicates()

    @abstractmethod
    def gets_clinical_domain(self) -> str:
        """"A string representing the clinical domain."""

        pass


class Conditions(ConceptAnnotator):

    def gets_clinical_domain(self) -> str:
        """"A string representing the clinical domain."""

        return 'Condition Occurrence'

    def clinical_concept_mapper(self, primary_key: str, code_level: str):
        """

        Args:
            primary_key:
            code_level:

        Returns:

        """

        # TODO: figure out how to do this for both concept and concept_ancestor, maybe this is done in main
        # primary_key, code_level = 'CONCEPT_ID', 'CONCEPT_SOURCE_CODE'

        # STEP 1: UMLS CUI + SEMANTIC TYPE ANNOTATION
        if self.umls_cui_data and self.umls_tui_data:
            umls_annotations = self.umls_cui_annotator(primary_key, code_level)
            data_stacked = data_frame_subsetter(umls_annotations[[primary_key, code_level]], primary_key, [code_level])
        else:
            # prepare clinical data -- stack data
            subset_cols = [code_level, 'UMLS_CODE', 'UMLS_CUI']
            data_stacked = data_frame_subsetter(self.clinical_data[[primary_key] + subset_cols],
                                                primary_key, subset_cols)

        # STEP 2 - DBXREF ANNOTATION
        stacked_dbxref = self.dbxref_mapper(data_stacked)

        # STEP 3 - EXACT STRING MAPPING

        return None
