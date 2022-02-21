#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import glob
import json
import os
import pandas as pd
import pickle
import sys

from omop2obo.utils import *


class ClinicalDataProcessor(object):
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
        primary_key: A string containing the column name of the primary key.
        concept_codes: A list of column names containing concept-level codes (optional).
        concept_strings: A list of column names containing concept-level labels and synonyms (optional).
        ancestor_codes: A list of column names containing ancestor concept-level codes (optional).
        ancestor_strings: A list of column names containing ancestor concept-level labels and synonyms (optional).
        umls_cui_data: A Pandas DataFrame containing UMLS CUI data from MRCONSO.RRF.
        umls_tui_data: A Pandas DataFrame containing UMLS CUI data from MRSTY.RRF.
        source_code_map: A dictionary containing clinical vocabulary source code abbreviations.
        umls_double_merge: A bool specifying whether to merge UMLS SAB codes with OMOP source codes once or twice.
            Merging once will only align OMOP source codes to UMLS SAB, twice with take the CUIs from the first merge
            and merge them again with the full UMLS SAB set resulting in a larger set of matches. The default value
            is True, which means that the merge will be performed twice.

    Raises:
        TypeError:
            If clinical_file is not type str or if clinical_file is empty.
            If source_codes is not type str or if source_codes is empty.
            If ontology_dictionary is not type dict.
            If umls_mrconso_file is not type str or if umls_mrconso_file is empty.
            If umls_mrsty_file is not type str or if umls_mrsty_file is empty.
            if primary_key is not type str.
            if concept_codes, concept_strings, ancestor_codes, and ancestor_strings (if provided) are not type list.
        OSError:
            If the clinical_file does not exist.
            If the source_codes does not  exist.
            If umls_mrconso_file does not exist.
            If umls_mrsty_file does not exist.
    """

    def __init__(self, clinical_file: str, ontology_dictionary: Dict, primary_key: str, concept_codes: Tuple,
                 concept_strings: Tuple = None, ancestor_codes: Tuple = None, ancestor_strings: Tuple = None,
                 umls_mrconso_file: str = None, umls_mrsty_file: str = None, umls_expand: bool = True,
                 source_codes: str = None) -> None:

        print('#### GENERATING EXACT MATCH MAPPINGS ####')
        print('*** Setting up Environment')

        self.umls_double_merge: bool = umls_expand