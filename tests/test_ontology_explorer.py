#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os.path
import pandas
import pickle
import shutil

from rdflib import Graph
from typing import Dict
from unittest import TestCase

from omop2obo.ontology_explorer import OntologyInfoExtractor


class TestOntologyInfoExtractor(TestCase):
    """Class to test functions used when extracting data from ontologies."""

    def setUp(self):

        # initialize OntologyInfoExtractor instance
        current_directory = os.path.dirname(__file__)
        dir_loc = os.path.join(current_directory, 'data')
        self.dir_loc = os.path.abspath(dir_loc)
        self.ontology_directory = self.dir_loc + '/ontologies'
        self.ont_dictionary = {'so': self.ontology_directory + '/so_without_imports.owl'}
        self.ontologies = OntologyInfoExtractor(self.ontology_directory, self.ont_dictionary)

        return None

    def test_initialization_ontology_directory(self):
        """Test class initialization for ontologies_directory."""

        # move files out ontologies directory
        shutil.copyfile(self.ontology_directory + '/empty_hp_without_imports.owl',
                        self.dir_loc + '/empty_hp_without_imports.owl')
        shutil.copyfile(self.ontology_directory + '/so_without_imports.owl',
                        self.dir_loc + '/so_without_imports.owl')

        os.remove(self.ontology_directory + '/empty_hp_without_imports.owl')
        os.remove(self.ontology_directory + '/so_without_imports.owl')

        # test when resource/ontologies directory does not exist
        self.assertRaises(OSError, OntologyInfoExtractor, 'ontologies', self.ont_dictionary)

        # test if file is empty
        self.assertRaises(IndexError, OntologyInfoExtractor, self.ontology_directory, self.ont_dictionary)

        # move files back
        shutil.copyfile(self.dir_loc + '/empty_hp_without_imports.owl',
                        self.ontology_directory + '/empty_hp_without_imports.owl')
        shutil.copyfile(self.dir_loc + '/so_without_imports.owl',
                        self.ontology_directory + '/so_without_imports.owl')

        os.remove(self.dir_loc + '/empty_hp_without_imports.owl')
        os.remove(self.dir_loc + '/so_without_imports.owl')

        return None

    def test_initialization_graph(self):
        """Test class initialization for creation of a graph object."""

        # verify that graph object is created
        self.assertIsInstance(self.ontologies.graph, Graph)

        return None

    def test_initialization_ont_directory(self):
        """Test class initialization for creation of the ont_directory object."""

        # verify that graph object is created
        self.assertIsInstance(self.ontologies.ont_directory, str)

        return None

    def test_ontology_dictionary(self):
        """Tests the ontology_dictionary object created after initializing the class."""

        # make sure that the ontology dictionary has been created
        self.assertIsInstance(self.ontologies.ont_dictionary, Dict)

        # make sure that only files with data were added
        self.assertTrue(len(self.ontologies.ont_dictionary) == 1)

        # make sure that the dictionary was created correctly
        self.assertIn('so', self.ontologies.ont_dictionary.keys())
        self.assertIn(self.ontology_directory + '/so_without_imports.owl', self.ontologies.ont_dictionary['so'])

        return None

    def test_get_ontology_information(self):
        """Tests the get_ontology_information method."""

        # load graph to enable testing
        self.ontologies.graph = Graph().parse(self.ontology_directory + '/so_without_imports.owl', format='xml')

        # run method
        results = self.ontologies.get_ontology_information('so')

        # check results output
        self.assertIsInstance(results, Dict)

        # check results content
        self.assertIn('label', results.keys())
        self.assertIn('definition', results.keys())
        self.assertIn('dbxref', results.keys())
        self.assertIn('synonym', results.keys())

        # check lengths of sub-dictionaries
        self.assertTrue(len(results['label']) == 2237)
        self.assertTrue(len(results['definition']) == 2022)
        self.assertTrue(len(results['dbxref']) == 267)
        self.assertTrue(len(results['synonym']) == 2109)

        return None

    def test_creates_pandas_dataframe(self):
        """Tests the creates_pandas_dataframe method."""

        # load graph to enable testing
        self.ontologies.graph = Graph().parse(self.ontology_directory + '/so_without_imports.owl', format='xml')
        self.ontologies.master_ontology_dictionary['so'] = {'df': None, 'ancestors': None, 'children': None}

        # run method
        results = self.ontologies.get_ontology_information('so')
        ont_df = self.ontologies.creates_pandas_dataframe(results, 'so')

        # test method returned a Pandas DataFrame object
        self.assertIsInstance(ont_df, pandas.DataFrame)
        self.assertTrue(len(ont_df) == 8323)
        cols = ['obo_id', 'code', 'string', 'string_type', 'dbx', 'dbx_type', 'dbx_source', 'dbx_source_name',
                'obo_source', 'obo_semantic_type']
        self.assertEqual(list(ont_df.columns), cols)

        # check that pickled files were created
        self.assertTrue(os.path.exists(self.ontology_directory + '/so_ontology_hierarchy_information.pkl'))
        os.remove(self.ontology_directory + '/so_ontology_hierarchy_information.pkl')  # clean up environment

        return None

    def test_ontology_entity_finder(self):
        """Tests the ontology_entity_finder method."""

        # load graph to enable testing
        self.ontologies.graph = Graph().parse(self.ontology_directory + '/so_without_imports.owl', format='xml')
        self.ontologies.master_ontology_dictionary['so'] = {'df': None, 'ancestors': None, 'children': None}

        # run method
        results = self.ontologies.get_ontology_information('so')
        ont_df = self.ontologies.creates_pandas_dataframe(results, 'so')
        self.ontologies.ontology_entity_finder(ont_df, 'so')

        # check that json files were created
        anc = self.ontology_directory + '/so_ontology_ancestors.json'
        kids = self.ontology_directory + '/so_ontology_children.json'
        self.assertTrue(os.path.exists(anc))
        self.assertTrue(os.path.exists(kids))

        # read in data and check values
        obo_anc = json.load(open(anc, 'r'))
        obo_kid = json.load(open(kids, 'r'))
        self.assertIsInstance(obo_anc, Dict)
        self.assertIsInstance(obo_kid, Dict)
        self.assertEqual(len(obo_anc), 2237)
        self.assertEqual(len(obo_kid), 2237)

        # obo ancs entry check
        anc_ans = {'0': ['http://purl.obolibrary.org/obo/SO_0001999'],
                   '1': ['http://purl.obolibrary.org/obo/SO_0000713'],
                   '2': ['http://purl.obolibrary.org/obo/SO_0000714'],
                   '3': ['http://purl.obolibrary.org/obo/SO_0001683'],
                   '4': ['http://purl.obolibrary.org/obo/SO_0001411'],
                   '5': ['http://purl.obolibrary.org/obo/SO_0000001'],
                   '6': ['http://purl.obolibrary.org/obo/SO_0000110']}
        self.assertEqual(obo_anc['http://purl.obolibrary.org/obo/SO_0002030'], anc_ans)

        # obo kid entry check
        self.assertEqual(len(obo_kid['http://purl.obolibrary.org/obo/SO_0000344']['0']), 2)

        # clean up environment
        os.remove(anc)
        os.remove(kids)

        return None

    def test_ontology_processor(self):
        """Tests the the ontology_processor method."""

        # run method
        self.ontologies.ontology_processor()

        # check that files were created
        obo = self.ontology_directory + '/so_ontology_hierarchy_information.pkl'
        anc = self.ontology_directory + '/so_ontology_ancestors.json'
        kids = self.ontology_directory + '/so_ontology_children.json'
        self.assertTrue(os.path.exists(obo))
        self.assertTrue(os.path.exists(anc))
        self.assertTrue(os.path.exists(kids))

        # read in the data
        max_bytes = 2 ** 31 - 1; input_size = os.path.getsize(obo); bytes_in = bytearray(0)
        with open(obo, 'rb') as f_in:
            for _ in range(0, input_size, max_bytes): bytes_in += f_in.read(max_bytes)
        obo_df = pickle.loads(bytes_in)
        obo_anc = json.load(open(anc, 'r'))
        obo_kid = json.load(open(kids, 'r'))

        # make sure that Pandas DataFrame looks right
        self.assertIsInstance(obo_df, pandas.DataFrame)
        self.assertTrue(len(obo_df) == 8323)

        # check results content of entity dictionaries
        self.assertIsInstance(obo_anc, Dict)
        self.assertIsInstance(obo_kid, Dict)
        self.assertEqual(len(obo_anc), 2237)
        self.assertEqual(len(obo_kid), 2237)

        # check the output of the metadata dictionary
        print(self.ontologies.master_ontology_dictionary)

        # clean up environment
        os.remove(obo)
        os.remove(anc)
        os.remove(kids)

        return None
