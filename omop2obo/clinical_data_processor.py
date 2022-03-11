#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import glob
import json
import os
import pandas as pd
import pickle
import sys

from typing import Dict, List, Optional

from omop2obo.utils import *


class ClinicalDataProcessor(object):
    """Class is designed to process and prepare specific UMLS and OMOP tables needed to support the mapping
    framework. This class assumes that at minimum, there is a directory of UMLS data files (i.e., MRCONSO.RRF,
    MRDEF.RRF, MRSTY.RRF, MRMAP.RRF, MRSAB.RRF, and MRHIER.RRF) and while optional, although optional, when provided,
    a directory of OMOP tables (i.e., concept.csv, vocabulary.csv, concept_relationship.csv,
    and concept_synonyms.csv). Similar to the processes performed on ontology data by the OntologyInfoExtractor()
    class, this class processes the clinical data to create a Pandas DataFrame and dictionaries which contain the
    ancestor and descendant concepts for all concepts.

    Attributes:
        umls_data_files: A list of strings that represent file paths.
        omop_data_files: A list of strings that represent file paths.
        master_data_dictionary: A string containing the filepath to the ontology data directory.

    Raises:
        OSError:
            If the umls_data directory exists.
            If the omop_data directory exists.
        TypeError:
            If umls_data is not a string.
            If omop_data is not a string.
        IndexError:
            If umls_data directory is empty.
            If omop_data directory is empty.
    """

    def __init__(self, umls_data: str, omop_data: Optional[str]) -> None:

        self.master_data_dictionary: Dict = {}

        # check umls data
        if not isinstance(umls_data, str):
            raise TypeError('umls_data is not type str')
        elif not os.path.exists(umls_data):
            raise OSError('The {} directory does not exist'.format(umls_data))
        elif len(glob.glob(umls_data + '/**/*.RRF', recursive=True)) == 0:
            raise IndexError('The {} directory is empty'.format(umls_data))
        else:
            self.umls_data_files: List = glob.glob(umls_data + '/**/*.RRF', recursive=True)

        # check umls data
        if not isinstance(omop_data, str):
            raise TypeError('omop_data is not type str')
        elif not os.path.exists(omop_data):
            raise OSError('The {} directory does not exist'.format(omop_data))
        elif len(glob.glob(omop_data + '/**/*.RRF', recursive=True)) == 0:
            raise IndexError('The {} directory is empty'.format(omop_data))
        else:
            self.omop_data_files: List = glob.glob(omop_data + '/**/*.RRF', recursive=True)
