#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import glob
# import json
import os
import pandas as pd
# import pickle
# import sys

from typing import Dict, List, Optional

from omop2obo.utils import *


class UMLSDataProcessor(object):
    """Class is designed to process and prepare specific UMLS and OMOP tables needed to support the mapping
    framework. This class assumes that at minimum, there is a directory of UMLS data files (i.e., MRCONSO.RRF,
    MRDEF.RRF, MRSTY.RRF, MRMAP.RRF, MRSAB.RRF, and MRHIER.RRF) and while optional, although optional, when provided,
    a directory of OMOP tables (i.e., concept.csv, vocabulary.csv, concept_relationship.csv,
    and concept_synonyms.csv). Similar to the processes performed on ontology data by the OntologyInfoExtractor()
    class, this class processes the clinical data to create a Pandas DataFrame and dictionaries which contain the
    ancestor and descendant concepts for all concepts.

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

    def __init__(self) -> None:

        self.umls_data_files: list = glob.glob('resources/clinical_data/*AA/META/*.RRF')
        self.mrconso: Optional[pd.DataFrame] = None
        self.mrdef: Optional[pd.DataFrame] = None
        self.mrsty: Optional[pd.DataFrame] = None
        self.mrmap: Optional[pd.DataFrame] = None
        self.mrsab: Optional[pd.DataFrame] = None
        self.mrhier: Optional[pd.DataFrame] = None

        # check umls data
        if not isinstance(umls_data, str):
            raise TypeError('umls_data is not type str')
        elif not os.path.exists(umls_data):
            raise OSError('The {} directory does not exist'.format(umls_data))
        elif len(glob.glob(umls_data + '/**/*.RRF', recursive=True)) == 0:
            raise IndexError('The {} directory is empty'.format(umls_data))
        else:
            self.umls_data_files: List = glob.glob(umls_data + '/**/*.RRF', recursive=True)


    def processes_mrconso(self):
        """Function reads in and processes data in the MRDOC.RRF file (https://www.ncbi.nlm.nih.gov/books/NBK9685/).

        Returns:
            None

        Raises:
            OSError: if the MRDOC.RRF file is missing.
            IndexError: if the MRDOC.RRF file is empty.
        """

        mrdoc_file = [x for x in self.umls_data_files if 'MRDOC' in x]
        if len(mrdoc_file) == 0: raise OSError('The MRDOC.RRF file is missing!')
        elif os.stat(mrdoc_file[0]).st_size == 0: raise IndexError('Input file: {} is empty'.format(mrdoc_file[0]))
        else:
            hds = ['VALUE', 'EXPL']
            self.mrdoc = pd.read_csv(mrdoc_file[0], sep='|', names=hds, low_memory=False, header=None, usecols=[0, 4])
            self.mrdoc.drop_duplicates(inplace=True)

        return None
    def _processes_mrsty(self):
        """

        :return:
        """

        return None
    def _processes_mrsab(self):
        """

        :return:
        """

        return None
    def _processes_mrdef(self):
        """

        :return:
        """

        return None

    def process_mrconso_data(self):
        """

        :return:
        """

        # get needed metadata
        mrsty, mrsab, mrdef = self._process_mrsty(); self._process_mrsab(); self._process_mrdef()

        # get acronym mapper
        self._process_mrdoc()

        return None

    def data_processor(self) -> pd.DataFrame:
        """

        :return:
        """

        # process umls data
        print('===' * 15 + '\nPROCESSING UMLS DATA\n' + '===' * 15)
        print('--> Processing MRCONSO')


        # process omop data


        # combine umls and omop data

        return self.clinical_data
