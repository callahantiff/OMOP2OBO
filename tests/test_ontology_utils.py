#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import os
import os.path
import unittest

from typing import Dict, List, Set
from rdflib import Graph, URIRef

from omop2obo.utils import *


class TestOntologyUtils(unittest.TestCase):
    """Class to test ontology utility methods."""

    def setUp(self):
        # initialize data location
        current_directory = os.path.dirname(__file__)
        dir_loc = os.path.join(current_directory, 'data/ontologies')
        self.dir_loc = os.path.abspath(dir_loc)

        # set some real and fake file name variables
        self.not_string_filename = [self.dir_loc + '/empty_hp_without_imports.owl']
        self.not_real_file_name = self.dir_loc + '/sop_without_imports.owl'
        self.empty_ontology_file_location = self.dir_loc + '/empty_hp_without_imports.owl'
        self.good_ontology_file_location = self.dir_loc + '/so_without_imports.owl'

        # pointer to owltools
        dir_loc2 = os.path.join(current_directory, 'utils/owltools')
        self.owltools_location = os.path.abspath(dir_loc2)

        # get ontology class information
        graph = Graph().parse(self.dir_loc + '/so_without_imports.owl', format='xml')
        deprecated_classes = gets_deprecated_ontology_classes(graph, 'so')
        self.filter_classes = set([x for x in gets_ontology_classes(graph, 'so') if x not in deprecated_classes])

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
        classes = gets_ontology_classes(graph, 'SO')
        self.assertIsInstance(classes, Set)
        self.assertEqual(2476, len(classes))

        # retrieve classes form graph with no data
        no_data_graph = Graph()
        self.assertRaises(ValueError, gets_ontology_classes, no_data_graph, 'SO')

        return None

    def test_gets_ontology_class_labels(self):
        """Tests the gets_ontology_class_labels method."""

        # read in ontology
        graph = Graph()
        graph.parse(self.good_ontology_file_location)

        # retrieve classes form graph with data
        classes = gets_ontology_class_labels(graph, self.filter_classes)
        self.assertIsInstance(classes, Dict)
        self.assertEqual(2237, len(classes))

        return None

    def test_gets_ontology_class_definitions(self):
        """Tests the gets_ontology_class_definitions method."""

        # read in ontology
        graph = Graph()
        graph.parse(self.good_ontology_file_location)

        # retrieve classes form graph with data
        classes = gets_ontology_class_definitions(graph, self.filter_classes)
        self.assertIsInstance(classes, Dict)
        self.assertEqual(2004, len(classes))

        return None

    def test_gets_ontology_class_synonyms(self):
        """Tests the gets_ontology_class_synonyms method."""

        # read in ontology
        graph = Graph()
        graph.parse(self.good_ontology_file_location)

        # retrieve classes form graph with data
        classes = gets_ontology_class_synonyms(graph, self.filter_classes)
        self.assertIsInstance(classes[0], Dict)
        self.assertIsInstance(classes[1], Dict)
        self.assertEqual(3819, len(classes[0]))
        self.assertEqual(3819, len(classes[1]))

        return None

    def test_gets_ontology_class_dbxrefs(self):
        """Tests the gets_ontology_class_dbxrefs method."""

        # read in ontology
        graph = Graph()
        graph.parse(self.good_ontology_file_location)

        # retrieve classes form graph with data
        classes = gets_ontology_class_dbxrefs(graph, self.filter_classes)
        self.assertIsInstance(classes[0], Dict)
        self.assertIsInstance(classes[1], Dict)
        self.assertEqual(391, len(classes[0]))
        self.assertEqual(391, len(classes[1]))

        return None

    def test_gets_deprecated_ontology_classes(self):
        """Tests the gets_deprecated_ontology_classes method."""

        # read in ontology
        graph = Graph()
        graph.parse(self.good_ontology_file_location)

        # retrieve classes form graph with data
        classes = gets_deprecated_ontology_classes(graph, 'SO')

        self.assertIsInstance(classes, Set)
        self.assertEqual(239, len(classes))

        return None

    def test_finds_class_ancestors(self):
        """Tests the finds_class_ancestors method."""

        # load ontology
        graph = Graph().parse(self.good_ontology_file_location, format='xml')
        so_class = [URIRef('http://purl.obolibrary.org/obo/SO_0000348')]

        # get ancestors when a valid class is provided -- class is URIRef
        ancestors1 = gets_class_ancestors(graph, so_class)
        # check output
        self.assertIsInstance(ancestors1, List)
        self.assertEqual(ancestors1,
                         ['http://purl.obolibrary.org/obo/SO_0000400', 'http://purl.obolibrary.org/obo/SO_0000443'])

        # get ancestors when a valid class is provided -- class is not URIRef
        ancestors1 = gets_class_ancestors(graph, [str(x).split('/')[-1] for x in so_class])
        # check output
        self.assertIsInstance(ancestors1, List)
        self.assertEqual(ancestors1,
                         ['http://purl.obolibrary.org/obo/SO_0000400', 'http://purl.obolibrary.org/obo/SO_0000443'])

        # get ancestors when no class is provided
        ancestors2 = gets_class_ancestors(graph, [])
        # check output
        self.assertIsInstance(ancestors2, List)
        self.assertEqual(ancestors2, [])

        return None

    def test_merges_ontologies(self):
        """Tests the merges_ontologies method."""

        # set up input parameters
        ontology_repository = [x for x in glob.glob(self.dir_loc + '/*.owl') if 'empty' not in x]
        merged_ontology_file = '/OMOP2OBO_MergedOntologies.owl'

        # make sure that there is no merged ontology file in write location
        self.assertFalse(os.path.exists(self.dir_loc + merged_ontology_file))

        # run merge function and check that file was generated
        merges_ontologies(ontology_files=ontology_repository, write_location=self.dir_loc,
                          merged_ont_kg=merged_ontology_file, owltools_location=self.owltools_location)
        self.assertTrue(os.path.exists(self.dir_loc + merged_ontology_file))

        # remove file
        os.remove(self.dir_loc + merged_ontology_file)

        return None

    def test_ontology_file_formatter(self):
        """Tests the ontology_file_formatter method."""

        # set-up input methods
        owltools = self.owltools_location

        # test method handling of bad file types
        # not an owl file
        self.assertRaises(TypeError, ontology_file_formatter, self.dir_loc, '/so_with_imports.txt', owltools)

        # a file that does not exist
        self.assertRaises(IOError, ontology_file_formatter, self.dir_loc, '/sop_without_imports.owl', owltools)

        # an empty file
        self.assertRaises(TypeError, ontology_file_formatter, self.dir_loc, '/empty_hp_without_imports.txt', owltools)

        # make sure method runs on legitimate file
        self.assertTrue(ontology_file_formatter(write_location=self.dir_loc,
                                                full_kg='/so_without_imports.owl',
                                                owltools_location=owltools) is None)

        return None
