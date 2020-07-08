#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import pickle

from unittest import TestCase

from omop2obo.clinical_concept_annotator import ConceptAnnotator
from omop2obo.utils import data_frame_subsetter


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
            self.ont_dict = pickle.load(handle)
        handle.close()

        # link to fake clinical data
        self.clinical_file = self.clinical_directory + '/sample_omop_condition_occurrence_data.csv'

        # link to stubbed UMLS data - CUIs have been scrambled
        self.umls_cui = self.mapping_directory + '/MRCONSO_FAKE.RRF'
        self.umls_tui = self.mapping_directory + '/MRSTY_FAKE.RRF'

        # initialize the class
        self.annotator = ConceptAnnotator(self.clinical_file, self.ont_dict, self.umls_cui, self.umls_tui)

        return None

    def test_initialization_clinical_file(self):
        """Test class initialization for clinical data input argument."""

        # test if file is not type string
        clinical_file_type = 1234
        self.assertRaises(TypeError, ConceptAnnotator, clinical_file_type, self.ont_dict, self.umls_cui, self.umls_tui)

        # test if file exists
        clinical_file_exists = self.clinical_directory + '/sample_omop_condition_occurrence.csv'
        self.assertRaises(OSError, ConceptAnnotator, clinical_file_exists, self.ont_dict, self.umls_cui, self.umls_tui)

        # test if file is empty
        clinical_file_empty = self.clinical_directory + '/sample_omop_condition_occurrence_data_empty.csv'
        self.assertRaises(TypeError, ConceptAnnotator, clinical_file_empty, self.ont_dict, self.umls_cui, self.umls_tui)

        return None

    def test_initialization_ontology_dict(self):
        """Test class initialization for ontologies dictionary input argument."""

        # check if ontology_dict is not type dict
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, 12, self.umls_cui, self.umls_tui)

        return None

    def test_initialization_umls_mrconso(self):
        """Test class initialization for the umls_mrconso data input argument."""

        # test if file is not type string
        mrconso_type = 1234
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, self.ont_dict, mrconso_type, self.umls_tui)

        # test if file exists
        mrconso_exists = self.mapping_directory + '/MRCONSO.RRF'
        self.assertRaises(OSError, ConceptAnnotator, self.clinical_file, self.ont_dict, mrconso_exists, self.umls_tui)

        # test if file is empty
        mrconso_empty = self.mapping_directory + '/MRCONSO_EMPTY.RRF'
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, self.ont_dict, mrconso_empty, self.umls_tui)

        return None

    def test_initialization_umls_mrsty(self):
        """Test class initialization for the umls_srdef data input argument."""

        # test if file is not type string
        mrsty_type = 1234
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, self.ont_dict, self.umls_cui, mrsty_type)

        # test if file exists
        mrsty_exists = self.mapping_directory + '/MRSTY.RRF'
        self.assertRaises(OSError, ConceptAnnotator, self.clinical_file, self.ont_dict, self.umls_cui, mrsty_exists)

        # test if file is empty
        mrsty_empty = self.mapping_directory + '/MRSTY_EMPTY.RRF'
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, self.ont_dict, self.umls_cui, mrsty_empty)

        return None

    def test_umls_cui_annotator(self):
        """Test the umls_cui_annotation method."""

        # run the method and verify the output
        umls_annotated_data = self.annotator.umls_cui_annotator('CONCEPT_ID', 'CONCEPT_SOURCE_CODE')
        self.assertTrue(len(umls_annotated_data) == 1)
        self.assertTrue(len(umls_annotated_data.columns) == 6)
        self.assertEqual(umls_annotated_data.at[0, 'UMLS_SEM_TYPE'], 'Pharmacologic Substance')

        return None

    def test_dbxref_mapper(self):
        """Tests the dbxref_mapper method."""

        # set-up input parameters
        primary_key, code_level = 'CONCEPT_ID', 'CONCEPT_SOURCE_CODE'
        subset_cols = [code_level, 'UMLS_CODE', 'UMLS_CUI']

        # run umls annotation
        umls_annotated_data = self.annotator.umls_cui_annotator(primary_key, code_level)
        umls_stack = data_frame_subsetter(umls_annotated_data[[primary_key] + subset_cols], primary_key, subset_cols)

        # get dbxrefs
        stacked_dbxref = self.annotator.dbxref_mapper(umls_stack)
        self.assertTrue(len(stacked_dbxref) == 4)
        self.assertTrue(len(stacked_dbxref.columns) == 6)
        self.assertEqual(list(stacked_dbxref.columns),
                         ['CONCEPT_ID', 'CODE', 'CODE_COLUMN', 'dbxref', 'Ontology_URI', 'EVIDENCE'])

        return None
