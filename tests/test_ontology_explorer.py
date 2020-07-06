#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
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
        """Test class initialization for ontologies directory."""

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
        self.assertRaises(TypeError, OntologyInfoExtractor, self.ontology_directory, self.ont_dictionary)

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
        self.assertIn('synonyms', results.keys())

        # check lengths of sub-dictionaries
        self.assertTrue(len(results['label']) == 2237)
        self.assertTrue(len(results['definition']) == 2004)
        self.assertTrue(len(results['dbxref']) == 391)
        self.assertTrue(len(results['synonyms']) == 3804)

        return None

    def test_ontology_processor(self):
        """Tests the the ontology_processor method."""

        # run method
        self.ontologies.ontology_processor()

        # check that pickled files were created
        self.assertTrue(os.path.exists(self.ontology_directory + '/so_without_imports_class_information.pickle'))

        # clean up environment
        os.remove(self.ontology_directory + '/so_without_imports_class_information.pickle')

        return None

    def test_ontology_loader(self):
        """Tests the ontology_loader method"""

        # run method
        self.ontologies.ontology_processor()
        pickled_dict = self.ontologies.ontology_loader()

        # make sure that output is correct
        self.assertTrue(len(pickled_dict.keys()) == 1)
        self.assertTrue(len(pickled_dict['so']) == 4)
        self.assertIsInstance(pickled_dict['so'], Dict)

        # check results content
        self.assertIn('label', pickled_dict['so'].keys())
        self.assertIn('definition', pickled_dict['so'].keys())
        self.assertIn('dbxref', pickled_dict['so'].keys())
        self.assertIn('synonyms', pickled_dict['so'].keys())

        # check lengths of sub-dictionaries
        self.assertTrue(len(pickled_dict['so']['label']) == 2237)
        self.assertTrue(len(pickled_dict['so']['definition']) == 2004)
        self.assertTrue(len(pickled_dict['so']['dbxref']) == 391)
        self.assertTrue(len(pickled_dict['so']['synonyms']) == 3804)

        # clean up environment
        os.remove(self.ontology_directory + '/so_without_imports_class_information.pickle')

        return None
