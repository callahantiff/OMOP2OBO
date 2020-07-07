#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import pickle

from unittest import TestCase

from omop2obo.clinical_concept_annotator import ConceptAnnotator


class TestConceptAnnotator(TestCase):
    """Class to test functions used when downloading ontology data sources."""

    def setUp(self):

        # initialize OntologyInfoExtractor instance
        current_directory = os.path.dirname(__file__)
        dir_loc = os.path.join(current_directory, 'data')
        self.dir_loc = os.path.abspath(dir_loc)
        self.clinical_directory = self.dir_loc + '/clinical_data'
        self.mapping_directory = self.dir_loc + '/mappings'

        # create some fake ontology data
        with open(self.dir_loc + '/condition_occurrence_ontology_dictionary.pickle', 'rb') as handle:
            self.ont_dictionary = pickle.load(handle)
        handle.close()

        # link to fake clinical data
        self.clinical_file = self.clinical_directory + '/sample_omop_condition_occurrence_data.csv'

        # link to fake clinical data - PLEASE DO NOT REDISTRIBUTE THIS FILE
        self.umls_mrconso = self.mapping_directory + '/MRCONSO_FAKE.RRF'

        # initialize the class
        self.annotator = ConceptAnnotator(self.clinical_file, self.ont_dictionary, self.umls_mrconso)

        return None

    def test_initialization_clinical_file(self):
        """Test class initialization for clinical data input argument."""

        # test if file is not type string
        clinical_file_type = 1234
        self.assertRaises(TypeError, ConceptAnnotator, clinical_file_type, self.ont_dictionary, self.umls_mrconso)

        # test if file exists
        clinical_file_exists = self.clinical_directory + '/sample_omop_condition_occurrence.csv'
        self.assertRaises(OSError, ConceptAnnotator, clinical_file_exists, self.ont_dictionary, self.umls_mrconso)

        # test if file is empty
        clinical_file_empty = self.clinical_directory + '/sample_omop_condition_occurrence_data_empty.csv'
        self.assertRaises(TypeError, ConceptAnnotator, clinical_file_empty, self.ont_dictionary, self.umls_mrconso)

        return None

    def test_initialization_ontology_dict(self):
        """Test class initialization for ontologies dictionary input argument."""

        # check if ontology_dict is not type dict
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, 12, self.umls_mrconso)

        return None

    def test_initialization_mrconso(self):
        """Test class initialization for the umls_mrconso data input argument."""

        # test if file is not type string
        mrconso_type = 1234
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, self.ont_dictionary, mrconso_type)

        # test if file exists
        mrconso_exists = self.mapping_directory + '/MRCONSO.RRF'
        self.assertRaises(OSError, ConceptAnnotator, self.clinical_file, self.ont_dictionary, mrconso_exists)

        # test if file is empty
        mrconso_empty = self.mapping_directory + '/MRCONSO_EMPTY.RRF'
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, self.ont_dictionary, mrconso_empty)

        return None
