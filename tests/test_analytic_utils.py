#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import os
import pandas as pd
import unittest

from typing import Dict, List, Tuple
from omop2obo.utils import *


class TestAnalyticUtils(unittest.TestCase):
    """Class to test the methods created in the analytic utility script."""

    def setUp(self):
        current_directory = os.path.dirname(__file__)
        dir_loc = os.path.join(current_directory, 'data')
        self.dir_loc = os.path.abspath(dir_loc)

        # read in chi-square test data
        self.chi_square_data = pd.read_csv(self.dir_loc + '/chi_square_test_data.txt', sep=',', index_col='ontology')

        # create some test data
        self.dbxref_test = pd.DataFrame({'CONCEPT_ID': [22288, 22426, 23986, 24609, 24966],
                                         'CONCEPT_LABEL': ['Hereditary elliptocytosis', 'Congenital macrostomia',
                                                           'Disorder of pituitary gland', 'Hypoglycemia',
                                                           'Esophageal varices'],
                                         'CONCEPT_DBXREF_HP_URI': ['HP_0004445', 'HP_0000154',
                                                                   'HP_0012503 | HP_0011747',
                                                                   'HP_0001943', 'HP_0002040'],
                                         'ANCESTOR_DBXREF_HP_URI': ['HP_0004445 | HP_0001871 | HP_0001877',
                                                                    'HP_0011024 | HP_0000153 | HP_0000154 | HP_0002664 '
                                                                    '| HP_0010566', 'HP_0002011 | HP_0001298 | '
                                                                                    'HP_0000818 | HP_0012503 | '
                                                                                    'HP_0011747', 'HP_0001943 | '
                                                                                                  'HP_0000818',
                                                                    'HP_0001626 | HP_0002619 | HP_0002040 | '
                                                                    'HP_0011024'],
                                         'CONCEPT_DBXREF_MONDO_URI': ['MONDO_0008165', 'MONDO_0013300', 'MONDO_0003381',
                                                                      'MONDO_0004946', 'MONDO_0001221'],
                                         'ANCESTOR_DBXREF_MONDO_URI': ['MONDO_0024505 | MONDO_0000001 | MONDO_0021199 '
                                                                       '| MONDO_0003847 | MONDO_0005570 | '
                                                                       'MONDO_0044347 | MONDO_0017319 | '
                                                                       'MONDO_0008165', 'MONDO_0024505 | MONDO_0000001 '
                                                                                        '| MONDO_0021199 | '
                                                                                        'MONDO_0004335 | MONDO_0000839 '
                                                                                        '| MONDO_0005042 | '
                                                                                        'MONDO_0006858 | '
                                                                                        'MONDO_0013300',
                                                                       'MONDO_0024505 | MONDO_0000001 | MONDO_0021199 '
                                                                       '| MONDO_0002602 | MONDO_0005071 | '
                                                                       'MONDO_0005042 | MONDO_0005560 | MONDO_0005151 '
                                                                       '| MONDO_0002150 | MONDO_0003381',
                                                                       'MONDO_0024505 | MONDO_0000001 | MONDO_0021199 '
                                                                       '| MONDO_0005066 | MONDO_0019052 | '
                                                                       'MONDO_0004946 | MONDO_0019214 | MONDO_0037792 '
                                                                       '| MONDO_0005151', 'MONDO_0024505 | '
                                                                                          'MONDO_0000001 | '
                                                                                          'MONDO_0021199 | '
                                                                                          'MONDO_0004634 | '
                                                                                          'MONDO_0004995 | '
                                                                                          'MONDO_0005385 | '
                                                                                          'MONDO_0000651 | '
                                                                                          'MONDO_0008638 | '
                                                                                          'MONDO_0001221']
                                         })

        self.dbxref_test2 = pd.DataFrame({'CONCEPT_ID': [22274, 22281, 22288, 22340, 22350],
                                          'CONCEPT_LABEL': ['Neoplasm of uncertain behavior of larynx', 'Hb SS disease',
                                                            'Hereditary elliptocytosis',
                                                            'Esophageal varices without bleeding', 'Edema of larynx'],
                                          'CONCEPT_DBXREF_CATEGORY_URI': [np.nan, np.nan, 'HP_0004445', np.nan,
                                                                          'HP_0012027'],
                                          'CONCEPT_DBXREF_CATEGORY_LABEL': [np.nan, np.nan, 'elliptocytosis', np.nan,
                                                                            'laryngeal edema'],
                                          'CONCEPT_DBXREF_CATEGORY_EVIDENCE': [np.nan, np.nan,
                                                                               'CONCEPT_DBXREF_snomed:191169008 | '
                                                                               'CONCEPT_DBXREF_umls:C0013902', np.nan,
                                                                               'CONCEPT_DBXREF_snomed:51599000 | '
                                                                               'CONCEPT_DBXREF_umls:C0023052'],
                                          'ANCESTOR_DBXREF_CATEGORY_URI': ['HP_0012288 | HP_0100606 | HP_0100605 | '
                                                                           'HP_0002664 | HP_0002795 | HP_0002094 | '
                                                                           'HP_0002098', 'HP_0001903 | HP_0002664 | '
                                                                                         'HP_0010566 | HP_0001871 | '
                                                                                         'HP_0001877', 'HP_0004445 | '
                                                                                                       'HP_0001871 | '
                                                                                                       'HP_0001877',
                                                                           'HP_0001626 | HP_0002619 | HP_0002040 | '
                                                                           'HP_0011024', 'HP_0000969 | HP_0012027 | '
                                                                                         'HP_0002795 | HP_0002094 | '
                                                                                         'HP_0002098 | HP_0100665'],
                                          'ANCESTOR_DBXREF_CATEGORY_LABEL': ['neoplasm of head and neck | neoplasm of '
                                                                             'the respiratory system | neoplasm of '
                                                                             'the larynx | neoplasm | functional '
                                                                             'respiratory abnormality | dyspnea | '
                                                                             'respiratory distress',
                                                                             'anemia | neoplasm | hamartoma | '
                                                                             'abnormality of blood and blood-forming '
                                                                             'tissues | abnormal erythrocyte '
                                                                             'morphology', 'elliptocytosis | '
                                                                                           'abnormality of blood and '
                                                                                           'blood-forming tissues | '
                                                                                           'abnormal erythrocyte '
                                                                                           'morphology',
                                                                             'abnormality of the cardiovascular '
                                                                             'system | varicose veins | esophageal '
                                                                             'varix | abnormality of the '
                                                                             'gastrointestinal tract',
                                                                             'edema | laryngeal edema | functional '
                                                                             'respiratory abnormality | dyspnea | '
                                                                             'respiratory distress | angioedema'],
                                          'ANCESTOR_DBXREF_CATEGORY_EVIDENCE': ['ANCESTOR_DBXREF_snomed:255055008 | '
                                                                                'ANCESTOR_DBXREF_snomed:448708002 | '
                                                                                'ANCESTOR_DBXREF_snomed:126667002 | '
                                                                                'ANCESTOR_DBXREF_snomed:126692004 | '
                                                                                'ANCESTOR_DBXREF_umls:C0027651 | '
                                                                                'ANCESTOR_DBXREF_umls:C1260922 | '
                                                                                'ANCESTOR_DBXREF_umls:C0013404 | '
                                                                                'ANCESTOR_DBXREF_umls:C0018671 | '
                                                                                'ANCESTOR_DBXREF_umls:C0035244 | '
                                                                                'ANCESTOR_DBXREF_umls:C0023055',
                                                                                'ANCESTOR_DBXREF_snomed:165397008 | '
                                                                                'ANCESTOR_DBXREF_snomed:271737000 | '
                                                                                'ANCESTOR_DBXREF_umls:C0027651 | '
                                                                                'ANCESTOR_DBXREF_umls:C0018552 | '
                                                                                'ANCESTOR_DBXREF_umls:C0018939 | '
                                                                                'ANCESTOR_DBXREF_umls:C0391870 | '
                                                                                'ANCESTOR_DBXREF_umls:C0162119 | '
                                                                                'ANCESTOR_DBXREF_umls:C0002871',
                                                                                'ANCESTOR_DBXREF_snomed:191169008 | '
                                                                                'ANCESTOR_DBXREF_umls:C0018939 | '
                                                                                'ANCESTOR_DBXREF_umls:C0391870 | '
                                                                                'ANCESTOR_DBXREF_umls:C0013902 | '
                                                                                'ANCESTOR_DBXREF_umls:C0427480',
                                                                                'ANCESTOR_DBXREF_snomed:49601007 | '
                                                                                'ANCESTOR_DBXREF_snomed:128060009 | '
                                                                                'ANCESTOR_DBXREF_snomed:28670008 | '
                                                                                'ANCESTOR_DBXREF_meddra:10056091 | '
                                                                                'ANCESTOR_DBXREF_umls:C0017178 | '
                                                                                'ANCESTOR_DBXREF_umls:C0007222 | '
                                                                                'ANCESTOR_DBXREF_umls:C0042345 | '
                                                                                'ANCESTOR_DBXREF_umls:C0014867',
                                                                                'ANCESTOR_DBXREF_snomed:267038008 | '
                                                                                'ANCESTOR_DBXREF_snomed:51599000 | '
                                                                                'ANCESTOR_DBXREF_umls:C1260922 | '
                                                                                'ANCESTOR_DBXREF_umls:C0013404 | '
                                                                                'ANCESTOR_DBXREF_umls:C0013604 | '
                                                                                'ANCESTOR_DBXREF_umls:C0002994 | '
                                                                                'ANCESTOR_DBXREF_umls:C0023052']

                                          })

        return None

    def test_reconfigures_dataframe(self):
        """Tests the reconfigures_dataframe method."""

        # run method and test output
        stacked_data = reconfigures_dataframe(['HP', 'MONDO'], self.dbxref_test)

        self.assertIsInstance(stacked_data, pd.DataFrame)
        self.assertTrue(len(stacked_data) == 10)
        self.assertEqual(list(stacked_data.columns), ['CONCEPT_ID', 'CONCEPT_LABEL', 'CONCEPT_DBXREF_CATEGORY_URI',
                                                      'ANCESTOR_DBXREF_CATEGORY_URI', 'CATEGORY'])

        return None

    def test_splits_concept_levels(self):
        """Tests the splits concept levels method."""

        split_data = splits_concept_levels(self.dbxref_test2, 'DBXREF')

        # check output
        self.assertIsInstance(split_data, List)
        self.assertTrue(len(split_data) == 2)
        concept_data, ancestor_data = split_data

        # check concept-level results
        self.assertIsInstance(concept_data, Tuple)
        self.assertTrue(len(concept_data) == 2)
        self.assertIsInstance(concept_data[0], pd.DataFrame)
        self.assertTrue(len(concept_data[0]) == 2)
        self.assertIsInstance(concept_data[1], List)
        self.assertTrue(len(concept_data[1]) == 2)

        # check ancestor-level results
        self.assertIsInstance(ancestor_data, Tuple)
        self.assertTrue(len(ancestor_data) == 2)
        self.assertIsInstance(ancestor_data[0], pd.DataFrame)
        self.assertTrue(len(ancestor_data[0]) == 5)
        self.assertIsInstance(ancestor_data[1], List)
        self.assertTrue(len(ancestor_data[1]) == 25)

        return None

    def test_outputs_ontology_metadata(self):
        """Tests the outputs_ontology_metadata method."""

        # set-up input data
        metadata = ['label', 'dbxref', 'synonym', 'synonym_type']
        ontology_list = ['hp']

        ontology_data = {'hp': {'dbxref': {'umls:c4023552': 'http://purl.obolibrary.org/obo/HP_0011071',
                                           'umls:c4023164': 'http://purl.obolibrary.org/obo/HP_0011843',
                                           'umls:c1837087': 'http://purl.obolibrary.org/obo/HP_0008002',
                                           'umls:c4022709': 'http://purl.obolibrary.org/obo/HP_0012852'},
                                'label': {'abnormality of skeletal physiology':
                                          'http://purl.obolibrary.org/obo/HP_0011843',
                                          'abnormality of permanent molar morphology':
                                          'http://purl.obolibrary.org/obo/HP_0011071',
                                          'hepatic bridging fibrosis':
                                          'http://purl.obolibrary.org/obo/HP_0012852',
                                          'abnormality of macular pigmentation':
                                          'http://purl.obolibrary.org/obo/HP_0008002'},
                                'synonym': {'abnormality of shape of adult molar':
                                            'http://purl.obolibrary.org/obo/HP_0011071',
                                            'abnormality of shape of permanent molar':
                                            'http://purl.obolibrary.org/obo/HP_0011071',
                                            'macular pigmentary changes': 'http://purl.obolibrary.org/obo/HP_0008002'},
                                'synonym_type': {'abnormality of shape of adult molar': 'hasExactSynonym',
                                                 'abnormality of shape of permanent molar': 'hasExactSynonym',
                                                 'macular pigmentary changes': 'hasRelatedSynonym'}}}

        # test method
        ont_results = outputs_ontology_metadata(ontology_data, ontology_list, metadata)
        self.assertIsInstance(ont_results, Dict)
        self.assertEqual(list(ont_results.keys()), ['hp'])
        self.assertIn('dbxref', list(ont_results['hp'].keys()))
        self.assertIn('label', list(ont_results['hp'].keys()))
        self.assertIn('synonym', list(ont_results['hp'].keys()))
        self.assertIn('synonym_type', list(ont_results['hp'].keys()))
        self.assertEqual(ont_results['hp']['label'], 4)
        self.assertEqual(ont_results['hp']['dbxref'], 4)
        self.assertEqual(ont_results['hp']['synonym'], 3)
        self.assertEqual(', '.join(sorted(ont_results['hp']['synonym_type'].split(', '))),
                         'hasExactSynonym, hasRelatedSynonym')

        return None

    def test_get_asterisks_for_pvalues(self):
        """Tests the get_asterisks_for_pvalues method."""

        # p > 0.05
        p1 = get_asterisks_for_pvalues(0.06)
        self.assertEqual(p1, 'ns')
        # p< 0.0001
        p2 = get_asterisks_for_pvalues(0.00009)
        self.assertEqual(p2, '****')
        # p< 0.001
        p3 = get_asterisks_for_pvalues(0.0009)
        self.assertEqual(p3, '***')
        # p< 0.01
        p4 = get_asterisks_for_pvalues(0.009)
        self.assertEqual(p4, '**')
        # p< 0.05
        p5 = get_asterisks_for_pvalues(0.04)
        self.assertEqual(p5, '*')

        return None

    def test_(self):
        """Tests the chisq_and_posthoc_corrected method."""

        self.assertEqual(chisq_and_posthoc_corrected(self.chi_square_data), None)

        return None
