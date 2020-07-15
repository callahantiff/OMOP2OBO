#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import nltk
import numpy as np
import pickle
import warnings

from sklearn.feature_extraction.text import TfidfVectorizer
from typing import Dict, List, Tuple
from unittest import TestCase

from omop2obo.string_similarity import SimilarStringFinder

# download stopwords data from NLTK
nltk.download('wordnet')


class TestSimilarStringFinder(TestCase):
    """Class to test functions used when performing string similarity."""

    def setUp(self):

        # disable warning
        warnings.filterwarnings('ignore')

        # set-up filename
        dir_loc = os.path.join(os.path.dirname(__file__), 'data')
        self.dir_loc = os.path.abspath(dir_loc)
        self.clinical_directory = self.dir_loc + '/clinical_data'
        self.mapping_directory = self.dir_loc + '/mappings'

        # create some fake ontology data
        with open(self.dir_loc + '/condition_occurrence_ontology_dictionary.pickle', 'rb') as handle:
            self.ont_dict = pickle.load(handle)
        handle.close()

        # link to fake clinical data
        self.clinical_file = self.clinical_directory + '/sample_omop_condition_occurrence_data.csv'

        # add clinical_data file input parameters
        self.primary_key = 'CONCEPT_ID'
        self.concept_strings = ['CONCEPT_LABEL', 'CONCEPT_SYNONYM']

        # read in corpus
        with open(self.dir_loc + '/clinical_data_corpus.pickle', 'rb') as f:
            self.corpus = pickle.load(f)

        # initialize the class
        self.similarity_finder = SimilarStringFinder(self.clinical_file, self.ont_dict, self.primary_key,
                                                     self.concept_strings)

        return None

    def test_initialization_clinical_file(self):
        """Test class initialization for clinical data input argument."""

        # test if file is not type string
        clinical_file_type = 1234
        self.assertRaises(TypeError, SimilarStringFinder, clinical_file_type, self.ont_dict, self.primary_key,
                          self.concept_strings)

        # test if file exists
        clinical_file_exists = self.clinical_directory + '/sample_omop_condition_occurrence.csv'
        self.assertRaises(OSError, SimilarStringFinder, clinical_file_exists, self.ont_dict, self.primary_key,
                          self.concept_strings)

        # test if file is empty
        clinical_file_empty = self.clinical_directory + '/sample_omop_condition_occurrence_data_empty.csv'
        self.assertRaises(TypeError, SimilarStringFinder, clinical_file_empty, self.ont_dict, self.primary_key,
                          self.concept_strings)

        return None

    def test_initialization_ontology_dict(self):
        """Test class initialization for ontologies dictionary input argument."""

        # check if ontology_dict is not type dict
        self.assertRaises(TypeError, SimilarStringFinder, self.clinical_file, 12, self.primary_key,
                          self.concept_strings)

        return None

    def test_initialization_primary_key(self):
        """Test the primary_key input parameter."""

        # check if primary_key is not a string
        self.assertRaises(TypeError, SimilarStringFinder, self.clinical_file, self.ont_dict, 123456,
                          self.concept_strings)

        return None

    def test_initialization_concept_strings(self):
        """Test the concept_string input parameter."""

        # check if clinical_strings are a list
        self.assertRaises(TypeError, SimilarStringFinder, self.clinical_file, self.ont_dict, self.primary_key, 'labels')

        return None

    def test_text_preprocessor(self):
        """Test the text_preprocessor method."""

        processed_text = self.similarity_finder.text_preprocessor(self.similarity_finder.clinical_data,
                                                                  self.primary_key)

        # check output
        self.assertIsInstance(processed_text, List)
        self.assertTrue(len(processed_text) == 5)
        self.assertIsInstance(processed_text[0], Tuple)

        return None

    def test_corpus_modifier(self):
        """Test the corpus_modifier method."""

        # test method
        results = self.similarity_finder.corpus_modifier(self.corpus, ['HP', 'ONT'])

        # check output
        self.assertIsInstance(results, Tuple)
        self.assertEqual(len(results), 2)

        # check the first dict
        dict1 = results[0]
        self.assertIsInstance(dict1, Dict)
        self.assertEqual(len(dict1), 15060)

        # check the second dict
        dict2 = results[1]
        self.assertIsInstance(dict2, Dict)
        self.assertEqual(len(dict2), 162974)

        return

    def test_filters_matches(self):
        """Test the filters_matches method."""

        # set-up the method
        matches = [[0.32094866776185677, 'MONDO_0023757'], [0.2376527813301072, 'MONDO_0023757'],
                   [0.32094866776185677, 'MONDO_0023757'], [0.24449752310188258, 'MONDO_0007975'],
                   [0.24449752310188258, 'MONDO_0007975'], [0.2110089826112492, 'MONDO_0023757']]

        # test the method
        results = self.similarity_finder.filters_matches(matches, 70)

        # check the output
        self.assertIsInstance(results, List)
        self.assertEqual(len(results), 1)

        return None

    def test_similarity_search(self):
        """Test the similarity_search method."""

        # set-up method
        tf = TfidfVectorizer(tokenizer=lambda x: x, preprocessor=lambda x: x, use_idf=True, norm='l2', lowercase=False)
        self.similarity_finder.matrix = tf.fit_transform([x[1] for x in self.corpus])
        onts = ['HP', 'MONDO']
        corpus_idx = self.similarity_finder.corpus_modifier(self.corpus, onts)[1]
        sub_idx = [i for j in [v for k, v in corpus_idx.items() if any(k.startswith(x) for x in onts)] for i in j]
        ont_matrix = self.similarity_finder.matrix.tocsr()[np.array(sub_idx), :]

        # test method
        results = self.similarity_finder.similarity_search(ont_matrix, 8, 10)

        # check output
        self.assertIsInstance(results, List)
        self.assertEqual(len(results), 10)
        self.assertIsInstance(results[0], Tuple)

        return None

    def test_scores_tfidf(self):
        """Test the scores_tfidf method."""

        # set-up method
        tf = TfidfVectorizer(tokenizer=lambda x: x, preprocessor=lambda x: x, use_idf=True, norm='l2', lowercase=False)
        self.similarity_finder.matrix = tf.fit_transform([x[1] for x in self.corpus])
        ontology_type = ['HP', 'MONDO']

        # run method
        results = self.similarity_finder.scores_tfidf(self.corpus, ontology_type, 10, 80)

        # test output
        self.assertTrue(len(results) == 5)
        self.assertTrue(len(results.columns) == 7)
        self.assertEqual(list(results.columns), ['CONCEPT_ID', 'HP_SIM_ONT_URI', 'HP_SIM_ONT_LABEL',
                                                 'HP_SIM_ONT_EVIDENCE', 'MONDO_SIM_ONT_URI', 'MONDO_SIM_ONT_LABEL',
                                                 'MONDO_SIM_ONT_EVIDENCE'])

        return None

    def test_performs_similarity_search(self):
        """Test the performs_similarity_search method."""

        # run method
        results = self.similarity_finder.performs_similarity_search()

        # test output
        self.assertTrue(len(results) == 5)
        self.assertTrue(len(results.columns) == 17)
        self.assertEqual(list(results.columns), ['CONCEPT_ID', 'CONCEPT_SOURCE_CODE', 'CONCEPT_LABEL', 'CONCEPT_VOCAB',
                                                 'CONCEPT_VOCAB_VERSION', 'CONCEPT_SYNONYM', 'ANCESTOR_CONCEPT_ID',
                                                 'ANCESTOR_SOURCE_CODE', 'ANCESTOR_LABEL', 'ANCESTOR_VOCAB',
                                                 'ANCESTOR_VOCAB_VERSION', 'HP_SIM_ONT_URI', 'HP_SIM_ONT_LABEL',
                                                 'HP_SIM_ONT_EVIDENCE', 'MONDO_SIM_ONT_URI', 'MONDO_SIM_ONT_LABEL',
                                                 'MONDO_SIM_ONT_EVIDENCE'])

        return None
