#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gzip
import os.path
import pandas as pd
import requests
import responses
import shutil
import unittest
import urllib3

from typing import Dict

from omop2obo.utils import *

# disable warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TestDataUtils(unittest.TestCase):
    """Class to test the downloading methods from the data utility script."""

    def setUp(self):
        # create temporary directory to store data for testing
        current_directory = os.path.dirname(__file__)
        dir_loc = os.path.join(current_directory, 'data/temp')
        self.dir_loc = os.path.abspath(dir_loc)
        os.mkdir(self.dir_loc)

        # create fake zipped data
        empty_zip_data = b'1F   8B  08  00  00  00  00  00  00  0B'

        with open(self.dir_loc + '/variant_summary.txt.gz', 'wb') as zp:
            zp.write(empty_zip_data)

        content = b'Lots of content here'
        with gzip.open(self.dir_loc + '/variant_summary.txt.gz', 'wb') as f:
            f.write(content)

        # create some fake ftp data
        with open(self.dir_loc + '/hgnc_complete_set.txt', 'w') as file:
            file.write('None')

        # set some urls
        self.url = 'https://proconsortium.org/download/current/promapping.txt'
        self.ftp_url = 'ftp://ftp.ebi.ac.uk/pub/databases/genenames/new/tsv/hgnc_complete_set.txt'
        self.gzipped_ftp_url = 'ftp://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz'
        self.zipped_url = 'https://reactome.org/download/current/ReactomePathways.gmt.zip'
        self.gzipped_url = 'https://www.disgenet.org/static/disgenet_ap1/files/downloads/disease_mappings.tsv.gz'

        # set write location
        self.write_location = self.dir_loc + '/'

        # create some fake Pandas DataFrames
        self.clin_data = pd.DataFrame({'CONCEPT_ID': ['4331309', '4331309', '37018594', '37018594', '442264'],
                                       'CONCEPT_SOURCE_CODE': ['2265305', '2265305', '802510', '802510', '6817202'],
                                       'UMLS_CUI': ['C0729608', 'C0729608', 'C4075981', 'C4075981', 'C0151936'],
                                       'UMLS_CODE': ['2265305', '2265305', '802510', '802510', '6817202']
                                       })
        self.subset_clin_data = pd.DataFrame({'CONCEPT_ID': ['4331309', '4331309', '37018594', '37018594', '442264',
                                                             '4331309', '4331309', '37018594', '37018594', '442264',
                                                             '4331309', '4331309', '37018594', '37018594', '442264'],
                                              'CODE': ['2265305', '2265305', '802510', '802510', '6817202',
                                                       'C0729608', 'C0729608', 'C4075981', 'C4075981', 'C0151936',
                                                       '2265305', '2265305', '802510', '802510', '6817202'],
                                              'CODE_COLUMN': ['CONCEPT_SOURCE_CODE'] * 5 +
                                                             ['UMLS_CUI'] * 5 +
                                                             ['UMLS_CODE'] * 5
                                              })

        self.string_data = pd.DataFrame({'CONCEPT_ID': ['4331309', '37018594', '442264', '4029098', '4012199'],
                                         'CONCEPT_LABEL': ['Myocarditis due to infectious agent',
                                                           'Complement level below reference range',
                                                           'Disorder of tendon',
                                                           'Disorder of tetrahydrobiopterin metabolism',
                                                           'Vulval pain'],
                                         'CONCEPT_SYNONYM': ['Myocarditis due to infectious agent | Infective '
                                                             'myocarditis | Myocarditis due to infectious agent ('
                                                             'disorder)',
                                                             'Complement level below reference range | Complement '
                                                             'level below reference range (finding)',
                                                             'Disorder of tendon (disorder) | Disorder of tendon | '
                                                             'Tendon disorder',
                                                             'Disorder of tetrahydrobiopterin metabolism (disorder) | '
                                                             'Disorder of tetrahydrobiopterin metabolism',
                                                             'Vulval pain (finding) | Vulval pain | Pain of vulva']
                                         })

        # create sample dictionaries
        self.sample_dicts = {
            'hp': {
                'dbxref': {'UMLS:C4022916': 'http://purl.obolibrary.org/obo/HP_0012400',
                           'UMLS:C4020882': 'http://purl.obolibrary.org/obo/HP_0000925',
                           'UMLS:C4021789': 'http://purl.obolibrary.org/obo/HP_0000925'},
                'label': {'abnormal aldolase level': 'http://purl.obolibrary.org/obo/HP_0012400',
                          'abnormality of the vertebral column': 'http://purl.obolibrary.org/obo/HP_0000925',
                          'patulous urethra': 'http://purl.obolibrary.org/obo/HP_0025417'}},
            'mondo': {
                'dbxref': {'GARD:0009221': 'http://purl.obolibrary.org/obo/MONDO_0022509',
                           'DOID:5726': 'http://purl.obolibrary.org/obo/MONDO_0003611',
                           'UMLS:C3642324': 'http://purl.obolibrary.org/obo/MONDO_0003611'},
                'label': {'asternia': 'http://purl.obolibrary.org/obo/MONDO_0022509',
                          'hyperekplexia 3': 'http://purl.obolibrary.org/obo/MONDO_0013827',
                          'color vision disorder': 'http://purl.obolibrary.org/obo/MONDO_0001703'}}
        }

        return None

    @responses.activate
    def test_url_download(self):
        """Tests url_download method"""

        # filename
        filename = self.url.split('/')[-1]

        # fake file connection
        responses.add(responses.GET,
                      self.url,
                      body='test',
                      status=200,
                      content_type='text/plain',
                      headers={'Content-Length': '1200'}
                      )

        # test mocked download
        url_download(self.url, self.write_location, filename)
        self.assertTrue(os.path.exists(self.write_location + filename))

        return None

    @responses.activate
    def test_ftp_url_download(self):
        """Tests ftp_url_download method."""

        filename = self.ftp_url.split('/')[-1]
        self.assertTrue(os.path.exists(self.write_location + filename))

        return None

    @responses.activate
    def test_gzipped_ftp_url_download(self):
        """Tests gzipped_ftp_url_download method."""

        # get ftp server info
        file = self.gzipped_ftp_url.replace('ftp://', '').split('/')[-1]
        write_loc = self.write_location + '{filename}'.format(filename=file)

        # read in gzipped file,uncompress, and write to directory
        with gzip.open(write_loc, 'rb') as fid_in:
            with open(write_loc.replace('.gz', ''), 'wb') as f:
                f.write(fid_in.read())
        fid_in.close()

        # change filename and remove gzipped and original files
        os.remove(write_loc)

        # test mocked download
        self.assertFalse(os.path.exists(write_loc))
        self.assertTrue(os.path.exists(write_loc[:-3]))

        return None

    @responses.activate
    def test_zipped_url_download(self):
        """Tests zipped_url_download methods."""

        # filename
        filename = self.zipped_url.split('/')[-1]

        # fake file connection
        responses.add(
            responses.GET,
            self.zipped_url,
            body=b'1F   8B  08  00  00  00  00  00  00  0B',
            status=200,
            content_type='zip',
            headers={'Content-Length': '1200'}
        )

        # test mocked download
        # zipped_url_download(self.zipped_url, self.write_location, filename)
        r = requests.get(self.zipped_url, allow_redirects=True)
        self.assertTrue(r.ok)

        # test writing data
        downloaded_data = open(self.write_location + '{filename}'.format(filename=filename[:-4]), 'wb')
        downloaded_data.write(r.content)
        downloaded_data.close()

        self.assertFalse(os.path.exists(self.write_location + filename))
        self.assertTrue(os.path.exists(self.write_location + filename[:-4]))

        return None

    @responses.activate
    def test_gzipped_url_download(self):
        """Tests gzipped_url_download method when returning a 200 status."""

        # filename
        filename = self.gzipped_url.split('/')[-1]

        # fake file connection
        responses.add(
            responses.GET,
            self.gzipped_url,
            body=gzip.compress(b'test data'),
            status=200,
            content_type='gzip',
            headers={'Content-Length': '1200'}
        )

        # test mocked download
        # gzipped_url_download(self.gzipped_url, self.write_location, filename)
        r = requests.get(self.gzipped_url, allow_redirects=True, verify=False)
        self.assertTrue(r.ok)

        # test writing data
        with open(self.write_location + '{filename}'.format(filename=filename[:-3]), 'wb') as outfile:
            outfile.write(gzip.decompress(r.content))
        outfile.close()
        self.assertFalse(os.path.exists(self.write_location + filename))
        self.assertTrue(os.path.exists(self.write_location + filename[:-3]))

        return None

    def test_data_downloader(self):
        """Tests data_downloader method."""

        # url data
        data_downloader(self.url, self.write_location)
        self.assertTrue(os.path.exists(self.write_location + self.url.split('/')[-1]))

        # # ftp url data
        self.assertTrue(os.path.exists(self.write_location + self.ftp_url.split('/')[-1]))

        # gzipped ftp url data
        file = self.gzipped_ftp_url.replace('ftp://', '').split('/')[-1]
        write_loc = self.write_location + '{filename}'.format(filename=file)
        self.assertTrue(os.path.exists(os.path.exists(write_loc[:-3])))

        # zipped data
        data_downloader(self.zipped_url, self.write_location)
        self.assertTrue(os.path.exists(self.write_location + self.zipped_url.split('/')[-1][:-4]))

        # gzipped data
        data_downloader(self.gzipped_url, self.write_location)
        self.assertTrue(os.path.exists(self.write_location + self.gzipped_url.split('/')[-1][:-3]))

        return None

    def test_data_frame_subsetter(self):
        """Tests the data_frame_subsetter method."""

        # run method and test output
        subset_data = data_frame_subsetter(self.clin_data, 'CONCEPT_ID',
                                           ['CONCEPT_SOURCE_CODE', 'UMLS_CUI', 'UMLS_CODE'])

        self.assertIsInstance(subset_data, pd.DataFrame)
        self.assertTrue(len(subset_data) == 9)
        self.assertEqual(list(subset_data.columns), ['CONCEPT_ID', 'CODE', 'CODE_COLUMN'])

        return None

    def test_data_frame_supersetter(self):
        """Tests the data_frame_supersetter method."""

        # run method and test output
        subset_data = data_frame_supersetter(self.subset_clin_data, 'CONCEPT_ID', ('CODE_COLUMN'), ('CODE'))

        self.assertIsInstance(subset_data, pd.DataFrame)
        self.assertTrue(len(subset_data) == 3)
        self.assertEqual(list(subset_data.columns), ['CONCEPT_ID', 'CONCEPT_SOURCE_CODE', 'UMLS_CODE', 'UMLS_CUI'])

        return None

    def test_column_splitter(self):
        """Tests the column_splitter method."""

        # set-up input parameters
        delimited_columns = ['CONCEPT_LABEL', 'CONCEPT_SYNONYM']
        split_data = column_splitter(self.string_data, delimited_columns, '|')

        # test method and output
        self.assertIsInstance(split_data, pd.DataFrame)
        self.assertTrue(len(split_data) == 13)
        self.assertEqual(list(split_data.columns), ['CONCEPT_ID', 'CONCEPT_LABEL', 'CONCEPT_SYNONYM'])

        return None

    def test_merge_dictionaries(self):
        """Tests the merge_dictionaries method."""

        # run method and test output
        combined_dicts = merge_dictionaries(self.sample_dicts, 'dbxref')

        self.assertIsInstance(combined_dicts, Dict)
        self.assertTrue(len(combined_dicts.keys()) == 6)
        self.assertTrue(len(combined_dicts.values()) == 6)

        return None

    def tearDown(self):
        # remove temp directory
        shutil.rmtree(self.dir_loc)

        return None
