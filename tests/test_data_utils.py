#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import unittest

from typing import Dict, Tuple
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

        # create example result data
        self.ont_data = {'hp': {'label': {'abetalipoproteinemia': 'http://purl.obolibrary.org/obo/HP_0008181'},
                                'dbxref': {'snomedct_us:190787008': 'http://purl.obolibrary.org/obo/HP_0008181'},
                                'dbxref_type': {'snomedct_us:190787008': 'DbXref'},
                                'synonym': {'wet lung': 'http://purl.obolibrary.org/obo/HP_0100598'},
                                'synonym_type': {'wet lung': 'hasExactSynonym'}}}
        self.source_codes = {'snomed:190787008': 'DbXref*snomedct_us'}

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
        split_data = column_splitter(self.string_data, 'CONCEPT_ID', delimited_columns, '|')

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

    def test_normalizes_source_codes(self):
        """Tests the normalizes_source_codes method."""

        # set-up input data
        data = pd.DataFrame(['reactome:r-hsa-937045', 'http://linkedlifedata.com/resource/umls/id/C0010323',
                             'snomedct_us:111395007', 'pesticides:derivatives/benazolin-ethyl'], columns=['CODE'])

        # set-up input dictionary
        source_code_dict = {'snomedct_us': 'snomed', 'http://linkedlifedata.com/resource/umls/id': 'umls'}

        # test method
        result = normalizes_source_codes(data['CODE'].to_frame(), source_code_dict)
        self.assertIsInstance(result, pd.Series)
        self.assertIn('reactome:r-hsa-937045', list(result))
        self.assertIn('umls:c0010323', list(result))
        self.assertIn('snomed:111395007', list(result))
        self.assertIn('pesticides:derivatives:benazolin-ethyl', list(result))

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

    def test_ohdsi_ananke(self):
        """Tests the ohdsi_ananke method."""

        # create input data
        combo_dict_df = pd.DataFrame({'CODE': ['hp:0001901', 'hp:0011737', 'hp:0002883', 'hp:0002883'],
                                      'CONCEPT_DBXREF_ONT_URI': ['http://purl.obolibrary.org/obo/HP_0001901',
                                                                 'http://purl.obolibrary.org/obo/HP_0011737',
                                                                 'http://purl.obolibrary.org/obo/HP_0002883',
                                                                 'http://purl.obolibrary.org/obo/HP_0002883']
                                      })

        clinical_data = pd.DataFrame({'CONCEPT_ID': ['315763', '440965', '138117', '999999'],
                                      'CODE': ['C0000005', 'C0000039', 'C5234707', 'C9999999'],
                                      'CODE_COLUMN': ['UMLS_CUI', 'UMLS_CUI', 'UMLS_CUI', 'UMLS_CUI']
                                      })

        umls_cui_data = pd.DataFrame({'CUI': ['C0000005', 'C0000039', 'C5234707'],
                                      'SAB': ['HPO', 'HPO', 'HPO'],
                                      'CODE': ['hp:0001901', 'hp:0011737', 'hp:0002883']
                                      })

        # run method and test output
        merged_data = ohdsi_ananke('CONCEPT_ID', ['hp'], combo_dict_df, clinical_data, umls_cui_data)
        self.assertIsInstance(merged_data, pd.DataFrame)
        self.assertTrue(len(merged_data) == 3)
        self.assertTrue(list(merged_data.columns) == ['CONCEPT_ID', 'CODE', 'CODE_COLUMN', 'CONCEPT_DBXREF_ONT_URI'])

        return None

    def tests_normalizes_clinical_source_codes(self):
        """Tests the normalizes_clinical_source_codes method."""

        # set input arguments
        dbxref_dict = {'umls:c0008733': 'DbXref', 'snomedct_us:462165005': 'DbXref'}
        source_dict = {'snomedct_us': 'snomed'}

        # test method
        results = normalizes_clinical_source_codes(dbxref_dict, source_dict)
        self.assertIsInstance(results, Dict)
        self.assertEqual(len(results), 2)

        return None

    def tests_filters_mapping_content_scenario1(self):
        """Tests the filters_mapping_content method - scenario 1."""

        # create input values
        # test set 1
        input_1_exact = [['HP_0008181', 'HP_0008181'], ['abetalipoproteinemia', 'abetalipoproteinemia'],
                         ['CONCEPT_DBXREF_snomed:190787008', 'CONCEPT_SOURCE_LABEL:abetalipoproteinemia']]
        input_1_sim = [['HP_0008181'], ['abetalipoproteinemia'], ['HP_0008181_1.0']]

        # test method -- input set 1
        results_1 = filters_mapping_content(input_1_exact, input_1_sim, 0.25)
        self.assertIsInstance(results_1[0], list)
        self.assertEqual(len(results_1[0]), 3)
        self.assertIsInstance(results_1[1], list)
        self.assertEqual(len(results_1[1]), 3)
        self.assertEqual(results_1[0], [['HP_0008181'], ['abetalipoproteinemia'],
                                        'CONCEPT_DBXREF_snomed:190787008 | CONCEPT_SOURCE_LABEL:abetalipoproteinemia'])
        self.assertEqual(results_1[1], [['HP_0008181'], ['abetalipoproteinemia'], 'HP_0008181_1.0'])

        return None

    def tests_filters_mapping_content_scenario2(self):
        """Tests the filters_mapping_content method - scenario 2."""

        # create input values
        # test set 2
        input_2_exact = [['HP_0011276', 'HP_0000951'], ['vascular skin abnormality', 'abnormality of the skin'],
                         ['ANCESTOR_DBXREF_snomed:11263005 | ANCESTOR_DBXREF_msh:d012871']]
        input_2_sim = [['HP_0100309', 'HP_0100310'], ['subdural hemorrhage', 'epidural hemorrhage'],
                       ['HP_0100309_0.75 | HP_0100310_0.786']]

        # test method -- input set 2
        results_2 = filters_mapping_content(input_2_exact, input_2_sim, 0.25)
        self.assertIsInstance(results_2[0], list)
        self.assertEqual(len(results_2[0]), 3)
        self.assertIsInstance(results_2[1], list)
        self.assertEqual(len(results_2[1]), 3)
        self.assertEqual(results_2[0], [['HP_0011276', 'HP_0000951'],
                                        ['vascular skin abnormality', 'abnormality of the skin'],
                                        'ANCESTOR_DBXREF_snomed:11263005 | ANCESTOR_DBXREF_msh:d012871'])
        self.assertEqual(results_2[1], [['HP_0100309', 'HP_0100310'], ['subdural hemorrhage', 'epidural hemorrhage'],
                                        'HP_0100309_0.75 | HP_0100310_0.786'])

        return None

    def tests_filters_mapping_content_scenario2_threshold(self):
        """Tests the filters_mapping_content method - scenario 2 with high thresholding."""

        # create input values
        # test set 2
        input_2a_exact = [['HP_0011276', 'HP_0000951'], ['vascular skin abnormality', 'abnormality of the skin'],
                          ['ANCESTOR_DBXREF_snomed:11263005 | ANCESTOR_DBXREF_msh:d012871']]
        input_2a_sim = [['HP_0100309', 'HP_0100310'], ['subdural hemorrhage', 'epidural hemorrhage'],
                        ['HP_0100309_0.75 | HP_0100310_0.786']]

        # test method -- input set 2
        results_2a = filters_mapping_content(input_2a_exact, input_2a_sim, 0.76)
        self.assertIsInstance(results_2a[0], list)
        self.assertEqual(len(results_2a[0]), 3)
        self.assertIsInstance(results_2a[1], list)
        self.assertEqual(len(results_2a[1]), 3)
        self.assertEqual(results_2a[0], [['HP_0011276', 'HP_0000951'],
                                         ['vascular skin abnormality', 'abnormality of the skin'],
                                         'ANCESTOR_DBXREF_snomed:11263005 | ANCESTOR_DBXREF_msh:d012871'])
        self.assertEqual(results_2a[1], [['HP_0100310'], ['epidural hemorrhage'], 'HP_0100310_0.786'])

        return None

    def tests_filters_mapping_content_scenario3(self):
        """Tests the filters_mapping_content method - scenario 3."""

        # create input values
        # test set 3
        input_3_exact = [['HP_0011276', 'HP_0000951'], ['vascular skin abnormality', 'abnormality of the skin'],
                         ['CONCEPT_DBXREF_snomed:11263005 | CONCEPT_DBXREF_msh:d012871']]
        input_3_sim = [['HP_0100309', 'HP_0100310'], ['subdural hemorrhage', 'epidural hemorrhage'],
                       ['HP_0100309_0.278 | HP_0100310_0.266']]

        # test method -- input set 3
        results_3 = filters_mapping_content(input_3_exact, input_3_sim, 0.25)
        self.assertIsInstance(results_3[0], list)
        self.assertEqual(len(results_3[0]), 3)
        self.assertIsInstance(results_3[1], list)
        self.assertEqual(len(results_3[1]), 3)
        self.assertEqual(results_3[0], [['HP_0011276', 'HP_0000951'],
                                        ['vascular skin abnormality', 'abnormality of the skin'],
                                        'CONCEPT_DBXREF_snomed:11263005 | CONCEPT_DBXREF_msh:d012871'])
        self.assertEqual(results_3[1], [['HP_0100309', 'HP_0100310'], ['subdural hemorrhage', 'epidural hemorrhage'],
                                        'HP_0100309_0.278 | HP_0100310_0.266'])

        return None

    def tests_filters_mapping_content_scenario4(self):
        """Tests the filters_mapping_content method - scenario 4."""

        # create input values
        # test set 4
        input_4_exact = [['HP_0011276', 'HP_0000951'], ['vascular skin abnormality', 'abnormality of the skin'],
                         ['ANCESTOR_DBXREF_snomed:11263005 | ANCESTOR_DBXREF_msh:d012871']]
        input_4_sim = [['HP_0100309', 'HP_0100310'], ['subdural hemorrhage', 'epidural hemorrhage'],
                       ['HP_0100309_0.278 | HP_0100310_0.266']]

        # test method -- input set 4
        results_4 = filters_mapping_content(input_4_exact, input_4_sim, 0.25)
        self.assertIsInstance(results_4[0], list)
        self.assertEqual(len(results_4[0]), 3)
        self.assertIsInstance(results_4[1], list)
        self.assertEqual(len(results_4[1]), 3)
        self.assertEqual(results_4[0], [['HP_0011276', 'HP_0000951'],
                                        ['vascular skin abnormality', 'abnormality of the skin'],
                                        'ANCESTOR_DBXREF_snomed:11263005 | ANCESTOR_DBXREF_msh:d012871'])
        self.assertEqual(results_4[1], [['HP_0100309', 'HP_0100310'], ['subdural hemorrhage', 'epidural hemorrhage'],
                                        'HP_0100309_0.278 | HP_0100310_0.266'])

        return None

    def tests_filters_mapping_content_scenario5(self):
        """Tests the filters_mapping_content method - scenario 5."""

        # create input values
        # test set 5
        input_5_exact = [['HP_0002011', 'HP_0002960', 'HP_0011096'],
                         ['morphological central nervous system abnormality', 'peripheral demyelination'],
                         ['ANCESTOR_DBXREF_snomed:23853001 | ANCESTOR_DBXREF_snomed:85828009',
                          'ANCESTOR_LABEL:demyelination']]
        input_5_sim = [[], [], []]

        # test method -- input set 5
        results_5 = filters_mapping_content(input_5_exact, input_5_sim, 0.25)
        self.assertIsInstance(results_5[0], list)
        self.assertEqual(len(results_5[0]), 3)
        self.assertIsInstance(results_5[1], list)
        self.assertEqual(len(results_5[1]), 3)
        self.assertEqual(results_5[0], [['HP_0002011', 'HP_0002960', 'HP_0011096'],
                                        ['morphological central nervous system abnormality',
                                         'peripheral demyelination'],
                                        'ANCESTOR_DBXREF_snomed:23853001 | ANCESTOR_DBXREF_snomed:85828009 | '
                                        'ANCESTOR_LABEL:demyelination'])
        self.assertEqual(results_5[1], [None, None, None])

        return None

    def tests_compiles_mapping_content_1(self):
        """Tests the compiles_mapping_content method - round 1."""

        # create required input resources
        data_row_1 = pd.Series({'CONCEPT_ID': '4098595',
                                'CONCEPT_DBXREF_HP_URI': 'http://purl.obolibrary.org/obo/HP_0008181',
                                'CONCEPT_DBXREF_HP_LABEL': 'abetalipoproteinemia',
                                'CONCEPT_DBXREF_HP_EVIDENCE': 'CONCEPT_DBXREF_snomed:190787008',
                                'CONCEPT_STR_HP_URI': 'http://purl.obolibrary.org/obo/HP_0008181',
                                'CONCEPT_STR_HP_LABEL': 'abetalipoproteinemia',
                                'CONCEPT_STR_HP_EVIDENCE': 'CONCEPT_SOURCE_LABEL:abetalipoproteinemia',
                                'HP_SIM_ONT_URI': 'HP_0008181',
                                'HP_SIM_ONT_LABEL': 'abetalipoproteinemia',
                                'HP_SIM_ONT_EVIDENCE': 'HP_0008181_1.0'})
        data_row_2 = pd.Series({'CONCEPT_ID': '4098595', 'CONCEPT_DBXREF_HP_URI': '', 'CONCEPT_DBXREF_HP_LABEL': '',
                                'CONCEPT_DBXREF_HP_EVIDENCE': '', 'CONCEPT_STR_HP_URI': '', 'CONCEPT_STR_HP_LABEL': '',
                                'CONCEPT_STR_HP_EVIDENCE': '', 'HP_SIM_ONT_URI': '', 'HP_SIM_ONT_LABEL': '',
                                'HP_SIM_ONT_EVIDENCE': ''})

        # test method
        results = compiles_mapping_content(data_row_1, 'HP', 0.75)
        self.assertIsInstance(results[0], list)
        self.assertIsInstance(results[1], list)
        self.assertEqual(len(results[0]), 3)
        self.assertEqual(len(results[1]), 3)
        self.assertIsInstance(results[0][0], list)
        self.assertIsInstance(results[0][1], list)
        self.assertIsInstance(results[0][2], str)

        results = compiles_mapping_content(data_row_2, 'HP', 0.75)
        self.assertIsInstance(results[0], list)
        self.assertIsInstance(results[1], list)
        self.assertEqual(len(results[0]), 3)
        self.assertEqual(len(results[1]), 3)
        self.assertEqual(results[0][0], None)
        self.assertEqual(results[0][1], None)
        self.assertEqual(results[0][2], None)

        return None

    def tests_compiles_mapping_content_2(self):
        """Tests the compiles_mapping_content method - round 2."""

        # create required input resources
        data_row_1 = pd.Series({'CONCEPT_ID': '4134318',
                                'CONCEPT_DBXREF_HP_URI': '',
                                'CONCEPT_DBXREF_HP_LABEL': '',
                                'CONCEPT_DBXREF_HP_EVIDENCE': '',
                                'CONCEPT_STR_HP_URI': 'http://purl.obolibrary.org/obo/HP_0041249',
                                'CONCEPT_STR_HP_LABEL': 'fractured nose',
                                'CONCEPT_STR_HP_EVIDENCE': 'CONCEPT_SYNONYM:fractured_nose',
                                'HP_SIM_ONT_URI': 'HP_0041249 | HP_0010939 | HP_0004646 | HP_0010941 | HP_0041162 | '
                                                  'HP_0041248',
                                'HP_SIM_ONT_LABEL': 'fractured nose | abnormality of the nasal bone | hypoplasia of '
                                                    'the nasal bone | aplasia of the nasal bone | fractured foot bone '
                                                    '| fractured carpal bone',
                                'HP_SIM_ONT_EVIDENCE': 'HP_0041249_1.0 | HP_0010939_0.379 | HP_0004646_0.352 | '
                                                       'HP_0010941_0.352 | HP_0041162_0.31 | HP_0041248_0.303'})

        # test method
        results = compiles_mapping_content(data_row_1, 'HP', 0.75)
        self.assertIsInstance(results[0], list)
        self.assertIsInstance(results[1], list)
        self.assertEqual(len(results[0]), 3)
        self.assertEqual(len(results[1]), 3)
        self.assertEqual(results[0][2], 'CONCEPT_SYNONYM:fractured_nose')
        self.assertEqual(results[1][2], 'HP_0041249_1.0')

        return None

    def tests_formats_mapping_evidence(self):
        """Tests the formats_mapping_evidence method."""

        # prepare needed input data
        ont_dict = {'label': {'abetalipoproteinemia': 'http://purl.obolibrary.org/obo/HP_0008181'},
                    'dbxref': {'snomedct_us:190787008': 'http://purl.obolibrary.org/obo/HP_0008181'},
                    'dbxref_type': {'snomedct_us:190787008': 'DbXref'},
                    'synonym': {'wet lung': 'http://purl.obolibrary.org/obo/HP_0100598'},
                    'synonym_type': {'wet lung': 'hasExactSynonym'}}
        source_dict = {'snomed:190787008': 'DbXref*snomedct_us'}
        result = ([['HP_0008181'], ['abetalipoproteinemia'],
                   'CONCEPT_DBXREF_snomed:190787008 | CONCEPT_DBXREF_umls:C0000744 | '
                   'CONCEPT_SOURCE_LABEL:abetalipoproteinemia | CONCEPT_SYNONYM:abetalipoproteinemia'],
                  [['HP_0008181'], ['abetalipoproteinemia'], 'HP_0008181_1.0'])
        clin_data = {'CONCEPT_LABEL': 'Abetalipoproteinemia',
                     'CONCEPT_SOURCE_LABEL': 'Abetalipoproteinemia',
                     'CONCEPT_SYNONYM': 'Abetalipoproteinaemia | Apolipoprotein B deficiency',
                     'ANCESTOR_LABEL': 'Autosomal recessive hereditary disorder | Metabolic disorder | Finding'}

        # test method
        results = formats_mapping_evidence(ont_dict, source_dict, result, clin_data)
        self.assertIsInstance(results, Tuple)
        self.assertEqual(results[0], 'OBO_DbXref-OMOP_CONCEPT_CODE:snomed_190787008 | '
                                     'OBO_DbXref-OMOP_CONCEPT_CODE:umls_C0000744 | '
                                     'OBO_LABEL-OMOP_CONCEPT_LABEL:abetalipoproteinemia')
        self.assertEqual(results[1], 'CONCEPT_SIMILARITY:HP_0008181_1.0')

        return None

    def tests_assigns_mapping_category_exact(self):
        """Tests the assigns_mapping_category method when evidence is exact."""

        # set function input 1
        mapping_info_1 = [['HP_0008181'], ['abetalipoproteinemia'],
                          'CONCEPT_DBXREF_snomed:190787008 | CONCEPT_DBXREF_umls:C0000744 | '
                          'CONCEPT_SOURCE_LABEL:abetalipoproteinemia | CONCEPT_SYNONYM:abetalipoproteinemia']
        mapping_evidence_1 = 'OBO_DbXref-OMOP_CONCEPT_CODE:snomedct_us_190787008 | ' \
                             'OBO_DbXref-OMOP_CONCEPT_CODE:umls_C0000744 | ' \
                             'OBO_LABEL-OMOP_CONCEPT_LABEL:abetalipoproteinemia | ' \
                             'OBO_LABEL-OMOP_CONCEPT_SYNONYM:abetalipoproteinemia '

        # set function inputs
        mapping_info_2 = [['HP_0008181'], ['abetalipoproteinemia'], 'HP_0008181_1.0']
        mapping_evidence_2 = 'CONCEPT_SIMILARITY:HP_0008181_1.0'

        # test method - exact
        results_1 = assigns_mapping_category(mapping_info_1, mapping_evidence_1)
        self.assertIsInstance(results_1, str)
        self.assertEqual(results_1, 'Automatic Exact - Concept')

        # test method - similarity
        results_2 = assigns_mapping_category(mapping_info_2, mapping_evidence_2)
        self.assertIsInstance(results_2, str)
        self.assertEqual(results_2, 'Manual Exact - Concept Similarity')

        return None

    def tests_assigns_mapping_category_similarity(self):
        """Tests the assigns_mapping_category method when evidence is from concept similarity."""

        # set function inputs
        mapping_info_2 = [['HP_0008181'], ['abetalipoproteinemia'], 'HP_0008181_1.0']
        mapping_evidence_2 = 'CONCEPT_SIMILARITY:HP_0008181_1.0'

        # test method - similarity
        results_2 = assigns_mapping_category(mapping_info_2, mapping_evidence_2)
        self.assertIsInstance(results_2, str)
        self.assertEqual(results_2, 'Manual Exact - Concept Similarity')

        return None

    def tests_aggregates_mapping_results_full_SimResults(self):
        """Tests the aggregates_mapping_results method when there is similarity data."""

        # set-up inputs
        data1 = pd.DataFrame({'CONCEPT_ID': ['4098595'],
                              'CONCEPT_LABEL': ['Abetalipoproteinemia'],
                              'CONCEPT_SOURCE_LABEL': ['Abetalipoproteinemia'],
                              'CONCEPT_SYNONYM': ['Abetalipoproteinaemia | ABL - Abetalipoproteinaemia | '
                                                  'Abetalipoproteinemia (disorder) | Apolipoprotein B deficiency | '
                                                  'Abetalipoproteinemia | ABL - Abetalipoproteinemia'],
                              'CONCEPT_DBXREF_HP_URI': ['http://purl.obolibrary.org/obo/HP_0008181'],
                              'CONCEPT_DBXREF_HP_LABEL': ['abetalipoproteinemia'],
                              'CONCEPT_DBXREF_HP_EVIDENCE': ['CONCEPT_DBXREF_snomed:190787008'],
                              'CONCEPT_STR_HP_URI': ['http://purl.obolibrary.org/obo/HP_0008181'],
                              'CONCEPT_STR_HP_LABEL': ['abetalipoproteinemia'],
                              'CONCEPT_STR_HP_EVIDENCE': ['CONCEPT_SOURCE_LABEL:abetalipoproteinemia'],
                              'HP_SIM_ONT_URI': ['HP_0008181'],
                              'HP_SIM_ONT_LABEL': ['abetalipoproteinemia'],
                              'HP_SIM_ONT_EVIDENCE': ['HP_0008181_1.0']})

        # test method when there is similarity data
        results = aggregates_mapping_results(data1, ['hp'], self.ont_data, self.source_codes, 0.25)
        self.assertIsInstance(results, pd.DataFrame)
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results.columns), 21)
        # check annotated values
        self.assertEqual(results.at[0, 'AGGREGATED_HP_URI'], 'HP_0008181')
        self.assertEqual(results.at[0, 'AGGREGATED_HP_LABEL'], 'abetalipoproteinemia')
        self.assertEqual(results.at[0, 'AGGREGATED_HP_MAPPING'], 'Automatic Exact - Concept')
        self.assertEqual(results.at[0, 'AGGREGATED_HP_EVIDENCE'], 'OBO_DbXref-OMOP_CONCEPT_CODE:snomed_190787008 | '
                                                                  'OBO_LABEL-OMOP_CONCEPT_LABEL:abetalipoproteinemia')
        self.assertEqual(results.at[0, 'SIMILARITY_HP_URI'], 'HP_0008181')
        self.assertEqual(results.at[0, 'SIMILARITY_HP_LABEL'], 'abetalipoproteinemia')
        self.assertEqual(results.at[0, 'SIMILARITY_HP_MAPPING'], 'Manual Exact - Concept Similarity')
        self.assertEqual(results.at[0, 'SIMILARITY_HP_EVIDENCE'], 'CONCEPT_SIMILARITY:HP_0008181_1.0')

        return None

    def tests_aggregates_mapping_results_full_NoSimResults(self):
        """Tests the aggregates_mapping_results method when there is similarity data - no similarity data."""

        # set-up inputs
        data2 = pd.DataFrame({'CONCEPT_ID': ['4098595'],
                              'CONCEPT_LABEL': ['Abetalipoproteinemia'],
                              'CONCEPT_SOURCE_LABEL': ['Abetalipoproteinemia'],
                              'CONCEPT_SYNONYM': ['Abetalipoproteinaemia | ABL - Abetalipoproteinaemia | '
                                                  'Abetalipoproteinemia (disorder) | Apolipoprotein B deficiency | '
                                                  'Abetalipoproteinemia | ABL - Abetalipoproteinemia'],
                              'CONCEPT_DBXREF_HP_URI': ['http://purl.obolibrary.org/obo/HP_0008181'],
                              'CONCEPT_DBXREF_HP_LABEL': ['abetalipoproteinemia'],
                              'CONCEPT_DBXREF_HP_EVIDENCE': ['CONCEPT_DBXREF_snomed:190787008'],
                              'CONCEPT_STR_HP_URI': ['http://purl.obolibrary.org/obo/HP_0008181'],
                              'CONCEPT_STR_HP_LABEL': ['abetalipoproteinemia'],
                              'CONCEPT_STR_HP_EVIDENCE': ['CONCEPT_SOURCE_LABEL:abetalipoproteinemia']})

        # test method when there is no similarity data
        results = aggregates_mapping_results(data2, ['hp'], self.ont_data, self.source_codes, 0.25)
        self.assertIsInstance(results, pd.DataFrame)
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results.columns), 18)
        # check annotated values
        self.assertEqual(results.at[0, 'AGGREGATED_HP_URI'], 'HP_0008181')
        self.assertEqual(results.at[0, 'AGGREGATED_HP_LABEL'], 'abetalipoproteinemia')
        self.assertEqual(results.at[0, 'AGGREGATED_HP_MAPPING'], 'Automatic Exact - Concept')
        self.assertEqual(results.at[0, 'AGGREGATED_HP_EVIDENCE'], 'OBO_DbXref-OMOP_CONCEPT_CODE:snomed_190787008 | '
                                                                  'OBO_LABEL-OMOP_CONCEPT_LABEL:abetalipoproteinemia')
        self.assertEqual(results.at[0, 'SIMILARITY_HP_URI'], None)
        self.assertEqual(results.at[0, 'SIMILARITY_HP_LABEL'], None)
        self.assertEqual(results.at[0, 'SIMILARITY_HP_MAPPING'], None)
        self.assertEqual(results.at[0, 'SIMILARITY_HP_EVIDENCE'], None)

        return None
