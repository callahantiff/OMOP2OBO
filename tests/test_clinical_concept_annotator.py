#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import pickle

from unittest import TestCase

from omop2obo.clinical_concept_annotator import ConceptAnnotator
from omop2obo.utils import column_splitter, data_frame_subsetter, normalizes_source_codes


class TestConceptAnnotator(TestCase):
    """Class to test functions used when annotating clinical concepts."""

    def setUp(self):

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

        # add clinical_data file input parameters
        self.primary_key = 'CONCEPT_ID'
        self.concept_codes = tuple(['CONCEPT_SOURCE_CODE'])
        self.concept_strings = tuple(['CONCEPT_LABEL', 'CONCEPT_SYNONYM'])
        self.ancestor_codes = tuple(['ANCESTOR_SOURCE_CODE'])
        self.ancestor_strings = tuple(['ANCESTOR_LABEL'])

        # source code map
        self.source_codes = self.mapping_directory + '/source_code_vocab_map.csv'

        # initialize the class
        self.annotator = ConceptAnnotator(self.clinical_file, self.ont_dict, self.primary_key, self.concept_codes,
                                          self.concept_strings, self.ancestor_codes, self.ancestor_strings,
                                          self.umls_cui, self.umls_tui, self.source_codes)

        return None

    def test_initialization_source_code_map(self):
        """Test class initialization for the source_code_map input argument."""

        # test if file is not type string
        source_codes_type = 1234
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, self.ont_dict, self.primary_key,
                          self.concept_codes, self.concept_strings, self.ancestor_codes, self.ancestor_strings,
                          self.umls_cui, self.umls_tui, source_codes_type)

        # test if file exists
        source_code_bad = self.mapping_directory + '/source_code_vocab_maps.csv'
        self.assertRaises(OSError, ConceptAnnotator, self.clinical_file, self.ont_dict, self.primary_key,
                          self.concept_codes, self.concept_strings, self.ancestor_codes, self.ancestor_strings,
                          self.umls_cui, self.umls_tui, source_code_bad)

        # test if file is empty
        source_code_empty = self.mapping_directory + '/empty_source_code_vocab_map.csv'

        print(os.stat(source_code_empty).st_size)
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, self.ont_dict, self.primary_key,
                          self.concept_codes, self.concept_strings, self.ancestor_codes, self.ancestor_strings,
                          self.umls_cui, self.umls_tui, source_code_empty)

        return None

    def test_initialization_clinical_file(self):
        """Test class initialization for clinical data input argument."""

        # test if file is not type string
        clinical_file_type = 1234
        self.assertRaises(TypeError, ConceptAnnotator, clinical_file_type, self.ont_dict, self.primary_key,
                          self.concept_codes, self.concept_strings, self.ancestor_codes, self.ancestor_strings,
                          self.umls_cui, self.umls_tui, self.source_codes)

        # test if file exists
        clinical_file_exists = self.clinical_directory + '/sample_omop_condition_occurrence.csv'
        self.assertRaises(OSError, ConceptAnnotator, clinical_file_exists, self.ont_dict, self.primary_key,
                          self.concept_codes, self.concept_strings, self.ancestor_codes, self.ancestor_strings,
                          self.umls_cui, self.umls_tui, self.source_codes)

        # test if file is empty
        clinical_file_empty = self.clinical_directory + '/sample_omop_condition_occurrence_data_empty.csv'
        self.assertRaises(TypeError, ConceptAnnotator, clinical_file_empty, self.ont_dict, self.primary_key,
                          self.concept_codes, self.concept_strings, self.ancestor_codes, self.ancestor_strings,
                          self.umls_cui, self.umls_tui, self.source_codes)

        return None

    def test_initialization_ontology_dict(self):
        """Test class initialization for ontologies dictionary input argument."""

        # check if ontology_dict is not type dict
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, 12, self.primary_key, self.concept_codes,
                          self.concept_strings, self.ancestor_codes, self.ancestor_strings, self.umls_cui,
                          self.umls_tui, self.source_codes)

        return None

    def test_initialization_primary_key(self):
        """Test the primary_key input parameter."""

        # check if primary_key is not a string
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, self.ont_dict, 123456, self.concept_codes,
                          self.concept_strings, self.ancestor_codes, self.ancestor_strings, self.umls_cui,
                          self.umls_tui, self.source_codes)

        return None

    def test_initialization_concept_codes(self):
        """Test the concept_codes input parameter."""

        # check if clinical_codes are a list
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, self.ont_dict, self.primary_key, 'codes',
                          self.concept_strings, self.ancestor_codes, self.ancestor_strings, self.umls_cui,
                          self.umls_tui, self.source_codes)

        return None

    def test_initialization_concept_strings(self):
        """Test the concept_string input parameter."""

        # check if clinical_strings are a list
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, self.ont_dict, self.primary_key,
                          self.concept_codes, 'labels', self.ancestor_codes, self.ancestor_strings, self.umls_cui,
                          self.umls_tui, self.source_codes)

        # check if clinical_strings are none
        annotator = ConceptAnnotator(self.clinical_file, self.ont_dict, self.primary_key, self.concept_codes,
                                     None, self.ancestor_codes, self.ancestor_strings, self.umls_cui, self.umls_tui,
                                     self.source_codes)

        self.assertEqual(annotator.concept_strings, None)

        return None

    def test_initialization_ancestor_codes(self):
        """Test the concept_codes input parameter."""

        # check if ancestor_codes are a list
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, self.ont_dict, self.primary_key,
                          self.concept_codes, self.concept_strings, 'codes', self.ancestor_strings, self.umls_cui,
                          self.umls_tui, self.source_codes)

        # check if ancestor_codes are none
        annotator = ConceptAnnotator(self.clinical_file, self.ont_dict, self.primary_key, self.concept_codes,
                                     self.concept_strings, None, self.ancestor_strings, self.umls_cui, self.umls_tui,
                                     self.source_codes)

        self.assertEqual(annotator.ancestor_codes, None)

        return None

    def test_initialization_ancestor_strings(self):
        """Test the ancestor_string input parameter."""

        # check if ancestor_strings are a list
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, self.ont_dict, self.primary_key,
                          self.concept_codes, self.concept_strings, 'labels', self.ancestor_strings, self.umls_cui,
                          self.umls_tui, self.source_codes)

        # check if ancestor_strings are none
        annotator = ConceptAnnotator(self.clinical_file, self.ont_dict, self.primary_key, self.concept_codes,
                                     self.concept_strings, self.ancestor_codes, None, self.umls_cui, self.umls_tui,
                                     self.source_codes)

        self.assertEqual(annotator.ancestor_strings, None)

        return None

    def test_initialization_umls_mrconso(self):
        """Test class initialization for the umls_mrconso data input argument."""

        # test if file is not type string
        mrconso_type = 1234
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, self.ont_dict, self.primary_key,
                          self.concept_codes, self.concept_strings, self.ancestor_codes, self.ancestor_strings,
                          mrconso_type, self.umls_tui, self.source_codes)

        # test if file exists
        mrconso_exists = self.mapping_directory + '/MRCONSO.RRF'
        self.assertRaises(OSError, ConceptAnnotator, self.clinical_file, self.ont_dict, self.primary_key,
                          self.concept_codes, self.concept_strings, self.ancestor_codes, self.ancestor_strings,
                          mrconso_exists, self.umls_tui, self.source_codes)

        # test if file is empty
        mrconso_empty = self.mapping_directory + '/MRCONSO_EMPTY.RRF'
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, self.ont_dict, self.primary_key,
                          self.concept_codes, self.concept_strings, self.ancestor_codes, self.ancestor_strings,
                          mrconso_empty, self.umls_tui, self.source_codes)

        return None

    def test_initialization_umls_mrsty(self):
        """Test class initialization for the umls_srdef data input argument."""

        # test if file is not type string
        mrsty_type = 1234
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, self.ont_dict, self.primary_key,
                          self.concept_codes, self.concept_strings, self.ancestor_codes, self.ancestor_strings,
                          self.umls_cui, mrsty_type, self.source_codes)

        # test if file exists
        mrsty_exists = self.mapping_directory + '/MRSTY.RRF'
        self.assertRaises(OSError, ConceptAnnotator, self.clinical_file, self.ont_dict, self.primary_key,
                          self.concept_codes, self.concept_strings, self.ancestor_codes, self.ancestor_strings,
                          self.umls_cui, mrsty_exists, self.source_codes)

        # test if file is empty
        mrsty_empty = self.mapping_directory + '/MRSTY_EMPTY.RRF'
        self.assertRaises(TypeError, ConceptAnnotator, self.clinical_file, self.ont_dict, self.primary_key,
                          self.concept_codes, self.concept_strings, self.ancestor_codes,
                          self.ancestor_strings, self.umls_cui, mrsty_empty, self.source_codes)

        return None

    def test_umls_cui_annotator_default(self):
        """Test the umls_cui_annotation method when using the default merge strategy."""

        # set-up parameters
        code_level = 'CONCEPT_SOURCE_CODE'

        # prep data before running code
        data, source_codes = self.annotator.clinical_data.copy(), self.annotator.source_code_map
        data[code_level] = normalizes_source_codes(data[code_level].to_frame(), source_codes)

        # run the method and verify the output
        umls_annotated_data = self.annotator.umls_cui_annotator(data, 'CONCEPT_ID', 'CONCEPT_SOURCE_CODE')
        self.assertTrue(len(umls_annotated_data) == 3)
        self.assertTrue(len(umls_annotated_data.columns) == 6)
        self.assertEqual(umls_annotated_data.at[0, 'UMLS_SEM_TYPE'], 'Amino Acid, Peptide, or Protein')

        return None

    def test_umls_cui_annotator_not_default(self):
        """Test the umls_cui_annotation method when not using the default merge strategy."""

        # set-up parameters
        code_level = 'CONCEPT_SOURCE_CODE'

        # prep data before running code
        data, source_codes = self.annotator.clinical_data.copy(), self.annotator.source_code_map
        data[code_level] = normalizes_source_codes(data[code_level].to_frame(), source_codes)

        # run the method and verify the output
        umls_annotated_data = self.annotator.umls_cui_annotator(data, 'CONCEPT_ID', 'CONCEPT_SOURCE_CODE', 'yes')
        self.assertTrue(len(umls_annotated_data) == 66)
        self.assertTrue(len(umls_annotated_data.columns) == 6)
        self.assertEqual(umls_annotated_data.at[0, 'UMLS_SEM_TYPE'], 'Amino Acid, Peptide, or Protein')

        return None

    def test_dbxref_mapper(self):
        """Tests the dbxref_mapper method."""

        # set-up input parameters
        primary_key, code_level = 'CONCEPT_ID', 'CONCEPT_SOURCE_CODE'
        subset_cols = [code_level, 'UMLS_CODE', 'UMLS_CUI']

        # prep data before running code
        data, source_codes = self.annotator.clinical_data.copy(), self.annotator.source_code_map
        data[code_level] = normalizes_source_codes(data[code_level].to_frame(), source_codes)
        self.annotator.clinical_data = data

        # run umls annotation
        umls_annotated_data = self.annotator.umls_cui_annotator(data, primary_key, code_level)
        umls_stack = data_frame_subsetter(umls_annotated_data[[primary_key] + subset_cols], primary_key, subset_cols)

        # get dbxrefs
        stacked_dbxref = self.annotator.dbxref_mapper(umls_stack, 'CONCEPT_ID', 'concept')
        self.assertTrue(len(stacked_dbxref) == 2)
        self.assertTrue(len(stacked_dbxref.columns) == 5)
        self.assertEqual(list(stacked_dbxref.columns), ['CONCEPT_ID', 'CONCEPT_DBXREF_ONT_URI',
                                                        'CONCEPT_DBXREF_ONT_TYPE', 'CONCEPT_DBXREF_ONT_LABEL',
                                                        'CONCEPT_DBXREF_ONT_EVIDENCE'])
        return None

    def test_exact_string_mapper(self):
        """Tests the exact_string_mapper method."""

        # prepare input data
        primary_key, code_strings = 'CONCEPT_ID', ['CONCEPT_LABEL', 'CONCEPT_SYNONYM']
        clinical_strings = self.annotator.clinical_data.copy()[[primary_key] + code_strings]
        split_strings = column_splitter(clinical_strings, primary_key, code_strings, '|')
        split_strings = split_strings[[primary_key] + code_strings]
        split_strings_stacked = data_frame_subsetter(split_strings, primary_key, code_strings)

        # test method
        stacked_strings = self.annotator.exact_string_mapper(split_strings_stacked, 'CONCEPT_ID', 'concept')
        self.assertTrue(len(stacked_strings) == 2)
        self.assertTrue(len(stacked_strings.columns) == 5)
        self.assertEqual(list(stacked_strings.columns), ['CONCEPT_ID', 'CONCEPT_STR_ONT_URI', 'CONCEPT_STR_ONT_TYPE',
                                                         'CONCEPT_STR_ONT_LABEL', 'CONCEPT_STR_ONT_EVIDENCE'])

        return None

    def test_clinical_concept_mapper(self):
        """Tests the clinical_concept_mapper method."""

        # test method
        results = self.annotator.clinical_concept_mapper()
        self.assertTrue(len(results) == 4)
        self.assertTrue(len(results.columns) == 30)

        return None

    def test_clinical_concept_mapper_no_umls(self):
        """Tests the clinical_concept_mapper method when no MRCONSO or MRSTY data are provided."""

        # change input parameters
        self.annotator.umls_cui_data = None
        self.annotator.umls_tui_data = None

        # test method
        results = self.annotator.clinical_concept_mapper()
        self.assertTrue(len(results) == 4)
        self.assertTrue(len(results.columns) == 26)

        return None

    def test_clinical_concept_mapper_no_ancestors(self):
        """Tests the clinical_concept_mapper method when no ancestor data is provided."""

        # change input parameters
        self.annotator.ancestor_codes = None
        self.annotator.ancestor_strings = None

        # test method
        results = self.annotator.clinical_concept_mapper()
        self.assertTrue(len(results) == 4)
        self.assertTrue(len(results.columns) == 19)

        return None

    def test_clinical_concept_mapper_no_umls_no_ancestors(self):
        """Tests the clinical_concept_mapper method when no umls data is input and ancestor data is provided."""

        # change input parameters
        self.annotator.ancestor_codes = None
        self.annotator.ancestor_strings = None
        self.annotator.umls_cui_data = None
        self.annotator.umls_tui_data = None

        # test method
        results = self.annotator.clinical_concept_mapper()
        self.assertTrue(len(results) == 4)
        self.assertTrue(len(results.columns) == 14)

        return None
