#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import os
import os.path
import pickle
import shutil

from unittest import TestCase

from omop2obo.clinical_data_processor import ClinicalDataProcessor
from omop2obo.utils import *


class TestClinicalDataProcessor(TestCase):
    """Class to test functions used when processing clinical data sources."""

    def setUp(self):
        # initialize OntologyInfoExtractor instance
        current_directory = os.path.dirname(__file__)
        dir_loc = os.path.join(current_directory, 'data')
        self.dir_loc = os.path.abspath(dir_loc)
        self.clinical_data_directory = self.dir_loc + '/clinical_data'
        self.umls_data = self.clinical_data_directory + '/umls_data'
        self.omop_data = self.clinical_data_directory + '/omop_data'

        return None

    def test_initialization_umls_data(self):
        """Test class initialization for the umls_data parameter."""

        # create empty directories for testing
        self.umls_data_empty = self.clinical_data_directory + '/umls_data_empty'
        os.mkdir(self.umls_data_empty)

        # test if file is not type string
        self.assertRaises(TypeError, ClinicalDataProcessor, 1234, self.omop_data)

        # test if file exists
        self.assertRaises(OSError, ClinicalDataProcessor, self.clinical_data_directory + '/umls_fake', self.omop_data)

        # test if directory is empty
        self.assertRaises(IndexError, ClinicalDataProcessor, self.umls_data_empty, self.omop_data)

        # remove empty directory
        os.rmdir(self.umls_data_empty)

        return None

    def test_initialization_omop_data(self):
        """Test class initialization for the omop_data parameter."""

        # create empty directories for testing
        self.omop_data_empty = self.clinical_data_directory + '/omop_data_empty'
        os.mkdir(self.omop_data_empty)

        # test if file is not type string
        self.assertRaises(TypeError, ClinicalDataProcessor, self.umls_data, 1234)

        # test if file exists
        self.assertRaises(OSError, ClinicalDataProcessor, self.umls_data, self.clinical_data_directory + '/omop_fake')

        # test if directory is empty
        self.assertRaises(IndexError, ClinicalDataProcessor, self.umls_data, self.omop_data_empty)

        # remove empty directory
        os.rmdir(self.omop_data_empty)

        return None
