#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import os
import os.path
import pandas as pd
import regex
import shutil

from datetime import date, datetime
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import OWL
from typing import Dict, List, Tuple
from unittest import TestCase

from omop2obo.semantic_mapping_representation import SemanticTransformer


class TestSemanticTransformer(TestCase):
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
        self.ontology_list = ['hp', 'mondo']
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

        # create timestamp
        self.timestamp = '_' + datetime.strftime(datetime.strptime(str(date.today()), '%Y-%m-%d'), '%d%b%Y').upper()

        # instantiate semantic transformation class
        self.map_transformer = SemanticTransformer(ontology_list=['so', 'vo'],
                                                   omop2obo_data_file=self.omop2obo_data_file,
                                                   domain='condition',
                                                   map_type=self.map_type,
                                                   ontology_directory=self.ontology_directory,
                                                   primary_column='CONCEPT')

        self.map_transformer_multi = SemanticTransformer(ontology_list=['so', 'vo'],
                                                         omop2obo_data_file=self.omop2obo_data_file,
                                                         domain='condition',
                                                         map_type='multi',
                                                         ontology_directory=self.ontology_directory,
                                                         primary_column='CONCEPT')

        # make sure that instantiated class points to testing data location of the OWLTools API
        self.map_transformer.owltools_location = self.owltools_location

        # make sure the the write location points to
        self.map_transformer.write_location = self.dir_loc2 + '/mapping_semantics'

        return None

    def test_ont_dictionary_single(self):
        """Tests the ont_dictionary when the construction type is single"""

        # test method
        ont_dict = self.map_transformer.ontology_metadata
        self.assertEqual(ont_dict, None)

        return None

    def test_ont_dictionary_not_exist(self):
        """Tests the ont_dictionary when the file does not exist"""

        # move file out of directory
        shutil.copyfile(self.ontology_directory + '/master_ontology_dictionary.pickle',
                        self.ontology_directory + '/master_ontology.pickle')
        os.remove(self.ontology_directory + '/master_ontology_dictionary.pickle')

        # catch when ontology_dictionary file does not exist
        self.assertRaises(OSError, SemanticTransformer, ontology_list=['so', 'vo'],
                          omop2obo_data_file=self.omop2obo_data_file, domain='condition', map_type='multi',
                          ontology_directory=self.ontology_directory, primary_column='CONCEPT')

        # move file back and clean-up directory
        shutil.copyfile(self.ontology_directory + '/master_ontology.pickle',
                        self.ontology_directory + '/master_ontology_dictionary.pickle')
        os.remove(self.ontology_directory + '/master_ontology.pickle')

        return None

    def test_ont_dictionary_empty_file(self):
        """Tests the ont_dictionary when the file is empty"""

        # rename original file
        shutil.copyfile(self.ontology_directory + '/master_ontology_dictionary.pickle',
                        self.ontology_directory + '/master_ontology.pickle')
        os.remove(self.ontology_directory + '/master_ontology_dictionary.pickle')

        # create fake empty file
        shutil.copyfile(self.ontology_directory + '/empty_hp_without_imports.owl',
                        self.ontology_directory + '/master_ontology_dictionary.pickle')

        # catch when ontology_dictionary file is empty
        self.assertRaises(TypeError, SemanticTransformer, ontology_list=['so', 'vo'],
                          omop2obo_data_file=self.omop2obo_data_file, domain='condition', map_type='multi',
                          ontology_directory=self.ontology_directory, primary_column='CONCEPT')

        # remove bad file
        os.remove(self.ontology_directory + '/master_ontology_dictionary.pickle')

        # move file back and clean-up directory
        shutil.copyfile(self.ontology_directory + '/master_ontology.pickle',
                        self.ontology_directory + '/master_ontology_dictionary.pickle')
        os.remove(self.ontology_directory + '/master_ontology.pickle')

        return None

    def test_input_ontology_list_list(self):
        """Tests the ontology list input parameter when input is a list."""

        # catch when ontology list is a list
        self.assertRaises(TypeError, SemanticTransformer, ontology_list=1234,
                          omop2obo_data_file=self.omop2obo_data_file, domain='condition',
                          map_type=self.map_type, ontology_directory=self.ontology_directory,
                          superclasses=self.superclasses, primary_column='CONCEPT')

        return None

    def test_input_ontology_list_empty(self):
        """Tests the ontology list input parameter when input is empty."""

        # catch when ontology list is empty
        self.assertRaises(ValueError, SemanticTransformer, ontology_list=[],
                          omop2obo_data_file=self.omop2obo_data_file, domain='condition',
                          map_type=self.map_type, ontology_directory=self.ontology_directory,
                          superclasses=self.superclasses, primary_column='CONCEPT')

        return None

    def test_input_mapping_data_not_string(self):
        """Tests the omop2obo mapping data file input parameter when input is not a string."""

        # catch when omo2obo data file input is not a string
        self.assertRaises(TypeError, SemanticTransformer, ontology_list=['so'],
                          omop2obo_data_file=1234, domain='condition', map_type=self.map_type,
                          ontology_directory=self.ontology_directory, superclasses=self.superclasses,
                          primary_column='CONCEPT')

        return None

    def test_input_mapping_data_bad_path(self):
        """Tests the omop2obo mapping data file input parameter when file path does not exist."""

        # catch when omo2obo data file points to a path that does not exist
        self.assertRaises(OSError, SemanticTransformer, ontology_list=['so'],
                          omop2obo_data_file=self.mapping_directory + '/fake+data_path.csv',
                          domain='condition', map_type=self.map_type, ontology_directory=self.ontology_directory,
                          superclasses=self.superclasses, primary_column='CONCEPT')

        return None

    def test_input_mapping_data_empty_file(self):
        """Tests the omop2obo mapping data file input parameter when file is empty."""

        # catch when omo2obo data file input points to an empty file
        empty_data_file = self.ontology_directory + '/empty_hp_without_imports.owl'
        self.assertRaises(TypeError, SemanticTransformer, ontology_list=['so'],
                          omop2obo_data_file=empty_data_file, domain='condition', map_type=self.map_type,
                          ontology_directory=self.ontology_directory, superclasses=self.superclasses,
                          primary_column='CONCEPT')

        return None

    def test_write_location(self):
        """Tests the write location for outputting processed ontology data."""

        # make sure default location is a string and that it exists
        self.assertIsInstance(self.map_transformer.write_location, str)
        self.assertTrue(os.path.exists(self.map_transformer.write_location))

        return None

    def test_input_ontology_directory_not_exist(self):
        """Tests the ontology directory input parameter when the directory does not exist."""

        # catch when ontology_directory does not exist
        ontology_directory = self.dir_loc1 + '/ontologie'
        self.assertRaises(OSError, SemanticTransformer, ontology_list=['so'],
                          omop2obo_data_file=self.omop2obo_data_file, domain='condition',
                          map_type=self.map_type, ontology_directory=ontology_directory,
                          superclasses=self.superclasses, primary_column='CONCEPT')

        return None

    def test_input_ontology_directory_bad_directory(self):
        """Tests the ontology directory input parameter when the directory is incorrect."""

        # catch when ontology_directory is empty b/c there are no ontology data files
        os.mkdir(self.dir_loc1 + '/temp_ontologies')
        ontology_directory = self.dir_loc1 + '/temp_ontologies'
        self.assertRaises(TypeError, SemanticTransformer, ontology_list=['so'],
                          omop2obo_data_file=self.omop2obo_data_file, domain='condition',
                          map_type=self.map_type, ontology_directory=ontology_directory,
                          superclasses=self.superclasses, primary_column='CONCEPT')
        os.rmdir(self.dir_loc1 + '/temp_ontologies')

        return None

    def test_input_ontology_directory_empty_directory(self):
        """Tests the ontology directory input parameter when directory is empty."""

        # catch when ontology_directory is empty b/c there are no ontology data files from
        self.assertRaises(ValueError, SemanticTransformer, ontology_list=['cl'],
                          omop2obo_data_file=self.omop2obo_data_file, domain='condition',
                          map_type=self.map_type, ontology_directory=self.ontology_directory,
                          superclasses=self.superclasses, primary_column='CONCEPT')

        return None

    def test_input_domain_string(self):
        """Tests the domain input parameter is type string."""

        # test that input is string
        self.assertRaises(TypeError, SemanticTransformer, ontology_list=['so', 'vo'],
                          omop2obo_data_file=self.omop2obo_data_file, domain=1234,
                          map_type=self.map_type, ontology_directory=self.ontology_directory, primary_column='CONCEPT')

        return None

    def test_input_domain_correct_type(self):
        """Tests the domain input parameter is one of the three possible input types."""

        # test that input is in list of expected domains
        self.assertRaises(ValueError, SemanticTransformer, ontology_list=['so', 'vo'],
                          omop2obo_data_file=self.omop2obo_data_file, domain='conditions',
                          map_type=self.map_type, ontology_directory=self.ontology_directory, primary_column='CONCEPT')

        return None

    def test_input_mapping_approach_type(self):
        """Tests the mapping approach type input parameter."""

        # when mapping type is not None
        self.assertRaises(TypeError, SemanticTransformer, ontology_list=['so'],
                          omop2obo_data_file=self.omop2obo_data_file, domain='condition', map_type=123,
                          ontology_directory=self.ontology_directory, superclasses=self.superclasses,
                          primary_column='CONCEPT')

        test_method = SemanticTransformer(ontology_list=['so'], omop2obo_data_file=self.omop2obo_data_file,
                                          domain='condition', ontology_directory=self.ontology_directory,
                                          superclasses=self.superclasses, primary_column='CONCEPT')

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
        test_method1 = SemanticTransformer(ontology_list=['so'], omop2obo_data_file=self.omop2obo_data_file,
                                           domain='condition', map_type='multi',
                                           ontology_directory=self.ontology_directory,
                                           superclasses=self.superclasses, primary_column='CONCEPT')
        self.assertIsInstance(test_method1.superclass_dict, Dict)
        self.assertEqual(test_method1.superclass_dict, test_dict)

        return None

    def test_input_subclass_dict_not_dictionary(self):
        """Tests the subclass_dict input parameter when the input is not type dictionary."""

        # check when subclass dict is not None
        self.assertRaises(TypeError, SemanticTransformer, ontology_list=['so'],
                          omop2obo_data_file=self.omop2obo_data_file, domain='condition', map_type='multi',
                          ontology_directory=self.ontology_directory, superclasses=123, primary_column='CONCEPT')

        return None

    def test_input_subclass_dict_single_construction_no_superclasses(self):
        """Tests that the subclass_dict input parameter is None when the construction type is single."""

        # check when construction type is single that the subclass dict is None
        test_method2 = SemanticTransformer(ontology_list=['so'], omop2obo_data_file=self.omop2obo_data_file,
                                           domain='condition', map_type='single',
                                           ontology_directory=self.ontology_directory, primary_column='CONCEPT')
        self.assertEqual(test_method2.superclass_dict, None)

        return None

    def test_input_ontology_relations_single_construction(self):
        """Tests the multi-ontology class relations data when construction type is not "multi"."""

        # test when construction type is not "multi"
        test_method = SemanticTransformer(ontology_list=['so'], omop2obo_data_file=self.omop2obo_data_file,
                                          ontology_directory=self.ontology_directory, map_type='single',
                                          domain='condition', superclasses=self.superclasses)
        self.assertEqual(test_method.multi_class_relations, None)

        return None

    def test_input_ontology_relations_no_relations_file(self):
        """Tests the multi-ontology class relations data when the relations file does not exist."""

        # test when relations file does not exist
        os.remove(self.resources_directory + '/omop2obo_class_relations.txt')
        self.assertRaises(OSError, SemanticTransformer, ontology_list=['so'],
                          omop2obo_data_file=self.omop2obo_data_file, domain='condition', map_type='multi',
                          ontology_directory=self.ontology_directory, primary_column='CONCEPT')

        return None

    def test_input_ontology_relations_empty_relations(self):
        """Tests the multi-ontology class relations data when relations data is empty."""

        # move and rename empty file into repo
        shutil.copyfile(self.dir_loc1 + '/omop2obo_class_relations_empty.txt',
                        self.resources_directory + '/omop2obo_class_relations.txt')
        self.assertRaises(TypeError, SemanticTransformer, ontology_list=['so'],
                          omop2obo_data_file=self.omop2obo_data_file, domain='condition', map_type='multi',
                          ontology_directory=self.ontology_directory, primary_column='CONCEPT')

        # clean up environment
        os.remove('resources/mapping_semantics/omop2obo_class_relations.txt')

        return None

    def test_input_ontology_relations_correct_formatting(self):
        """Tests the multi-ontology class relations data when file is correct - in order to test output."""

        # check output when file correctly formatted
        shutil.copyfile(self.dir_loc1 + '/omop2obo_class_relations.txt',
                        self.resources_directory + '/omop2obo_class_relations.txt')
        test_method2 = SemanticTransformer(ontology_list=['so'], omop2obo_data_file=self.omop2obo_data_file,
                                           ontology_directory=self.ontology_directory,
                                           domain='condition', map_type='multi', superclasses=self.superclasses,
                                           primary_column='CONCEPT')
        self.assertEqual(test_method2.multi_class_relations, self.test_relations_dict)

        # clean up environment
        os.remove('resources/mapping_semantics/omop2obo_class_relations.txt')

        return None

    def test_input_primary_column_string(self):
        """Tests the primary_column input when not a string."""

        self.assertRaises(TypeError, SemanticTransformer, ontology_list=['so', 'vo'],
                          omop2obo_data_file=self.omop2obo_data_file,
                          domain='condition',
                          map_type=self.map_type,
                          ontology_directory=self.ontology_directory,
                          primary_column=1234)

        return None

    def test_input_primary_column_none(self):
        """Tests the primary_column input when no input is provided."""

        test_method = SemanticTransformer(ontology_list=['so', 'vo'],
                                          omop2obo_data_file=self.omop2obo_data_file, domain='condition',
                                          map_type=self.map_type, ontology_directory=self.ontology_directory)
        self.assertEqual(test_method.primary_column, 'CONCEPT')

        return None

    def test_input_secondary_column_string(self):
        """Tests the secondary_column input when not a string."""

        self.assertRaises(TypeError, SemanticTransformer, ontology_list=['so', 'vo'],
                          omop2obo_data_file=self.omop2obo_data_file,
                          domain='condition',
                          map_type=self.map_type,
                          ontology_directory=self.ontology_directory,
                          primary_column='CONCEPT',
                          secondary_column=1234)

        return None

    def test_input_secondary_column_none(self):
        """Tests the secondary_column input when no input is provided."""

        test_method = SemanticTransformer(ontology_list=['so', 'vo'],
                                          omop2obo_data_file=self.omop2obo_data_file, domain='condition',
                                          map_type=self.map_type, ontology_directory=self.ontology_directory,
                                          primary_column='CONCEPT')
        self.assertEqual(test_method.secondary_column, None)

        return None

    def test_find_existing_omop2obo_data(self):
        """"Tests the search for existing omop2obo mapping ontology data."""

        # test when there is not an existing omop2obo mapping file present
        test_method1 = SemanticTransformer(ontology_list=['so'], omop2obo_data_file=self.omop2obo_data_file,
                                           ontology_directory=self.ontology_directory,
                                           domain='condition', map_type='multi', superclasses=self.superclasses,
                                           primary_column='CONCEPT')
        self.assertEqual(test_method1.current_omop2obo, None)

        # test when there is not an existing omop2obo mapping file present
        shutil.copyfile(self.ontology_directory + '/so_without_imports.owl',
                        self.resources_directory + '/omop2obo_v0.owl')
        test_method2 = SemanticTransformer(ontology_list=['so'], omop2obo_data_file=self.omop2obo_data_file,
                                           ontology_directory=self.ontology_directory,
                                           domain='condition', map_type='multi', superclasses=self.superclasses,
                                           primary_column='CONCEPT')

        self.assertEqual(test_method2.current_omop2obo, 'resources/mapping_semantics/omop2obo_v0.owl')

        # clean up environment
        os.remove('resources/mapping_semantics/omop2obo_v0.owl')

        return None

    def test_loads_ontology_data_single_construction(self):
        """Tests the loads_ontology_data method for a single class construction type."""

        # run the method to load ontology data
        ont_dictionary = self.map_transformer.loads_ontology_data()
        print(ont_dictionary)

        # check output
        self.assertIsInstance(ont_dictionary, Dict)
        self.assertIn('vo', ont_dictionary.keys())
        self.assertIn('so', ont_dictionary.keys())

        return None

    def test_loads_ontology_data_multi_construction(self):
        """Tests the loads_ontology_data method for a multi class construction type."""

        # instantiate method
        self.map_transformer2 = SemanticTransformer(ontology_list=['so', 'vo'],
                                                    omop2obo_data_file=self.omop2obo_data_file,
                                                    domain='condition', map_type='multi',
                                                    ontology_directory=self.ontology_directory,
                                                    primary_column='CONCEPT')
        self.map_transformer2.owltools_location = self.owltools_location

        # run the method to load ontology data
        ont_dictionary = self.map_transformer2.loads_ontology_data()
        merged_file = glob.glob(self.ontology_directory + '/OMOP2OBO_MergedOntologies_*.owl')[0]

        # check output
        self.assertIsInstance(ont_dictionary, Dict)
        self.assertIn('merged', list(ont_dictionary.keys())[0])
        self.assertIsInstance(ont_dictionary['merged'], Graph)
        self.assertEqual(len(ont_dictionary['merged']), 127283)
        self.assertEqual(merged_file, self.ontology_directory + '/OMOP2OBO_MergedOntologies' + self.timestamp + '.owl')

        # remove file
        os.remove(merged_file)

        return None

    def test_orders_constructors(self):
        """Tests the orders_constructors method."""

        # set-up inputs
        logic = 'OR(AND(0, 1, 2, 3), OR(AND(0, 1, 2), 3))'
        result = regex.search(r'(?<grp>\((?:[^()]++|(?&grp))*\))', logic).captures('grp')
        output_results = ['AND', 'AND', 'OR', 'OR']

        # test method
        output = self.map_transformer.orders_constructors(logic, result)
        self.assertIsInstance(output, List)
        self.assertEqual(output, output_results)

        return None

    def test_extracts_logic_information_and(self):
        """Tests the extracts_logic_information method when logic string contains 'AND' constructor."""

        # test simple logic - AND
        logic = 'AND(0, 1)'
        result = regex.search(r'(?<grp>\((?:[^()]++|(?&grp))*\))', logic).captures('grp')
        construct = self.map_transformer.orders_constructors(logic, result.copy())
        and_test = self.map_transformer.extracts_logic(logic, result.copy(), construct.copy())

        # test results
        self.assertIsInstance(and_test, List)
        self.assertEqual(and_test, [['AND', '0, 1']])

        return None

    def test_extracts_logic_information_or(self):
        """Tests the extracts_logic_information method when logic string contains 'OR' constructor."""

        # test simple logic - OR
        logic = 'OR(0, 1)'
        result = regex.search(r'(?<grp>\((?:[^()]++|(?&grp))*\))', logic).captures('grp')
        construct = self.map_transformer.orders_constructors(logic, result.copy())
        or_test = self.map_transformer.extracts_logic(logic, result.copy(), construct.copy())

        # test results
        self.assertIsInstance(or_test, List)
        self.assertEqual(or_test, [['OR', '0, 1']])

        return None

    def test_extracts_logic_information_not(self):
        """Tests the extracts_logic_information method when logic string contains 'NOT' constructor."""

        # test simple logic - NOT
        logic = 'NOT(1)'
        result = regex.search(r'(?<grp>\((?:[^()]++|(?&grp))*\))', logic).captures('grp')
        construct = self.map_transformer.orders_constructors(logic, result.copy())
        not_test = self.map_transformer.extracts_logic(logic, result.copy(), construct.copy())

        # test results
        self.assertIsInstance(not_test, List)
        self.assertEqual(not_test, [['NOT', '1']])

        return None

    def test_extracts_logic_information_complex(self):
        """Tests the extracts_logic_information method when using multiple complex orientations of OWL constructors."""

        # test complex logic - constructor wrapped around two inner constructors
        logic = 'AND(OR(0, 1), NOT(1))'
        result = regex.search(r'(?<grp>\((?:[^()]++|(?&grp))*\))', logic).captures('grp')
        construct = self.map_transformer.orders_constructors(logic, result.copy())
        complex_test1 = self.map_transformer.extracts_logic(logic, result.copy(), construct.copy())
        # test results
        expected_output = [['OR', '0, 1'], ['NOT', '1'], ['AND', 'OR-4, NOT-14']]
        self.assertIsInstance(complex_test1, List)
        self.assertEqual(complex_test1, expected_output)

        # test complex logic - 2
        logic = 'AND(0, OR(0, 1), NOT(1))'
        result = regex.search(r'(?<grp>\((?:[^()]++|(?&grp))*\))', logic).captures('grp')
        construct = self.map_transformer.orders_constructors(logic, result.copy())
        complex_test2 = self.map_transformer.extracts_logic(logic, result.copy(), construct.copy())
        # test results
        expected_output = [['OR', '0, 1'], ['NOT', '1'], ['AND', '0, OR-7, NOT-17']]
        self.assertIsInstance(complex_test2, List)
        self.assertEqual(complex_test2, expected_output)

        # test complex logic - 3
        logic = 'OR(AND(0, 1), AND(2, NOT(3)))'
        result = regex.search(r'(?<grp>\((?:[^()]++|(?&grp))*\))', logic).captures('grp')
        construct = self.map_transformer.orders_constructors(logic, result.copy())
        complex_test3 = self.map_transformer.extracts_logic(logic, result.copy(), construct.copy())
        # test results
        expected_output = [['AND', '0, 1'], ['NOT', '3'], ['AND', '2, NOT-21'], ['OR', 'AND-3, AND-14']]
        self.assertIsInstance(complex_test3, List)
        self.assertEqual(complex_test3, expected_output)

        # test complex logic - 4
        logic = 'OR(AND(0, NOT(1)), OR(0, NOT(1)))'
        result = regex.search(r'(?<grp>\((?:[^()]++|(?&grp))*\))', logic).captures('grp')
        construct = self.map_transformer.orders_constructors(logic, result.copy())
        complex_test4 = self.map_transformer.extracts_logic(logic, result.copy(), construct.copy())
        # test results
        expected_output = [['NOT', '1'], ['AND', '0, NOT-10'], ['OR', '0, NOT-10'], ['OR', 'AND-3, OR-19']]
        self.assertIsInstance(complex_test4, List)
        self.assertEqual(complex_test4, expected_output)

        return None

    def test_gets_concept_id_data_(self):
        """Tests the gets_concept_id_data method."""

        # initialize a row of data
        row_data = pd.Series({'CONCEPT_ID': 27526, 'CONCEPT_LABEL': "Nezelof's syndrome",
                              'CONCEPT_SYNONYMS': "Nezelof syndrome | Congenital thymic dysplasia syndrome",
                              'CONCEPT_VOCAB': 'SNOMED', 'CONCEPT_VOCAB_VERSION': 'SnomedCT Release 20180131',
                              'CONCEPT_SOURCE_CODE': 55602000, 'CONCEPT_CUI': 'C0152094',
                              'CONCEPT_SEMANTIC_TYPE': 'Disease or Syndrome'})

        # test method
        test_output = self.map_transformer.gets_concept_id_data(row_data)
        self.assertIsInstance(test_output, Dict)
        self.assertIn('primary_data', test_output[27526].keys())
        self.assertIn('secondary_data', test_output[27526].keys())

        # check primary key dict
        self.assertEqual(len(test_output[27526]['primary_data']), 8)

        # check secondary key dict
        self.assertEqual(test_output[27526]['secondary_data'], None)

        return None

    def test_complement_of_constructor_list_input(self):
        """Tests the complement_of_constructor method when the wrong type of input structure is passed."""

        # test method
        self.assertRaises(TypeError, self.map_transformer.complement_of_constructor, ['HP_0005359'])

        return None

    def test_complement_of_constructor(self):
        """Tests the complement_of_constructor method."""

        # test method
        test_output = self.map_transformer.complement_of_constructor('HP_0005359')
        self.assertIsInstance(test_output, Tuple)
        self.assertIsInstance(test_output[0], BNode)
        self.assertIsInstance(test_output[1], List)
        self.assertEqual(len(test_output[1]), 1)

        return None

    def test_other_owl_constructor_too_few_uris(self):
        """Tests the other_owl_constructor method when too few URIs are passed."""

        # test method
        self.assertRaises(ValueError, self.map_transformer.other_owl_constructor, ['HP_0005359'], OWL.unionOf)
        self.assertRaises(ValueError, self.map_transformer.other_owl_constructor, ['HP_0005359'], OWL.intersectionOf)

        return None

    def test_other_owl_constructor_unionof(self):
        """Tests the other_owl_constructor method for type OWL:unionOf."""

        # test method
        test_output = self.map_transformer.other_owl_constructor(['HP_0004430', 'HP_0000007'], OWL.unionOf)
        self.assertIsInstance(test_output, Tuple)
        self.assertIsInstance(test_output[0], BNode)
        self.assertIsInstance(test_output[1], List)
        self.assertEqual(len(test_output[1]), 5)

        return None

    def test_other_owl_constructor_intersectionof(self):
        """Tests the other_owl_constructor method for type OWL:intersectionOf."""

        # test method
        test_output = self.map_transformer.other_owl_constructor(['HP_0004430', 'HP_0000007'], OWL.intersectionOf)
        self.assertIsInstance(test_output, Tuple)
        self.assertIsInstance(test_output[0], BNode)
        self.assertIsInstance(test_output[1], List)
        self.assertEqual(len(test_output[1]), 5)

        return None

    def test_class_constructor_intersection(self):
        """Tests the class_constructor method for a simple intersection."""

        # create method inputs
        logic, logic_info, uris = 'OR(0, 1)', [['OR', '0, 1']], ['HP_0004430', 'HP_0000007']
        span_data = regex.search(r'(?<grp>\((?:[^()]++|(?&grp))*\))', logic).captures('grp')

        # test method
        test_output = self.map_transformer.class_constructor(logic, logic_info.copy(), span_data, uris)
        self.assertIsInstance(test_output, Tuple)
        self.assertIsInstance(test_output[0], BNode)
        self.assertIsInstance(test_output[1], List)
        self.assertEqual(len(test_output[1]), 9)

        return None

    def test_class_constructor_union(self):
        """Tests the class_constructor method for a simple union."""

        # create method inputs
        logic, logic_info, uris = 'AND(0, 1)', [['AND', '0, 1']], ['HP_0004430', 'HP_0000007']
        span_data = regex.search(r'(?<grp>\((?:[^()]++|(?&grp))*\))', logic).captures('grp')

        # test method
        test_output = self.map_transformer.class_constructor(logic, logic_info.copy(), span_data, uris)
        self.assertIsInstance(test_output, Tuple)
        self.assertIsInstance(test_output[0], BNode)
        self.assertIsInstance(test_output[1], List)
        self.assertEqual(len(test_output[1]), 9)

        return None

    def test_class_constructor_complement(self):
        """Tests the class_constructor method for a simple complement."""

        # create method inputs
        logic, logic_info, uris = 'NOT(0)', [['NOT', '0']], ['HP_0004430']
        span_data = regex.search(r'(?<grp>\((?:[^()]++|(?&grp))*\))', logic).captures('grp')

        # test method
        test_output = self.map_transformer.class_constructor(logic, logic_info.copy(), span_data, uris)
        self.assertIsInstance(test_output, Tuple)
        self.assertIsInstance(test_output[0], BNode)
        self.assertIsInstance(test_output[1], List)
        self.assertEqual(len(test_output[1]), 5)

        return None

    def test_class_constructor_complex(self):
        """Tests the class_constructor method for a complex set of log."""

        # create method inputs
        logic, logic_info = 'AND(OR(1, 2), AND(0, 3))', [['OR', '1, 2'], ['AND', '0, 3'], ['AND', 'OR-4, AND-14']]
        uris = ['HP_0004430', 'HP_0000007', 'HP_0001419', 'HP_0005359']
        span_data = regex.search(r'(?<grp>\((?:[^()]++|(?&grp))*\))', logic).captures('grp')

        # test method
        test_output = self.map_transformer.class_constructor(logic, logic_info.copy(), span_data, uris)
        self.assertIsInstance(test_output, Tuple)
        self.assertIsInstance(test_output[0], BNode)
        self.assertIsInstance(test_output[1], List)
        self.assertEqual(len(test_output[1]), 19)

        return None

    def test_serializes_semantic_representation_ont(self):
        """Tests the serializes_semantic_representation method for a single ontology."""

        # Set up inputs
        graph = Graph().parse(self.ontology_directory + '/so_without_imports.owl', format='xml')

        # test method
        self.map_transformer.serializes_semantic_representation('hp', graph, self.ontology_directory)
        # make sure method runs on legitimate file
        serialized_file = glob.glob(self.ontology_directory + '/OMOP2OBO*.owl')
        file_name = '/OMOP2OBO_Condition_SemanticRepresentation_HP' + self.timestamp + '.owl'
        self.assertEqual(serialized_file[0], self.ontology_directory + file_name)

        # remove file
        os.remove(serialized_file[0])

        return None

    def test_serializes_semantic_representation_full(self):
        """Tests the serializes_semantic_representation method for all ontologies."""

        # Set up inputs
        graph = Graph().parse(self.ontology_directory + '/so_without_imports.owl', format='xml')

        # test method
        self.map_transformer.serializes_semantic_representation('merged', graph, self.ontology_directory)
        # make sure method runs on legitimate file
        serialized_file = glob.glob(self.ontology_directory + '/OMOP2OBO*.owl')
        file_name = '/OMOP2OBO_Condition_SemanticRepresentation_Full' + self.timestamp + '.owl'
        self.assertEqual(serialized_file[0], self.ontology_directory + file_name)

        # remove file
        os.remove(serialized_file[0])

        return None

    def test_adds_class_metadata_multi(self):
        """Tests the adds_class_metadata method when the construction_type is 'multi'."""

        # set-up input
        class_data = {'primary_data': {'CONCEPT_ID': 27526, 'CONCEPT_LABEL': "Nezelof's syndrome"},
                      'secondary_data': None,
                      'triples': (BNode('N464bb6346c4c421f8de89c3d56cc0f2c'),
                                  [(BNode('N464bb6346c4c421f8de89c3d56cc0f2c'),
                                    URIRef('http://www.w3.org/2002/07/owl#complementOf'),
                                    URIRef('http://purl.obolibrary.org/obo/HP_0004430'))])}

        # test method
        triples = self.map_transformer_multi.adds_class_metadata(class_data, 'primary_data')
        self.assertIsInstance(triples, List)
        self.assertEqual(len(triples), 7)
        self.assertIn((URIRef('https://github.com/callahantiff/omop2obo/OMOP_27526'),
                       URIRef('http://www.w3.org/2000/01/rdf-schema#subClassOf'),
                       URIRef('http://purl.obolibrary.org/obo/HP_0000118')), triples)

        return None

    def test_adds_class_metadata_single(self):
        """Tests the adds_class_metadata method when the construction_type is 'single'."""

        # set-up input
        class_data = {'primary_data': {'CONCEPT_ID': 27526, 'CONCEPT_LABEL': "Nezelof's syndrome"},
                      'secondary_data': None,
                      'triples': (BNode('N464bb6346c4c421f8de89c3d56cc0f2c'),
                                  [(BNode('N464bb6346c4c421f8de89c3d56cc0f2c'),
                                    URIRef('http://www.w3.org/2002/07/owl#complementOf'),
                                    URIRef('http://purl.obolibrary.org/obo/HP_0004430'))])}

        # test method
        triples = self.map_transformer.adds_class_metadata(class_data, 'primary_data')
        self.assertIsInstance(triples, List)
        self.assertEqual(len(triples), 6)

        return None

    def test_adds_triples_to_ontology(self):
        """Tests the adds_triples_to_ontology method."""

        # set-up method
        class_data = {46274126: {'so': {'primary_data': {'CONCEPT_ID': 46274126, 'CONCEPT_LABEL': 'Edentulism'},
                                        'secondary_data': None,
                                        'triples':
                                            [(URIRef('https://github.com/callahantiff/omop2obo/OMOP_46274126'),
                                              URIRef('http://www.geneontology.org/formats/oboInOwl#hasOBONamespace'),
                                              Literal('OMOP2OBO')),
                                             (URIRef('https://github.com/callahantiff/omop2obo/OMOP_46274126'),
                                              URIRef('http://www.geneontology.org/formats/oboInOwl#id'),
                                              Literal('OMOP:46274126')),
                                             (URIRef('https://github.com/callahantiff/omop2obo/OMOP_46274126'),
                                              URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
                                              URIRef('http://www.w3.org/2002/07/owl#Class')),
                                             (URIRef('https://github.com/callahantiff/omop2obo/OMOP_46274126'),
                                              URIRef('http://www.w3.org/2000/01/rdf-schema#label'),
                                              Literal('Complete edentulism due to caries')),
                                             (URIRef('https://github.com/callahantiff/omop2obo/OMOP_46274126'),
                                              URIRef('http://www.w3.org/2002/07/owl#equivalentClass'),
                                              BNode('Nd65d385cf6734a19b37e79adbf48e095')),
                                             (BNode('Nd65d385cf6734a19b37e79adbf48e095'),
                                              URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
                                              URIRef('http://www.w3.org/2002/07/owl#Restriction')),
                                             (BNode('Nd65d385cf6734a19b37e79adbf48e095'),
                                              URIRef('http://www.w3.org/2002/07/owl#onProperty'),
                                              URIRef('http://purl.obolibrary.org/obo/BFO_0000051')),
                                             (BNode('Nd65d385cf6734a19b37e79adbf48e095'),
                                              URIRef('http://www.w3.org/2002/07/owl#someValuesFrom'),
                                              BNode('N40a89b262a5545e5afbeb6c8244d2619')),
                                             (BNode('N40a89b262a5545e5afbeb6c8244d2619'),
                                              URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
                                              URIRef('http://www.w3.org/2002/07/owl#Class')),
                                             (BNode('N40a89b262a5545e5afbeb6c8244d2619'),
                                              URIRef('http://www.w3.org/2002/07/owl#intersectionOf'),
                                              BNode('Nee63471f3bc4480da0dd663b6dd48dbc')),
                                             (BNode('Nee63471f3bc4480da0dd663b6dd48dbc'),
                                              URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#first'),
                                              URIRef('http://purl.obolibrary.org/obo/HP_0006480')),
                                             (BNode('Nee63471f3bc4480da0dd663b6dd48dbc'),
                                              URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#rest'),
                                              BNode('N9ef5520613c84ee2bac214241c2cdb02')),
                                             (BNode('N9ef5520613c84ee2bac214241c2cdb02'),
                                              URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#first'),
                                              URIRef('http://purl.obolibrary.org/obo/HP_0000670')),
                                             (BNode('N9ef5520613c84ee2bac214241c2cdb02'),
                                              URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#rest'),
                                              URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#nil'))]},
                      'vo': {'primary_data': {'CONCEPT_ID': 22871, 'CONCEPT_LABEL': 'Pineal neoplasm'},
                             'secondary_data': None,
                             'triples': [(URIRef('https://github.com/callahantiff/omop2obo/OMOP_22871'),
                                          URIRef('http://www.geneontology.org/formats/oboInOwl#hasOBONamespace'),
                                          Literal('OMOP2OBO')),
                                         (URIRef('https://github.com/callahantiff/omop2obo/OMOP_22871'),
                                          URIRef('http://www.geneontology.org/formats/oboInOwl#id'),
                                          Literal('OMOP:22871')),
                                         (URIRef('https://github.com/callahantiff/omop2obo/OMOP_22871'),
                                          URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
                                          URIRef('http://www.w3.org/2002/07/owl#Class')),
                                         (URIRef('https://github.com/callahantiff/omop2obo/OMOP_22871'),
                                          URIRef('http://www.w3.org/2000/01/rdf-schema#label'),
                                          Literal('Neoplasm of uncertain behavior of pineal gland')),
                                         (URIRef('https://github.com/callahantiff/omop2obo/OMOP_22871'),
                                          URIRef('http://www.w3.org/2002/07/owl#equivalentClass'),
                                          URIRef('http://purl.obolibrary.org/obo/HP_0030693'))]}}}

        # prepare to test method by loading ontology data
        self.map_transformer.ontology_list = ['so', 'vo']
        self.map_transformer.ontology_data_dict = self.map_transformer.loads_ontology_data()
        so_graph = self.map_transformer.ontology_data_dict['so']
        so_original_nodes = len(set([i for j in [x[0::2] for x in so_graph] for i in j]))
        so_original_edges = len(so_graph)
        vo_graph = self.map_transformer.ontology_data_dict['vo']
        vo_original_nodes = len(set([i for j in [x[0::2] for x in vo_graph] for i in j]))
        vo_original_edges = len(vo_graph)

        # test method
        self.map_transformer.adds_triples_to_ontology(class_data, ['so', 'vo'])
        # so results
        so_file_name = glob.glob(self.map_transformer.write_location + '/*_SemanticRepresentation_SO_*.owl')[0]
        self.assertTrue(os.path.exists(so_file_name))
        so_post_graph = Graph().parse(so_file_name, format='xml')
        so_post_nodes = len(set([i for j in [x[0::2] for x in so_post_graph] for i in j]))
        so_post_edges = len(so_post_graph)
        self.assertTrue(so_post_nodes > so_original_nodes)
        self.assertTrue(so_post_edges > so_original_edges)
        self.assertEqual(so_post_edges, 42251)
        # vo results
        vo_file_name = glob.glob(self.map_transformer.write_location + '/*_SemanticRepresentation_VO_*.owl')[0]
        self.assertTrue(os.path.exists(vo_file_name))
        vo_post_graph = Graph().parse(vo_file_name, format='xml')
        vo_post_nodes = len(set([i for j in [x[0::2] for x in vo_post_graph] for i in j]))
        vo_post_edges = len(vo_post_graph)
        self.assertTrue(vo_post_nodes > vo_original_nodes)
        self.assertTrue(vo_post_edges > vo_original_edges)
        self.assertEqual(vo_post_edges, 85074)

        # clean up environment
        os.remove(glob.glob(self.map_transformer.write_location + '/*_SemanticRepresentation_VO_*.owl')[0])
        os.remove(glob.glob(self.map_transformer.write_location + '/*_SemanticRepresentation_SO_*.owl')[0])

        return None
