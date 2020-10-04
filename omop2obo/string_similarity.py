#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import hashlib
import os
import numpy as np  # type: ignore
import pandas as pd  # type: ignore
import re

from functools import reduce
# from nltk.corpus import stopwords  # type: ignore
from nltk.stem import WordNetLemmatizer  # type: ignore
from nltk.tokenize import RegexpTokenizer  # type: ignore
from pandas import errors
from scipy import sparse  # type: ignore
from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
from sklearn.metrics.pairwise import linear_kernel  # type: ignore
from tqdm import tqdm  # type: ignore
from typing import Dict, List, Optional, Tuple

from omop2obo.utils import column_splitter, data_frame_subsetter, merge_dictionaries

# load stopwords into environment -- horrible workaround until Travis is fixed
# nltk.download('wordnet')
stopwords = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd",
             'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers',
             'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what',
             'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were',
             'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the',
             'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about',
             'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from',
             'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here',
             'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
             'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can',
             'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain',
             'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn',
             "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn',
             "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't",
             'wouldn', "wouldn't"]


class SimilarStringFinder(object):
    """This class is designed to facilitate the mapping of clinical concepts from the Observational Medical Outcomes
    Partnership to Open Biomedical Ontology concepts. To suggest labels, we leverage clinical labels and synonyms as
    well as ontological labels, synonyms, and definitions. These items are preprocessed and then converted into a
    TF-IDF matrix, which is used to help us calculate Cosine similarity between all clinical concepts and ontology
    classes. When aligning, the user is able to pass a percentile threshold to reduce the potential list of potential
    matches and thus we return the n most similar annotations for each clinical concept. To ensure that these
    annotations are useful, we also return the similarity score for each match.

    Attributes:
        clinical_data: A Pandas DataFrame containing clinical data.
        ontology_dictionary: A nested dictionary containing ontology data, where outer keys are ontology identifiers
            (e.g. "hp", "mondo"), inner keys are data types (e.g. "label", "definition", "dbxref", and "synonyms").
            For each inner key, there is a third dictionary keyed by a string of that item type and with values that
            are the ontology URI for that string type.
        primary_key: A string containing the column name of the primary key.
        concept_strings: A list of column names containing concept-level labels and synonyms (optional).
        matrix: A Scipy sparse matrix containing the TF-IDF results for all clinical data (i.e. labels and synonyms)
            and ontology data (i.e. labels, definitions, and synonyms).

    Raises:
        TypeError:
            If clinical_file is not type str or if clinical_file is empty.
            If ontology_dictionary is not type dict.
            if primary_key is not type str.
            if concept_strings and ancestor_strings (if provided) are not type list.
        OSError:
            If the clinical_file does not exist.
    """

    def __init__(self, clinical_file: str, ontology_dictionary: Dict, primary_key: str, concept_strings: Tuple) -> None:

        self.matrix: sparse.csr_matrix = sparse.csr_matrix(0, dtype=np.int8)

        # clinical_file
        if not isinstance(clinical_file, str):
            raise TypeError('clinical_file must be type str.')
        elif not os.path.exists(clinical_file):
            raise OSError('The {} file does not exist!'.format(clinical_file))
        elif os.stat(clinical_file).st_size == 0:
            raise TypeError('Input file: {} is empty'.format(clinical_file))
        else:
            print('Loading Clinical Data')
            try:
                self.clinical_data: pd.DataFrame = pd.read_csv(clinical_file, header=0, low_memory=False).astype(str)
            except pd.errors.ParserError:
                self.clinical_data = pd.read_csv(clinical_file, header=0, sep='\t', low_memory=False).astype(str)

            self.clinical_data.fillna('', inplace=True)
            self.clinical_data = self.clinical_data.replace('nan', '')

        # check primary key
        if not isinstance(primary_key, str): raise TypeError('primary_key must be type str.')
        else: self.primary_key: str = primary_key

        # check concept-level string input (optional)
        if concept_strings is None:
            self.concept_strings: Optional[List] = concept_strings
        else:
            if not isinstance(concept_strings, Tuple):  # type: ignore
                raise TypeError('concept_strings must be type tuple.')
            else:
                self.concept_strings = list(concept_strings)

        # check ontology_dictionary
        if not isinstance(ontology_dictionary, Dict):
            raise TypeError('ontology_dictionary must be type dict.')
        else:
            self.ont_dict: Dict = ontology_dictionary

    @staticmethod
    def text_preprocessor(data: pd.DataFrame, primary_key: str) -> List:
        """Takes a Pandas DataFrame as input and performs several text preprocessing steps on one of the input columns.

        Args:
            data: A Pandas DataFrame containing two columns: (1) primary_key and (2) the column containing text to
                perform preprocessing on.
            primary_key: A string containing the name of the column to use as a primary key.

        Returns:
            data_corpus: A list of tuples, where each tuple contains an identifier and a string process.
        """

        col = [x for x in data.columns if x != primary_key][0]  # get text to perform preprocessing on
        # stop_word_patterns = re.compile(r'\b(' + r'|'.join(stopwords.words('english')) + r')\b\s*')
        stop_word_patterns = re.compile(r'\b(' + r'|'.join(stopwords) + r')\b\s*')
        lemmatizer = WordNetLemmatizer()

        # process data
        data['CODE_PROC'] = data[col].apply(lambda x: re.sub(r"\s+", " ", str(x.encode('ascii', 'ignore').decode())))
        data['CODE_PROC'] = data['CODE_PROC'].apply(lambda x: stop_word_patterns.sub('', x).lower())
        data['CODE_PROC'] = data['CODE_PROC'].apply(lambda x: RegexpTokenizer(r"\w+").tokenize(x))
        data['CODE_PROC'] = data['CODE_PROC'].apply(lambda x: [str(lemmatizer.lemmatize(i)) for i in x])

        # split column and update identifier to be primary_key_hash(string)
        hashed_str = data['CODE_PROC'].apply(lambda x: hashlib.md5(bytes(' '.join(x), 'utf-8')).hexdigest())
        data[primary_key] = data[primary_key] + '_' + hashed_str

        # convert to corpus format
        data_corpus = list(map(lambda x, y: (x, y), list(data[primary_key]), list(data['CODE_PROC'])))

        return data_corpus

    @staticmethod
    def corpus_modifier(corpus: List, ont_type: List) -> Tuple:
        """Takes a corpus, represented as a list of tuples and creates two dictionaries from it, which have been
        designed to speed up matrix-based similarity look-up.

        Args:
            corpus: A list of tuples representing a corpus, where the first item in the tuple is an identifier and
                the second item is a list of tokens. For example:
            ont_type: A list of strings specifying the ontology types (e.g. "HP", "MONDO").

        Returns:
            A tuple of dictionaries:
                (1) corpus_idx: keys are identifiers and values are lists of row identifiers.
                (2) corpus_enum: keys are row identifiers and values are indices of the row identifiers in the corpus.
        """

        # convert corpus to dictionary for faster look-up of clinical keys
        corpus_idx: Dict = {}
        for x in corpus:
            key = x[0].split('_')[0] if x[0].split('_')[0] not in ont_type else '_'.join(x[0].split('_')[0:2])
            if key in corpus_idx.keys(): corpus_idx[key].append(x[0])
            else: corpus_idx[key] = [x[0]]

        # create dict with id as key and index as value
        corpus_enum: Dict = {}
        for x, y in enumerate(corpus):
            if y[0] in corpus_enum.keys(): corpus_enum[y[0]].append(x)
            else: corpus_enum[y[0]] = [x]

        return corpus_idx, corpus_enum

    @staticmethod
    def filters_matches(matches: List, threshold: int) -> List:
        """Takes a nested list of matches, which are output from the similarity search and a threshold value and
        returns a modified list, such that only those match scores greater than or equal to the input threshold
        percentile.

        Args:
            matches: A nested list of matches from similarity search (e.g. [[0.518615172821148, 'HP_0012384']...]]).
            threshold: An integer specifying a percentile for deriving a threshold cut-off.

        Returns:
            final_matches: A list of the filtered matches (e.g. [[1.0, 'HP_0012384'], [0.7654, 'HP_00123678']]).
        """

        # filter matches to reduce duplicate results
        filtered_matches: List = []
        for x, y in sorted(matches, reverse=True):
            if not any(i for i in filtered_matches if y in i):
                filtered_matches.append([x, y])

        # derive threshold cut-off to reduce match list
        score_threshold = np.percentile([x[0] for x in filtered_matches], threshold)
        final_matches = [[str(round(x[0], 3)), x[1]] for x in filtered_matches if x[0] >= score_threshold]

        return final_matches

    def similarity_search(self, ontology_matrix: sparse.csr_matrix, var_idx: int, top_n: int) -> List:
        """The function calculates the cosine similarity between the index variables and all other included variables in
        the matrix. The results are sorted and returned as a list of lists, where each list contains a variable
        identifier and the cosine similarity score for the top set of similar variables as indicated by the input
        argument are returned.

        Args:
            ontology_matrix: A sparse Scipy matrix where each row represents a variables and each column represents a
                concept and counts are weighted by TF-IDF. This matrix only contains ontology data.
            var_idx: An integer representing a variable identifier.
            top_n: An integer representing the number of similar variables to return.

        Returns:
            similar_variables: A nested list where each list contains a variable identifier and the cosine similarity
                scores for the top_n set of similar words.
        """

        var_vector = self.matrix[var_idx:var_idx + 1]
        cosine_similarities = linear_kernel(var_vector, ontology_matrix).flatten()
        rel_var_indices = cosine_similarities.argsort()[::-1]
        similar_variables = [(variable, cosine_similarities[variable]) for variable in rel_var_indices][0:top_n]

        return similar_variables

    def scores_tfidf(self, corpus: List, ontology_type: List, top_n: int, threshold: int) -> pd.DataFrame:
        """The function iterates over the corpus and returns the top_n (as specified by user) most similar variables,
        by cosine similarity score, which are filtered to only include the top x% most similar matches.

        Args:
            corpus: A list of lists, where the first item in each list is the identifier and the second item is a list
                containing the processed question definition.
            ontology_type: A list containing ontology types (e.g. ["hp", "mondo"]) to use when filtering results.
            top_n: The number of results to return for each variable.
            threshold: An integer specifying a percentile for deriving a threshold cut-off.

        Returns:
            results: A pandas DataFrame of the top_n (as specified by user) results for each variable, with two new
                columns added per ontology. See example below:

                OUTPUT
                      CONCEPT_ID     HP_SIM_ONT_URI  HP_SIM_ONT_LABEL   MONDO_SIM_ONT_URI   MONDO_SIM_ONT_LABEL
                    0    4311399         HP_0002617        dilatation       MONDO_0001273             megacolon
        """

        onts, ont_uri = ontology_type, 'http://purl.obolibrary.org/obo/'
        ont_labels = merge_dictionaries(self.ont_dict, 'label', reverse=True)
        corpus_id, corpus_idx = self.corpus_modifier(corpus, onts)  # convert corpus to dictionary for faster look-up
        results: Dict = {x: [] for x in onts}

        # create ont-only version of TF-IDF matrix and corpus for faster cosine similarity look-up
        sub_idx = [i for j in [v for k, v in corpus_idx.items() if any(k.startswith(x) for x in onts)] for i in j]
        ont_matrix, ont_corpus = self.matrix.tocsr()[np.array(sub_idx), :], [corpus[x] for x in sub_idx]

        # matching data in filtered file
        for index, row in tqdm(self.clinical_data.iterrows(), total=self.clinical_data.shape[0]):
            match_vars = corpus_id[row[self.primary_key]]
            var_id = set([i for j in [corpus_idx[x] for x in match_vars] for i in j])
            scores = [x for y in [self.similarity_search(ont_matrix, v, top_n) for v in set(var_id)] for x in y]
            match_info = [[x[1], '_'.join(ont_corpus[x[0]][0].split('_')[0:2])] for x in scores if x[1] > 0.25]

            if len(match_info) > 0:  # extract matches by ontology type
                for ont in onts:
                    ont_matches = [x for x in match_info if ont in x[1]]
                    if len(ont_matches) > 0:
                        hits = self.filters_matches(ont_matches, threshold)
                        results[ont].append([row[self.primary_key],
                                             ' | '.join([x[1] for x in hits]),
                                             ' | '.join([ont_labels[ont_uri + x[1]] if ont_uri + x[1] in ont_labels
                                                         else x[1] for x in hits]),
                                             ' | '.join([x[1] + '_' + x[0] for x in hits])])
                    else: continue
            else:
                continue

        # convert results to Pandas DataFrame + merge ontology findings together
        ont_sim = [pd.DataFrame({self.primary_key: [x[0] for x in results[ont]],
                                 ont + '_SIM_ONT_URI': [x[1] for x in results[ont]],
                                 ont + '_SIM_ONT_LABEL': [x[2] for x in results[ont]],
                                 ont + '_SIM_ONT_EVIDENCE': [x[3] for x in results[ont]]})
                   for ont in results.keys()]

        scored = reduce(lambda x, y: pd.merge(x, y, how='outer', on=self.primary_key), ont_sim)

        return scored.drop_duplicates()

    def performs_similarity_search(self):
        """

        Returns:
            complete_mapping: A Pandas DataFrame containing the results of calculating pairwise cosine similarity
                between the input clinical data and the input ontologies and merged back with the original input
                clinical data.
        """

        print('\n#### PERFORMING STRING SIMILARITY SEARCH ####')

        # STEP 1 - Pre-process Clinical and Ontology Data
        print('\n*** Pre-Processing Input Data ...')
        # subset input clinical data set to only include string columns
        print('Clinical Data')
        subset_data = self.clinical_data.copy()[[self.primary_key] + self.concept_strings].drop_duplicates()
        split_strings = column_splitter(subset_data, self.primary_key, self.concept_strings, '|')
        str_stacked = data_frame_subsetter(split_strings[[self.primary_key] + self.concept_strings],
                                           self.primary_key, self.concept_strings)[[self.primary_key, 'CODE']]
        preprocessed_clinical_data = self.text_preprocessor(str_stacked, self.primary_key)

        # convert ont dictionary into dictionary of Pandas DataFrames keyed by ontology type
        ont_data_dict = {}
        for ont in self.ont_dict.keys():
            print('Ontology Data: {}'.format(ont.upper()))
            ont_df = pd.concat([pd.DataFrame(self.ont_dict[ont][str_col].items(), columns=['CODE', 'ONT_URI'])
                                for str_col in ['label', 'definition', 'synonym']])
            ont_df['ONT_URI'] = ont_df['ONT_URI'].apply(lambda x: x.split('/')[-1])
            ont_data_dict[ont] = self.text_preprocessor(ont_df, 'ONT_URI')

        # STEP 2 - CREATE TF-IDF MATRIX
        print('\n*** Building TF-IDF Matrix')
        corpus = preprocessed_clinical_data + [x for y in [v for k, v in ont_data_dict.items()] for x in y]
        tf = TfidfVectorizer(tokenizer=lambda x: x, preprocessor=lambda x: x, use_idf=True, norm='l2', lowercase=False,
                             ngram_range=(1, 3))
        self.matrix = tf.fit_transform([x[1] for x in corpus])

        # STEP 3 - Calculating Cosine Similarity
        print('\n*** Calculating Cosine Similarity')
        keys = self.ont_dict.keys()
        ont_lists = [list(self.ont_dict[x]['label'].values())[0].split('/')[-1].split('_')[0] for x in keys]
        cosine_sim = self.scores_tfidf(corpus, ont_lists, 10, 75)

        # merge results with clinical data
        complete_mapping = pd.merge(self.clinical_data, cosine_sim, how='left', on=self.primary_key)
        complete_mapping.columns = [x.upper() for x in complete_mapping.columns]
        complete_mapping.fillna('', inplace=True)

        return complete_mapping
