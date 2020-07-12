#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import unittest

from typing import Dict

from omop2obo.utils import *


class TestDataUtils(unittest.TestCase):
    """Class to test the downloading methods from the data utility script."""

    def setUp(self):
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

        # create data to verifying grouping function
        self.group_data = pd.DataFrame({'CONCEPT_ID': ['442264', '4029098', '4141365', '133835', '133835'],
                                        'CONCEPT_DBXREF_ONT_URI': ['http://purl.obolibrary.org/obo/MONDO_0100010',
                                                                   'http://purl.obolibrary.org/obo/MONDO_0045014',
                                                                   'http://purl.obolibrary.org/obo/MONDO_0043358',
                                                                   'http://purl.obolibrary.org/obo/HP_0000964',
                                                                   'http://purl.obolibrary.org/obo/MONDO_0002406'],
                                        'CONCEPT_DBXREF_ONT_TYPE': ['MONDO', 'MONDO', 'MONDO', 'HP', 'MONDO'],
                                        'CONCEPT_DBXREF_ONT_LABEL': ['tendinopathy',
                                                                     'tetrahydrobiopterin metabolic process disease',
                                                                     'engraftment syndrome', 'eczema', 'dermatitis'],
                                        'CONCEPT_DBXREF_ONT_EVIDENCE': ['CONCEPT_DBXREF_sctid:68172002',
                                                                        'CONCEPT_DBXREF_sctid:237913008',
                                                                        'CONCEPT_DBXREF_sctid:426768001',
                                                                        'CONCEPT_DBXREF_snomedct_us:43116000',
                                                                        'CONCEPT_DBXREF_sctid:43116000']
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
        subset_data = data_frame_supersetter(self.subset_clin_data, 'CONCEPT_ID', 'CODE_COLUMN', 'CODE')

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

    def test_aggregates_column_values(self):
        """Tests the aggregates_column_values method."""

        # set-up input parameters
        agg_data = aggregates_column_values(self.subset_clin_data, 'CONCEPT_ID', ['CODE', 'CODE_COLUMN'], '|')

        # test method and output
        self.assertIsInstance(agg_data, pd.DataFrame)
        self.assertTrue(len(agg_data) == 3)
        self.assertEqual(list(agg_data.columns), ['CONCEPT_ID', 'CODE', 'CODE_COLUMN'])

        return None

    def test_data_frame_grouper(self):
        """Tests the data_frame_grouper method."""

        grouped_data = data_frame_grouper(self.group_data, 'CONCEPT_ID', 'CONCEPT_DBXREF_ONT_TYPE',
                                          aggregates_column_values)

        # test method and output
        self.assertIsInstance(grouped_data, pd.DataFrame)
        self.assertTrue(len(grouped_data) == 4)
        self.assertEqual(list(grouped_data.columns), ['CONCEPT_ID', 'CONCEPT_DBXREF_HP_URI',
                                                      'CONCEPT_DBXREF_HP_LABEL', 'CONCEPT_DBXREF_HP_EVIDENCE',
                                                      'CONCEPT_DBXREF_MONDO_URI', 'CONCEPT_DBXREF_MONDO_LABEL',
                                                      'CONCEPT_DBXREF_MONDO_EVIDENCE'])

        return None

    def test_merge_dictionaries(self):
        """Tests the merge_dictionaries method."""

        # run method and test output
        combined_dicts = merge_dictionaries(self.sample_dicts, 'dbxref')
        self.assertIsInstance(combined_dicts, Dict)
        self.assertTrue(len(combined_dicts.keys()) == 6)
        self.assertTrue(len(combined_dicts.values()) == 6)

        # test the method when reverse=True
        combined_dicts_rev = merge_dictionaries(self.sample_dicts, 'dbxref', reverse=True)
        self.assertIsInstance(combined_dicts_rev, Dict)
        self.assertTrue(len(combined_dicts_rev.keys()) == 4)
        self.assertTrue(len(combined_dicts_rev.values()) == 4)

        return None
