#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import unittest

from typing import Dict, Tuple
from omop2obo.utils import *


class TestAnalyticUtils(unittest.TestCase):
    """Class to test the methods created in the analytic utility script."""

    def setUp(self):
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
