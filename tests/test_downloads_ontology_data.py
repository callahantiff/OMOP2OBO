#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path

from unittest import TestCase

from omop2obo.ontology_downloader import OntologyDownloader


class TestOntData(TestCase):
    """Class to test functions used when downloading ontology data sources."""

    def setUp(self):

        # initialize OntData instance
        current_directory = os.path.dirname(__file__)
        dir_loc = os.path.join(current_directory, 'data')
        self.dir_loc = os.path.abspath(dir_loc)
        self.ontologies = OntologyDownloader(self.dir_loc + '/ontology_source_list.txt')

        # pointer to owltools
        dir_loc2 = os.path.join(current_directory, 'utils/owltools')
        self.owltools_location = os.path.abspath(dir_loc2)

        return None

    def test_initialization_data_path(self):
        """Test class initialization for data_path attribute."""

        # test if file is type string
        self.assertRaises(TypeError, OntologyDownloader, list(self.dir_loc + '/ontology_source_list.txt'))

        # test if file exists
        self.assertRaises(OSError, OntologyDownloader, self.dir_loc + '/ontology_sources_lists.txt')

        # test if file is empty
        self.assertRaises(TypeError, OntologyDownloader, self.dir_loc + '/ontology_source_list_empty.txt')

        return None

    def test_input_file(self):
        """Tests data file passed to initialize class."""

        self.assertIsInstance(self.ontologies.data_path, str)
        self.assertTrue(os.stat(self.ontologies.data_path).st_size != 0)

        # make sure that bad input data is caught
        self.ontologies.data_path = self.dir_loc + '/ontology_source_bad_format.txt'
        self.assertRaises(Exception, self.ontologies.parses_resource_file)

        return None

    def test_downloads_data_from_url(self):
        """Tests downloads_data_from_url method."""

        # check path to write ontology data correctly derived
        derived_path = '/'.join(self.ontologies.data_path.split('/')[:-1]) + '/ontologies/'
        self.assertEqual(self.dir_loc + '/ontologies/', derived_path)

        # checks that the file downloads
        self.ontologies.downloads_data_from_url(self.owltools_location)
        self.assertTrue(os.path.exists(derived_path + 'hp_without_imports.owl'))

        return None

    def test_generates_source_metadata(self):
        """Tests whether or not metadata is being generated."""

        self.ontologies.parses_resource_file()
        self.ontologies.downloads_data_from_url(self.owltools_location)

        # generate metadata for downloaded file
        self.ontologies.generates_source_metadata()

        # check that metadata was generated
        self.assertTrue(len(self.ontologies.metadata) == 4)

        # check that the metadata content is correct
        self.assertEqual(4, len(self.ontologies.metadata[1]))
        self.assertTrue('DOWNLOAD_URL' in self.ontologies.metadata[1][0])
        self.assertTrue('DOWNLOAD_DATE' in self.ontologies.metadata[1][1])
        self.assertTrue('FILE_SIZE_IN_BYTES' in self.ontologies.metadata[1][2])
        self.assertTrue('DOWNLOADED_FILE_LOCATION' in self.ontologies.metadata[1][3])

        # check for metadata
        self.assertTrue(os.path.exists(self.dir_loc + '/ontologies/ontology_source_metadata.txt'))

        # clean up environment
        os.remove(self.dir_loc + '/ontologies/hp_without_imports.owl')
        os.remove(self.dir_loc + '/ontologies/ontology_source_metadata.txt')

        return None
