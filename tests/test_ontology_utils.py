#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import os.path
import unittest

from typing import Dict, Set
from rdflib import Graph, Namespace, URIRef  # type: ignore
from rdflib.namespace import OWL, RDF, RDFS  # type: ignore

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
        graph = Graph().parse(self.good_ontology_file_location)

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
        graph = Graph().parse(self.good_ontology_file_location)

        # retrieve classes form graph with data
        classes = gets_ontology_class_labels(graph, self.filter_classes)
        self.assertIsInstance(classes, Dict)
        self.assertEqual(2237, len(classes))

        return None

    def test_gets_ontology_class_definitions(self):
        """Tests the gets_ontology_class_definitions method."""

        # read in ontology
        graph = Graph().parse(self.good_ontology_file_location)

        # retrieve classes form graph with data
        classes = gets_ontology_class_definitions(graph, self.filter_classes)
        self.assertIsInstance(classes, Dict)
        self.assertEqual(2022, len(classes))

        return None

    def test_gets_ontology_class_synonyms(self):
        """Tests the gets_ontology_class_synonyms method."""

        # read in ontology
        graph = Graph().parse(self.good_ontology_file_location)

        # retrieve classes form graph with data
        classes = gets_ontology_class_synonyms(graph, self.filter_classes)
        self.assertIsInstance(classes, Dict)
        self.assertEqual(2109, len(classes))

        return None

    def test_gets_ontology_class_dbxrefs(self):
        """Tests the gets_ontology_class_dbxrefs method."""

        # read in ontology
        graph = Graph().parse(self.good_ontology_file_location)

        # retrieve classes form graph with data
        classes = gets_ontology_class_dbxrefs(graph, self.filter_classes)
        self.assertIsInstance(classes, Dict)
        self.assertEqual(267, len(classes))

        return None

    def test_gets_deprecated_ontology_classes(self):
        """Tests the gets_deprecated_ontology_classes method."""

        # read in ontology
        graph = Graph().parse(self.good_ontology_file_location)

        # retrieve classes form graph with data
        classes = gets_deprecated_ontology_classes(graph, 'SO')

        self.assertIsInstance(classes, Set)
        self.assertEqual(239, len(classes))

        return None

    def test_gets_obsolete_ontology_classes(self):
        """Tests the gets_deprecated_ontology_classes method."""

        # read in ontology
        graph = Graph().parse(self.good_ontology_file_location)

        # retrieve classes form graph with data
        classes = gets_obsolete_ontology_classes(graph, 'SO')

        self.assertIsInstance(classes, Set)
        self.assertEqual(0, len(classes))

        return None

    def test_clean_uri(self):
        """Tests the clean_uri method."""

        # read in ontology
        graph = Graph().parse(self.good_ontology_file_location)

        # create generator
        test_data = graph.subjects(RDF.type, OWL.Class)

        # test the method
        result = clean_uri(test_data)
        self.assertTrue(len(result) == 2573)

        return None

    def test_entity_search(self):
        """Tests the entity_search method."""

        # load ontology
        graph = Graph().parse(self.good_ontology_file_location, format='xml')
        so_class = URIRef('http://purl.obolibrary.org/obo/SO_0000348')

        # get ancestors when a valid class is provided -- class is URIRef
        ancestors1 = entity_search(graph, so_class, 'ancestors', None, RDFS.subClassOf)
        self.assertIsInstance(ancestors1, Dict)
        self.assertEqual(ancestors1['0'], ['http://purl.obolibrary.org/obo/SO_0000443'])
        self.assertEqual(ancestors1['1'], ['http://purl.obolibrary.org/obo/SO_0000400'])

        return None

    def test_entity_search_bad_format(self):
        """Tests the entity_search method when badly formatted class_uris are passed."""

        # load ontology
        graph = Graph().parse(self.good_ontology_file_location, format='xml')
        so_class = URIRef('http://purl.obolibrary.org/obo/SO_000034')

        # get ancestors when a valid class is provided -- class is not URIRef
        class_uri = str(so_class)
        ancestors1 = entity_search(graph, class_uri, 'ancestors', None, RDFS.subClassOf)
        self.assertEqual(ancestors1, None)

        return None

    def test_entity_search_bad_input(self):
        """Tests the entity_search method when a bad value for search_type is passed."""

        # load ontology
        graph = Graph().parse(self.good_ontology_file_location, format='xml')
        so_class = URIRef('http://purl.obolibrary.org/obo/SO_0000348')

        # get ancestors when a valid class is provided -- class is not URIRef
        class_uri = str(so_class)
        self.assertRaises(ValueError, entity_search, graph, class_uri, 'anc', None, RDFS.subClassOf)

        return None

    def test_entity_search_none(self):
        """Tests the entity_search method when an empty set of class uris is passed."""

        # load ontology
        graph = Graph().parse(self.good_ontology_file_location, format='xml')

        # get ancestors when no class is provided
        ancestors2 = entity_search(graph, '', 'ancestors', None, RDFS.subClassOf)
        self.assertEqual(ancestors2, None)

        return None

    def test_entity_search_filtered(self):
        """Tests the entity_search method when the method filters out all classes that are not from the core
        ontology."""

        # load ontology
        graph = Graph().parse(self.good_ontology_file_location, format='xml')
        so_class = URIRef('http://purl.obolibrary.org/obo/SO_0000348')

        # get ancestors when no class is provided
        ancestors3 = entity_search(graph, so_class, 'ancestors', 'SO', RDFS.subClassOf)
        self.assertIsInstance(ancestors3, Dict)
        self.assertEqual(ancestors3['0'], ['http://purl.obolibrary.org/obo/SO_0000443'])
        self.assertEqual(ancestors3['1'], ['http://purl.obolibrary.org/obo/SO_0000400'])

        return None
