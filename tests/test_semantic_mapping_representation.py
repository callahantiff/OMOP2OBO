#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import os
import os.path
import shutil

from rdflib import Graph, URIRef
from typing import Dict, List
from unittest import TestCase

from omop2obo.semantic_mapping_representation import SemanticMappingTransformer


class TestSemanticMappingTransformer(TestCase):
    """Class to test functions used when converting the omop2obo mapping set to RDF."""

    def setUp(self):
        # initialize data directories
        current_directory = os.path.dirname(__file__)
        dir_loc1 = os.path.join(current_directory, 'data')
        self.dir_loc1 = os.path.abspath(dir_loc1)
        self.ontology_directory = self.dir_loc1 + '/ontologies'
        self.mapping_directory = self.dir_loc1 + '/mappings'

        # create a second location
        dir_loc2 = os.path.join(current_directory, 'resources')
        self.dir_loc2 = os.path.abspath(dir_loc2)
        self.resources_directory = self.dir_loc2 + '/mapping_semantics'

        # create pointer to testing utilities
        dir_loc3 = os.path.join(current_directory, 'utils/owltools')
        self.owltools_location = os.path.abspath(dir_loc3)

        # create input parameters
        self.ontology_list = ['HP', 'MONDO']
        self.omop2obo_data_file = self.mapping_directory + '/omop2obo_mapping_data.xlsx'
        self.ontology_directory = self.ontology_directory
        self.map_type = 'single'
        self.superclasses = None

        # move relation data to main semantic directory
        shutil.copyfile(self.dir_loc1 + '/omop2obo_class_relations.txt',
                        self.resources_directory + '/omop2obo_class_relations.txt')

        # create test data
        self.test_relations_dict = {
            'conditions': {'relations': {'MONDO-HP': URIRef('http://purl.obolibrary.org/obo/RO_0002200')}},
            'drugs': {'relations': {'CHEBI-VO': URIRef('http://purl.obolibrary.org/obo/RO_0002180'),
                                    'CHEBI-PR': URIRef('http://purl.obolibrary.org/obo/RO_0002180'),
                                    'VO-NCBITAXON': URIRef('http://purl.obolibrary.org/obo/RO_0002162'),
                                    'PR-NCBITAXON': URIRef('http://purl.obolibrary.org/obo/RO_0002162')}},
            'measurements': {'relations': {'HP-UBERON': URIRef('http://purl.obolibrary.org/obo/RO_0002479'),
                                           'HP-CL': URIRef('http://purl.obolibrary.org/obo/RO_0002180'),
                                           'HP-CHEBI': URIRef('http://purl.obolibrary.org/obo/RO_0002180'),
                                           'HP-PR': URIRef('http://purl.obolibrary.org/obo/RO_0002180'),
                                           'PR-CHEBI': URIRef('http://purl.obolibrary.org/obo/RO_0004028'),
                                           'CL-NCBITAXON': URIRef('http://purl.obolibrary.org/obo/RO_0002162'),
                                           'CHEBI-NCBITAXON': URIRef(
                                               'http://purl.obolibrary.org/obo/RO_0002162'),
                                           'PR-NCBITAXON': URIRef('http://purl.obolibrary.org/obo/RO_0002162'),
                                           'UBERON-NCBITAXON': URIRef(
                                               'http://purl.obolibrary.org/obo/RO_0002162')}}}

        # instantiate semantic transformation class
        self.map_transformer = SemanticMappingTransformer(['so', 'vo'], self.omop2obo_data_file, 'condition',
                                                          self.map_type, self.ontology_directory)

        # make sure that instantiated class points to testing data location of the OWLTools API
        self.map_transformer.owltools_location = self.owltools_location

        return None

    def test_input_ontology_list_list(self):
        """Tests the ontology list input parameter when input is a list."""

        # catch when ontology list is a list
        self.assertRaises(TypeError, SemanticMappingTransformer, 1234, self.omop2obo_data_file, 'condition',
                          self.map_type, self.ontology_directory, self.superclasses)

        return None

    def test_input_ontology_list_empty(self):
        """Tests the ontology list input parameter when input is empty."""

        # catch when ontology list is empty
        self.assertRaises(ValueError, SemanticMappingTransformer, [], self.omop2obo_data_file, 'condition',
                          self.map_type, self.ontology_directory, self.superclasses)

        return None

    def test_input_mapping_data_not_string(self):
        """Tests the omop2obo mapping data file input parameter when input is not a string."""

        # catch when omo2obo data file input is not a string
        self.assertRaises(TypeError, SemanticMappingTransformer, ['so'], 1234, 'condition', self.map_type,
                          self.ontology_directory, self.superclasses)

        return None

    def test_input_mapping_data_bad_path(self):
        """Tests the omop2obo mapping data file input parameter when file path does not exist."""

        # catch when omo2obo data file points to a path that does not exist
        self.assertRaises(OSError, SemanticMappingTransformer, ['so'], self.mapping_directory + '/fake+data_path.csv',
                          'condition', self.map_type, self.ontology_directory, self.superclasses)

        return None

    def test_input_mapping_data_empty_file(self):
        """Tests the omop2obo mapping data file input parameter when file is empty."""

        # catch when omo2obo data file input points to an empty file
        empty_data_file = self.ontology_directory + '/empty_hp_without_imports.owl'
        self.assertRaises(TypeError, SemanticMappingTransformer, ['so'], empty_data_file, 'condition', self.map_type,
                          self.ontology_directory, self.superclasses)

        return None

    def test_input_ontology_directory_not_exist(self):
        """Tests the ontology directory input parameter when the directory does not exist."""

        # catch when ontology_directory does not exist
        ontology_directory = self.dir_loc1 + '/ontologie'
        self.assertRaises(OSError, SemanticMappingTransformer, ['so'], self.omop2obo_data_file,
                          'condition', self.map_type, ontology_directory, self.superclasses)

        return None

    def test_input_ontology_directory_bad_directory(self):
        """Tests the ontology directory input parameter when the directory is incorrect."""

        # catch when ontology_directory is empty b/c there are no ontology data files
        os.mkdir(self.dir_loc1 + '/temp_ontologies')
        ontology_directory = self.dir_loc1 + '/temp_ontologies'
        self.assertRaises(TypeError, SemanticMappingTransformer, ['so'], self.omop2obo_data_file, 'condition',
                          self.map_type, ontology_directory, self.superclasses)
        os.rmdir(self.dir_loc1 + '/temp_ontologies')

        return None

    def test_input_ontology_directory_empty_directory(self):
        """Tests the ontology directory input parameter when directory is empty."""

        # catch when ontology_directory is empty b/c there are no ontology data files from
        self.assertRaises(ValueError, SemanticMappingTransformer, ['cl'], self.omop2obo_data_file, 'condition',
                          self.map_type, self.ontology_directory, self.superclasses)

        return None

    def test_input_domain_string(self):
        """Tests the domain input parameter is type string."""

        # test that input is string
        self.assertRaises(TypeError, SemanticMappingTransformer, ['so', 'vo'], self.omop2obo_data_file, 1234,
                          self.map_type, self.ontology_directory)

        return None

    def test_input_domain_correct_type(self):
        """Tests the domain input parameter is one of the three possible input types."""

        # test that input is in list of expected domains
        self.assertRaises(ValueError, SemanticMappingTransformer, ['so', 'vo'], self.omop2obo_data_file, 'conditions',
                          self.map_type, self.ontology_directory)

        return None

    def test_input_mapping_approach_type(self):
        """Tests the mapping approach type input parameter."""

        # when mapping type is not None
        self.assertRaises(TypeError, SemanticMappingTransformer, ['so'], self.omop2obo_data_file, 'condition', 123,
                          self.ontology_directory, self.superclasses)

        test_method = SemanticMappingTransformer(ontology_list=['so'], omop2obo_data_file=self.omop2obo_data_file,
                                                 domain='condition', ontology_directory=self.ontology_directory,
                                                 superclasses=self.superclasses)

        self.assertEqual(test_method.construction_type, 'multi')

        return None

    def test_input_subclass_dict(self):
        """Tests the subclass_dict input parameter."""

        # create dict to test method output
        test_dict = {'condition': {'phenotype': URIRef('http://purl.obolibrary.org/obo/HP_0000118'),
                                   'disease': URIRef('http://purl.obolibrary.org/obo/MONDO_0000001')},
                     'drug': URIRef('http://purl.obolibrary.org/obo/CHEBI_24431'),
                     'measurement': URIRef('http://purl.obolibrary.org/obo/HP_0000118')}

        # check when subclass dict input is None
        test_method1 = SemanticMappingTransformer(['so'], self.omop2obo_data_file, 'condition', 'multi',
                                                  self.ontology_directory, self.superclasses)
        self.assertIsInstance(test_method1.superclass_dict, Dict)
        self.assertEqual(test_method1.superclass_dict, test_dict)

        # check when subclass dict is not None
        self.assertRaises(TypeError, SemanticMappingTransformer, ['so'], self.omop2obo_data_file, 'condition', 'multi',
                          self.ontology_directory, 123, 'not a dict')

        # check when construction type is single that the subclass dict is None
        test_method2 = SemanticMappingTransformer(['so'], self.omop2obo_data_file, 'condition', 'single',
                                                  self.ontology_directory)
        self.assertEqual(test_method2.superclass_dict, None)

        return None

    def test_input_ontology_relations_single_construction(self):
        """Tests the multi-ontology class relations data when construction type is not "multi"."""

        # test when construction type is not "multi"
        test_method = SemanticMappingTransformer(ontology_list=['so'], omop2obo_data_file=self.omop2obo_data_file,
                                                 ontology_directory=self.ontology_directory, map_type='single',
                                                 domain='condition', superclasses=self.superclasses)
        self.assertEqual(test_method.multi_class_relations, None)

        return None

    def test_input_ontology_relations_no_relations_file(self):
        """Tests the multi-ontology class relations data when the relations file does not exist."""

        # test when relations file does not exist
        os.remove(self.resources_directory + '/omop2obo_class_relations.txt')
        self.assertRaises(OSError, SemanticMappingTransformer, ['so'], self.omop2obo_data_file, 'condition', 'multi',
                          self.ontology_directory)

        return None

    def test_input_ontology_relations_empty_relations(self):
        """Tests the multi-ontology class relations data when relations data is empty."""

        # move and rename empty file into repo
        shutil.copyfile(self.dir_loc1 + '/omop2obo_class_relations_empty.txt',
                        self.resources_directory + '/omop2obo_class_relations.txt')
        self.assertRaises(TypeError, SemanticMappingTransformer, ['so'], self.omop2obo_data_file, 'condition', 'multi',
                          self.ontology_directory)

        # clean up environment
        os.remove('resources/mapping_semantics/omop2obo_class_relations.txt')

        return None

    def test_input_ontology_relations_correct_formatting(self):
        """Tests the multi-ontology class relations data when file is correct - in order to test output."""

        # check output when file correctly formatted
        shutil.copyfile(self.dir_loc1 + '/omop2obo_class_relations.txt',
                        self.resources_directory + '/omop2obo_class_relations.txt')
        test_method2 = SemanticMappingTransformer(ontology_list=['so'], omop2obo_data_file=self.omop2obo_data_file,
                                                  ontology_directory=self.ontology_directory,
                                                  domain='condition', map_type='multi', superclasses=self.superclasses)
        self.assertEqual(test_method2.multi_class_relations, self.test_relations_dict)

        # clean up environment
        os.remove('resources/mapping_semantics/omop2obo_class_relations.txt')

        return None

    def test_find_existing_omop2obo_data(self):
        """"Tests the search for existing omop2obo mapping ontology data."""

        # test when there is not an existing omop2obo mapping file present
        test_method1 = SemanticMappingTransformer(ontology_list=['so'], omop2obo_data_file=self.omop2obo_data_file,
                                                  ontology_directory=self.ontology_directory,
                                                  domain='condition', map_type='multi', superclasses=self.superclasses)
        self.assertEqual(test_method1.current_omop2obo, None)

        # test when there is not an existing omop2obo mapping file present
        shutil.copyfile(self.ontology_directory + '/so_without_imports.owl',
                        self.resources_directory + '/omop2obo_v0.owl')
        test_method2 = SemanticMappingTransformer(ontology_list=['so'], omop2obo_data_file=self.omop2obo_data_file,
                                                  ontology_directory=self.ontology_directory,
                                                  domain='condition', map_type='multi', superclasses=self.superclasses)

        self.assertEqual(test_method2.current_omop2obo, 'resources/mapping_semantics/omop2obo_v0.owl')

        # clean up environment
        os.remove('resources/mapping_semantics/omop2obo_v0.owl')

        return None

    def test_loads_ontology_data_single_construction(self):
        """Tests the loads_ontology_data method for a single class construction type."""

        # run the method to load ontology data
        ont_dictionary = self.map_transformer.loads_ontology_data()

        # check output
        self.assertIsInstance(ont_dictionary, Dict)

        return None

    def test_loads_ontology_data_multi_construction(self):
        """Tests the loads_ontology_data method for a multi class construction type."""

        # instantiate method
        self.map_transformer2 = SemanticMappingTransformer(['so', 'vo'], self.omop2obo_data_file, 'condition', 'multi',
                                                           self.ontology_directory)
        self.map_transformer2.owltools_location = self.owltools_location

        # run the method to load ontology data
        ont_dictionary = self.map_transformer2.loads_ontology_data()
        print(len(ont_dictionary['merged']))

        # check output
        self.assertIsInstance(ont_dictionary, Dict)
        self.assertIn('merged', ont_dictionary.keys())
        self.assertIsInstance(ont_dictionary['merged'], Graph)
        self.assertEqual(len(ont_dictionary['merged']), 127283)

        # remove file
        merged_ontology_file = glob.glob(self.ontology_directory + '/OMOP2OBO_MergedOntologies_*.owl')[0]
        os.remove(merged_ontology_file)

        return None

    def test_extracts_logic_information_na(self):
        """Tests the extracts_logic_information method when logic is 'N/A'."""

        # test simple logic - N/A
        logic = 'N/A'
        constructors = [x for x in ['AND', 'OR', 'NOT'] if x in logic][::-1]
        na_test = self.map_transformer.extracts_logic_information(logic, constructors.copy())

        # test results
        self.assertIsInstance(na_test, List)
        self.assertEqual(na_test, [])

        return None

    def test_extracts_logic_information_and(self):
        """Tests the extracts_logic_information method when logic string contains 'AND' constructor."""

        # test simple logic - AND
        logic = 'AND(0, 1)'
        constructors = [x for x in ['AND', 'OR', 'NOT'] if x in logic][::-1]
        and_test = self.map_transformer.extracts_logic_information(logic, constructors.copy())

        # test results
        self.assertIsInstance(and_test, List)
        self.assertEqual(and_test, [['AND', '0, 1']])

        return None

    def test_extracts_logic_information_or(self):
        """Tests the extracts_logic_information method when logic string contains 'OR' constructor."""

        # test simple logic - OR
        logic = 'OR(0, 1)'
        constructors = [x for x in ['AND', 'OR', 'NOT'] if x in logic][::-1]
        or_test = self.map_transformer.extracts_logic_information(logic, constructors.copy())

        # test results
        self.assertIsInstance(or_test, List)
        self.assertEqual(or_test, [['OR', '0, 1']])

        return None

    def test_extracts_logic_information_not(self):
        """Tests the extracts_logic_information method when logic string contains 'NOT' constructor."""

        # test simple logic - NOT
        logic = 'NOT(1)'
        constructors = [x for x in ['AND', 'OR', 'NOT'] if x in logic][::-1]
        not_test = self.map_transformer.extracts_logic_information(logic, constructors.copy())

        # test results
        self.assertIsInstance(not_test, List)
        self.assertEqual(not_test, [['NOT', '1']])

        return None

    def test_extracts_logic_information_complex(self):
        """Tests the extracts_logic_information method when using multiple OWL constructors."""

        # test complex logic - constructor wrapped around two inner constructors
        logic = 'AND(OR(0, 1), NOT(1))'
        constructors = [x for x in ['AND', 'OR', 'NOT'] if x in logic][::-1]
        complex_test1 = self.map_transformer.extracts_logic_information(logic, constructors.copy())
        # test results
        expected_output = [['NOT', '1'], ['OR', '0, 1'], ['AND', 'NOT, OR']]
        self.assertIsInstance(complex_test1, List)
        self.assertEqual(complex_test1, expected_output)

        # test complex logic - 2
        logic = 'AND(0, OR(0, 1), NOT(1))'
        constructors = [x for x in ['AND', 'OR', 'NOT'] if x in logic][::-1]
        complex_test2 = self.map_transformer.extracts_logic_information(logic, constructors.copy())
        # test results
        expected_output = [['NOT', '1'], ['OR', '0, 1'], ['AND', '0, NOT, OR']]
        self.assertIsInstance(complex_test2, List)
        self.assertEqual(complex_test2, expected_output)

        return None