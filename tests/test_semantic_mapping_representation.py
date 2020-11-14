#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import os.path
import shutil

from rdflib import URIRef
from typing import Dict
from unittest import TestCase

from omop2obo.semantic_mapping_representation import SemanticMappingTransformer


class TestSemanticMappingTransformer(TestCase):
    """Class to test functions used when converting the omop2obo mapping set to RDF."""

    def setUp(self):
        # initialize data directories
        current_directory1 = os.path.dirname(__file__)
        dir_loc1 = os.path.join(current_directory1, 'data')
        self.dir_loc1 = os.path.abspath(dir_loc1)
        self.ontology_directory = self.dir_loc1 + '/ontologies'
        self.mapping_directory = self.dir_loc1 + '/mappings'

        # create a second location
        current_directory2 = os.path.dirname(__file__)
        dir_loc2 = os.path.join(current_directory2, 'resources')
        self.dir_loc2 = os.path.abspath(dir_loc2)
        self.resources_directory = self.dir_loc2 + '/mapping_semantics'

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
        self.map_transformer = SemanticMappingTransformer(['so'], self.omop2obo_data_file,
                                                          self.ontology_directory,
                                                          self.map_type)

        return None

    def test_input_ontology_list(self):
        """Tests the ontology list input parameter."""

        # catch when ontology list is a list
        self.assertRaises(TypeError, SemanticMappingTransformer, 1234, self.omop2obo_data_file, self.ontology_directory,
                          self.map_type, self.superclasses)

        # catch when ontology list is empty
        self.assertRaises(ValueError, SemanticMappingTransformer, [], self.omop2obo_data_file, self.ontology_directory,
                          self.map_type, self.superclasses)

        return None

    def test_input_mapping_data(self):
        """Tests the omop2obo mapping data file input parameter."""

        # catch when omo2obo data file input is not a string
        self.assertRaises(TypeError, SemanticMappingTransformer, ['so'], 1234, self.ontology_directory,
                          self.map_type, self.superclasses)

        # catch when omo2obo data file points to a path that does not exist
        self.assertRaises(OSError, SemanticMappingTransformer, ['so'], self.mapping_directory + '/fake+data_path.csv',
                          self.ontology_directory, self.map_type, self.superclasses)

        # catch when omo2obo data file input points to an empty file
        empty_data_file = self.ontology_directory + '/empty_hp_without_imports.owl'
        self.assertRaises(TypeError, SemanticMappingTransformer, ['so'], empty_data_file, self.ontology_directory,
                          self.map_type, self.superclasses)

        return None

    def test_input_ontology_directory(self):
        """Tests the ontology directory input parameter."""

        # catch when ontology_directory does not exist
        ontology_directory = self.dir_loc1 + '/ontologie'
        self.assertRaises(OSError, SemanticMappingTransformer, ['so'], self.omop2obo_data_file,
                          ontology_directory, self.map_type, self.superclasses)

        # catch when ontology_directory is empty b/c there are no ontology data files
        os.mkdir(self.dir_loc1 + '/temp_ontologies')
        ontology_directory = self.dir_loc1 + '/temp_ontologies'
        self.assertRaises(TypeError, SemanticMappingTransformer, ['so'], self.omop2obo_data_file,
                          ontology_directory, self.map_type, self.superclasses)
        os.rmdir(self.dir_loc1 + '/temp_ontologies')

        # catch when ontology_directory is empty b/c there are no ontology data files from
        self.assertRaises(ValueError, SemanticMappingTransformer, ['cl'], self.omop2obo_data_file,
                          self.ontology_directory, self.map_type, self.superclasses)

        return None

    def test_input_mapping_approach_type(self):
        """Tests the mapping approach type input parameter."""

        # when mapping type is not None
        self.assertRaises(TypeError, SemanticMappingTransformer, ['so'], self.omop2obo_data_file,
                          self.ontology_directory, 123, self.superclasses)

        # when mapping type is not None
        test_method = SemanticMappingTransformer(ontology_list=['so'], omop2obo_data_file=self.omop2obo_data_file,
                                                 ontology_directory=self.ontology_directory,
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
        test_method = SemanticMappingTransformer(['so'], self.omop2obo_data_file, self.ontology_directory,
                                                 self.map_type, self.superclasses)
        self.assertIsInstance(test_method.superclass_dict, Dict)
        self.assertEqual(test_method.superclass_dict, test_dict)

        # check when subclass dict is not None
        self.assertRaises(TypeError, SemanticMappingTransformer, ['so'], self.omop2obo_data_file,
                          self.ontology_directory, 123, 'not a dict')

        return None

    def test_input_ontology_relations(self):
        """Tests the multi-ontology class relations data."""

        # create test data dictionary

        # test when construction type is not "multi"
        test_method = SemanticMappingTransformer(ontology_list=['so'], omop2obo_data_file=self.omop2obo_data_file,
                                                 ontology_directory=self.ontology_directory, map_type='single',
                                                 superclasses=self.superclasses)
        self.assertEqual(test_method.multi_class_relations, None)

        # test when relations file does not exist
        os.remove(self.resources_directory + '/omop2obo_class_relations.txt')
        self.assertRaises(OSError, SemanticMappingTransformer, ['so'], self.omop2obo_data_file,
                          self.ontology_directory, 'multi')

        # move and rename empty file into repo
        shutil.copyfile(self.dir_loc1 + '/omop2obo_class_relations_empty.txt',
                        self.resources_directory + '/omop2obo_class_relations.txt')
        self.assertRaises(TypeError, SemanticMappingTransformer, ['so'], self.omop2obo_data_file,
                          self.ontology_directory, 'multi')

        # check output when file correctly formatted
        shutil.copyfile(self.dir_loc1 + '/omop2obo_class_relations.txt',
                        self.resources_directory + '/omop2obo_class_relations.txt')
        test_method2 = SemanticMappingTransformer(ontology_list=['so'], omop2obo_data_file=self.omop2obo_data_file,
                                                  ontology_directory=self.ontology_directory, map_type='multi',
                                                  superclasses=self.superclasses)
        self.assertEqual(test_method2.multi_class_relations, self.test_relations_dict)

        # clean up environment
        os.remove('resources/mapping_semantics/omop2obo_class_relations.txt')

        return None

    def test_find_existing_omop2obo_data(self):
        """"Tests the search for existing omop2obo mapping ontology data."""

        # test when there is not an existing omop2obo mapping file present
        test_method1 = SemanticMappingTransformer(ontology_list=['so'], omop2obo_data_file=self.omop2obo_data_file,
                                                  ontology_directory=self.ontology_directory, map_type='multi',
                                                  superclasses=self.superclasses)
        self.assertEqual(test_method1.current_omop2obo, None)

        # test when there is not an existing omop2obo mapping file present
        shutil.copyfile(self.ontology_directory + '/so_without_imports.owl',
                        self.resources_directory + '/omop2obo_v0.owl')
        test_method2 = SemanticMappingTransformer(ontology_list=['so'], omop2obo_data_file=self.omop2obo_data_file,
                                                  ontology_directory=self.ontology_directory, map_type='multi',
                                                  superclasses=self.superclasses)

        print(test_method2.current_omop2obo)
        self.assertEqual(test_method2.current_omop2obo, 'resources/mapping_semantics/omop2obo_v0.owl')

        # clean up environment
        os.remove('resources/mapping_semantics/omop2obo_v0.owl')

        return None
