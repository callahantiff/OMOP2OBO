#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import os
import pandas as pd  # type: ignore

from abc import ABCMeta, abstractmethod
from pandas import errors
from typing import Optional

from omop2obo.utils.umls_api import *


class ConceptAnnotator(object):
    """An annotator to map clinical codes to ontology terms.

    Attributes:
        clinical_data: A Pandas DataFrame containing clinical data.
        ontology_dictionary: A nested dictionary containing ontology data, where outer keys are ontology identifiers
            (e.g. "hp", "mondo"), inner keys are data types (e.g. "label", "definition", "dbxref", and "synonyms").
            For each inner key, there is a third dictionary keyed by a string of that item type and with values that
            are the ontology URI for that string type.
        umls_data: A Pandas DataFrame containing UMLS CUI data.

    Raises:
        TypeError:
            If clinical_file is not type str or if clinical_file is empty.
            If ontology_dictionary is not type dict.
            If umls_file is not type str or if umls_mrconso is empty.
        OSError:
            If the clinical_file does not exist.
            If umls_file does not exist.
    """

    __metaclass__ = ABCMeta

    def __init__(self, clinical_file: str, ontology_dictionary: Dict, umls_file: str = None) -> None:

        # check clinical_file
        if not isinstance(clinical_file, str):
            raise TypeError('clinical_file must be type str.')
        elif not os.path.exists(clinical_file):
            raise OSError('The {} file does not exist!'.format(clinical_file))
        elif os.stat(clinical_file).st_size == 0:
            raise TypeError('Input file: {} is empty'.format(clinical_file))
        else:
            print('**Loading {} **'.format(clinical_file))
            try:
                self.clinical_data: pd.DataFrame = pd.read_csv(clinical_file, header=0, sep=',',
                                                               low_memory=False).astype(str)
            except pd.errors.ParserError:
                self.clinical_data = pd.read_csv(clinical_file, header=0, sep='\t',
                                                 low_memory=False).astype(str)

        # check ontology_dictionary
        if not isinstance(ontology_dictionary, Dict):
            raise TypeError('ontology_dictionary must be type dict.')
        else:
            self.ontology_dictionary: Dict = ontology_dictionary

        # check for UMLS MRCONSO file
        if not umls_file:
            self.umls_data: Optional[pd.DataFrame] = None
        else:
            if not isinstance(umls_file, str):
                raise TypeError('umls_mrconso must be type str.')
            elif not os.path.exists(umls_file):
                raise OSError('The {} file does not exist!'.format(umls_file))
            elif os.stat(umls_file).st_size == 0:
                raise TypeError('Input file: {} is empty'.format(umls_file))
            else:
                print('**Loading UMLS MRCONSO Data **')
                headers = ['CUI', 'SAB', 'CODE']
                self.umls_data = pd.read_csv(umls_file, header=None, sep='|', names=headers, low_memory=False,
                                             usecols=[0, 11, 13]).drop_duplicates().astype(str)
                self.umls_data = self.umls_data[self.umls_data.CODE != 'NOCODE'].drop_duplicates()  # remove 'NOCODE'

    def umls_annotator(self, code_type: str) -> Optional[pd.DataFrame]:
        """Method maps concepts in the map_column in a clinical data file to UMLS concepts in the umls_mrconso Pandas
        DataFrame.

        Args:
            code_type: A string containing the name of a clinical vocabulary to use when filtering the UMLS (

        Returns:
            None.

        """

        # subset DataFrames to only include columns needed for merge
        if self.umls_data:
            umls_cui = self.umls_data[self.umls_data.apply(lambda x: code_type in x['SAB'], axis=1)].drop_duplicates()
            clinical_ids = self.clinical_data[['CONCEPT_ID', 'CONCEPT_SOURCE_CODE']].drop_duplicates()

            # merge reduced concepts
            umls_merged = clinical_ids.merge(umls_cui, how='left', left_on='CONCEPT_SOURCE_CODE', right_on='CODE')

            return umls_merged[['CONCEPT_ID', 'CONCEPT_SOURCE_CODE', 'CUI']].drop_duplicates()

        else:
            return None

    @abstractmethod
    def gets_clinical_domain(self) -> str:
        """"A string representing the clinical domain."""

        pass


class Conditions(ConceptAnnotator):

    def gets_clinical_domain(self) -> str:
        """"A string representing the clinical domain."""

        return 'Condition Occurrence'
