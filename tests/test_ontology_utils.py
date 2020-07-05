import os
import os.path
import unittest

from typing import Set
from rdflib import Graph

from omop2obo.utils import gets_ontology_statistics, gets_ontology_classes, gets_deprecated_ontology_classes


class TestOntologyUtils(unittest.TestCase):
    """Class to test ontology utility methods."""

    def setUp(self):
        # initialize data location
        current_directory = os.path.dirname(__file__)
        dir_loc = os.path.join(current_directory, 'data/ontologies')
        self.dir_loc = os.path.abspath(dir_loc)

        # set some real and fake file name variables
        self.not_string_filename = [self.dir_loc + '/empty_hp_with_imports.owl']
        self.not_real_file_name = self.dir_loc + '/sop_with_imports.owl'
        self.empty_ontology_file_location = self.dir_loc + '/empty_hp_with_imports.owl'
        self.good_ontology_file_location = self.dir_loc + '/so_with_imports.owl'

        # pointer to owltools
        dir_loc2 = os.path.join(current_directory, 'utils/owltools')
        self.owltools_location = os.path.abspath(dir_loc2)

        return None

    def test_gets_ontology_statistics(self):
        """Tests gets_ontology_statistics method."""

        # test non-string file name
        self.assertRaises(TypeError, gets_ontology_statistics, self.not_string_filename)

        # test fake file name
        self.assertRaises(OSError, gets_ontology_statistics, self.not_real_file_name)

        # test empty file
        self.assertRaises(ValueError, gets_ontology_statistics, self.empty_ontology_file_location)

        # test good file
        self.assertIsNone(gets_ontology_statistics(self.good_ontology_file_location, self.owltools_location))

        return None

    def test_gets_ontology_classes(self):
        """Tests the gets_ontology_classes method."""

        # read in ontology
        graph = Graph()
        graph.parse(self.good_ontology_file_location)

        # retrieve classes form graph with data
        classes = gets_ontology_classes(graph)

        self.assertIsInstance(classes, Set)
        self.assertEqual(2573, len(classes))

        # retrieve classes form graph with no data
        no_data_graph = Graph()
        self.assertRaises(ValueError, gets_ontology_classes, no_data_graph)

        return None

    def test_gets_deprecated_ontology_classes(self):
        """Tests the gets_deprecated_ontology_classes method."""

        # read in ontology
        graph = Graph()
        graph.parse(self.good_ontology_file_location)

        # retrieve classes form graph with data
        classes = gets_deprecated_ontology_classes(graph)

        self.assertIsInstance(classes, Set)
        self.assertEqual(336, len(classes))

        return None
