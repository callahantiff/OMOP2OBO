#########################
# concept_annotator.py #
########################


import gspread
import hashlib
import pandas as pd
import re as re

from abc import ABCMeta, abstractmethod
from nltk.corpus import stopwords
# nltk.download("wordnet")
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import RegexpTokenizer
import numpy as np
from oauth2client.service_account import ServiceAccountCredentials
from progressbar import ProgressBar, FormatLabel, Percentage, Bar
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from scripts.python.umls_api import *


class Annotator(object):
    """An annotator to map clinical codes to ontology terms.

    Attributes:
        input_file: A list string containing the filepath or url to data.
        data: A place holder for a pandas data frame.

    """

    __metaclass__ = ABCMeta

    def __init__(self, input_file):
        self.input_file = input_file
        self.data = ''

    def read_data(self):
        """Return a pandas data frame from a Google Sheet."""

        cred = ServiceAccountCredentials.from_json_keyfile_name(self.input_file[0], self.input_file[1])
        worksheet = gspread.authorize(cred).open(self.input_file[2])
        self.data = pd.DataFrame(worksheet.worksheet(self.input_file[3]).get_all_records())

        return self.data

    def get_data(self):
        return self.data

    def set_data(self, new_data):
        self.data = new_data

    def umls_mapper(self, col_name):
        """Map terminology codes to UMLS CUIs and retrieve their semantic types.

        Args:
            col_name: A string which holds a column name.

        Returns:
            A pandas data frame.
        """

        widgets = [Percentage(), Bar(), FormatLabel('(elapsed: %(elapsed)s)')]
        pbar = ProgressBar(widgets=widgets, maxval=len(self.data))

        data_umls = pd.DataFrame(index=range(0, len(self.data)),
                                 columns=[str(col_name), str(col_name) + '_CUI', str(col_name) + '_SEM_TYPE'])

        for row, val in pbar(self.data.iterrows()):
            cui_map = []
            tui_map = []
            codes = val[str(col_name)].split('|') if '|' in str(val[str(col_name)]) else [val[str(col_name)]]

            for x in codes:
                res = code_search(x)
                cui = res[0] if len(res) > 0 else None
                cui_map.append(cui)

                if cui != '':
                    for i in [cui]:
                        cui_res = cui_search(i)
                        tui_map.append('|'.join([str(x['name']) for x in cui_res['semanticTypes']]))

            data_umls[str(col_name)][row] = val[str(col_name)]
            data_umls[str(col_name) + '_CUI'][row] = '|'.join(cui_map)
            data_umls[str(col_name) + '_SEM_TYPE'] = '|'.join(tui_map)

        pbar.finish()
        return data_umls

    def data_update(self, data_merge, col_name):
        """Update the instance of data by merging it with another data frame.

        Args:
            data_merge: A pandas data frame
            col_name: A string containing the column name to merge on.

        Returns:
            None.

        Raises:
            ValueError: An error occurred when attempting to merge two pandas data frames because they were different
            lengths.
        """

        if len(data_merge) != len(self.data):
            raise ValueError('Cannot merge data frames of differing lengths')

        self.data = pd.merge(self.data, data_merge, on=col_name)

    def data_pre_process(self, identifier, definition, splitter, gram_size):
        """Using the input two lists, the function assembles an identifier and definition for each question. The definition
        is then preprocessed by making all words lowercase, removing all punctuation, tokenizing by word,
        removing english stop words, and lemmatization (via wordnet). The final step is to generate the n-grams of
        different lengths.

        Args:
            identifier: A list of columns used to assemble question identifier. This function assumes that the list
            contains 2 columns.
            definition: A list of columns used to assemble question definition.
            splitter: A string that specifies the character to split synonyms.
            gram_size: A list of integers specifying different n-gram sizes.

        Returns:
            A list of tuples, where the first item in each list is the identifier and the second item is a list
            containing the processed question definition.

        """

        widgets = [Percentage(), Bar(), FormatLabel("(elapsed: %(elapsed)s)")]
        pbar = ProgressBar(widgets=widgets, maxval=len(self.data))

        # create a list to store
        vocab_list = []

        for index, row in pbar(self.data.iterrows()):

            # create identifier (RowIndex_vocab_code)
            if len(identifier) > 1:
                var = str(index) + '_' + str(row[str(identifier[0])]) + '_' + str(row[str(identifier[1])])

                # create list of labels and synonyms (each synonym treated as an item in a list)
                code_definition = [row[str(definition[0])]] + row[str(definition[1])].split(splitter)
            else:
                var = str(row[str(identifier[0])])
                code_definition = row[str(definition[0])].split(splitter)

            for item in code_definition:
                # lowercase item
                item_lower = item.lower()

                # replace all none alphanumeric characters with spaces
                item_lower_punctuation = re.sub(' +', ' ', re.sub(r'[^a-zA-Z0-9\s]', ' ', item_lower))

                # tokenize & remove punctuation
                item_token = RegexpTokenizer(r'\w+').tokenize(item_lower_punctuation)

                # remove stop words & perform lemmatization
                stop_words = stopwords.words('english')
                item_token_lemma = [str(WordNetLemmatizer().lemmatize(x)) for x in item_token if x not in stop_words]

                # create different n-grams using input list as well as the full original string
                for n in gram_size + [len(item_token_lemma)]:
                    ngrams = zip(*[item_token_lemma[i:] for i in range(n)])
                    ngram_list = [' '.join(ngram) for ngram in ngrams]

                    # add items to vocabulary list
                    res = [tuple([str(var) + '_' + str(n) + '_' + str(re.sub(r'\s', '.', i)), i]) for i in ngram_list]
                    vocab_list += res

        # close progress bar and return vocab list
        pbar.finish()
        return vocab_list

    def similarity_search(self, index_var, top_n):
        """Calculates the cosine similarity between the index variables and all other included variables in
        the matrix. The results are sorted and returned as a list of lists, where each list contains a variable
        identifier and the cosine similarity score for the top set of similar variables as indicated by the input
        argument are returned.

        Args:
            index_var: an integer representing a variable id.
            top_n: an integer representing the number of similar variables to return.

        Returns:
            A list of lists where each list contains a variable identifier and the cosine similarity
            score the top set of similar as indicated by the input argument are returned.
        """

        # calculate similarity
        cosine_similarities = linear_kernel(self.data[index_var:index_var + 1], self.data).flatten()
        rel_var_indices = [i for i in cosine_similarities.argsort()[::-1] if i != index_var]
        similar_variables = [(variable, cosine_similarities[variable]) for variable in rel_var_indices][0:top_n]

        return similar_variables

    def score_variables(self, data, var_col, filter_data, corpus, top_n):
        """Iterates over the corpus and returns the top_n (as specified by user) most similar variables,
        with a score, for each variable as a pandas data frame.

        Args:
            var_col: list of columns used to assemble question identifier.
            data: pandas data frame containing variable information.
            corpus: a list of lists, where the first item in each list is the identifier and the second item is a list
            containing the processed question definition.
            filter_data: a pandas data frame containing variable information used to filter results containing the
            processed question definition.
            top_n: number of results to return for each variable.

        Returns:
            A pandas data frame of the top_n (as specified by user) results for each variable.

        """

        widgets = [Percentage(), Bar(), FormatLabel("(elapsed: %(elapsed)s)")]
        pbar = ProgressBar(widgets=widgets, maxval=len(filter_data))
        sim_res = []
        matches = 0

        # matching data in filtered file
        for num, row in pbar(filter_data.iterrows()):
            print(num,row)
            # get index of filter data in corpus
            matches = []
            scores = []
            # retrieve top_n similar variables
            for i in [x for x in corpus if x[0].split('_')[0] == str(num)]:

                num = 2
                row = data.loc[num]
                i = [x for x in corpus if x[0].split('_')[0] == str(num)][0]
                top_n = 200

                for index, score in similarity_search(tfidf_matrix, corpus.index(i), top_n):
                    if score > 0 and 'http' in corpus[index][0]:
                        print(corpus[index][0].split('_')[2], index, '_'.join(corpus[index][0].split('_')[0:2]),
                              corpus[index][1], score)

                        ngram = corpus[index][0].split('_')[2]
                        ontid = '_'.join(corpus[index][0].split('_')[0:2])
                        ontlabel = ont_labels[ontid]

                        matches.append(tuple([ngram, score, index, ontid, ontlabel]))
                        scores.append(tuple([score, ngram, index, ontid, ontlabel]))

                        matches.sort(reverse=True)
                        scores.sort(reverse=True)
                        matches[0:10]
                        scores[0:10]

            sim_res.append([

                corpus[index]
            ])

        # create pandas data frame
        scored_vars = pd.DataFrame(dict(study1_random_id=[x[0] for x in sim_res],
                                        study1=[x[1] for x in sim_res],
                                        study1_id=[x[2] for x in sim_res],
                                        study1_data_desc=[x[3] for x in sim_res],
                                        study1_var_id=[x[4] for x in sim_res],
                                        study1_var_name=[x[5] for x in sim_res],
                                        study1_concept=[x[6] for x in sim_res],
                                        study2_random_id=[x[7] for x in sim_res],
                                        study2=[x[8] for x in sim_res],
                                        study2_id=[x[9] for x in sim_res],
                                        study2_data_desc=[x[10] for x in sim_res],
                                        study2_var_id=[x[11] for x in sim_res],
                                        study2_var_name=[x[12] for x in sim_res],
                                        score=[x[13] for x in sim_res],
                                        match_id=[x[14] for x in sim_res]))

        pbar.finish()

        # verify that we got all the matches we expected (assumes we matched all vars in filtered data)
        if matches != len(filter_data):
            matched = round(matches / float(len(filter_data)) * 100, 2)
            raise ValueError('ERROR: Only matched {0}% of filtered variables'.format(matched))
        else:
            print("Filtering matched " + str(matches) + " of " + str(len(filter_data)) + " variables")
            return scored_vars


    #
    # def similarity_search(tfidf_matrix, index_var, top_n):
    #     """
    #     The function calculates the cosine similarity between the index variables and all other included variables in
    #     the matrix. The results are sorted and returned as a list of lists, where each list contains a variable
    #     identifier and the cosine similarity score for the top set of similar variables as indicated by the input
    #     argument are returned.
    #
    #     :param tfidf_matrix: where each row represents a variables and each column represents a concept and counts are
    #     weighted by TF-IDF
    #     :param index_var: an integer representing a variable id
    #     :param top_n: an integer representing the number of similar variables to return
    #     :return: a list of lists where each list contains a variable identifier and the cosine similarity
    #         score the top set of similar as indicated by the input argument are returned
    #     """
    #
    #     # calculate similarity
    #     cosine_similarities = linear_kernel(tfidf_matrix[index_var:index_var + 1], tfidf_matrix).flatten()
    #     rel_var_indices = [i for i in cosine_similarities.argsort()[::-1] if i != index_var]
    #     similar_variables = [(variable, cosine_similarities[variable]) for variable in rel_var_indices][0:top_n]
    #
    #     return similar_variables
    #
    # def score_variables(var_col, defn_col, label, data, corpus, tfidf_matrix, top_n):
    #     """
    #     The function iterates over the corpus and returns the top_n (as specified by user) most similar variables,
    #     with a score, for each variable as a pandas data frame.
    #
    #     :param var_col: list of columns used to assemble question identifier
    #     :param data: pandas data frame containing variable information
    #     :param corpus: a list of lists, where the first item in each list is the identifier and the second item is a
    #     list
    #     containing the processed question definition
    #     :param tfidf_matrix: matrix where each row represents a variables and each column represents a concept and
    #     counts
    #     are weighted by TF-IDF
    #     :param top_n: number of results to return for each variable
    #     :return: pandas data frame of the top_n (as specified by user) results for each variable
    #     """
    #     widgets = [Percentage(), Bar(), FormatLabel("(elapsed: %(elapsed)s)")]
    #     pbar = ProgressBar(widgets=widgets, maxval=len(data))
    #     sim_res = []
    #     matches = 0
    #
    #     # matching data in filtered file
    #     for index, row in pbar(data.iterrows()):
    #         var = str(row[str(var_col[0])]) + "|" + str(row[str(var_col[1])])
    #
    #         # get index of filter data in corpus
    #         if "|" in row[defn_col]:
    #             var_idx = [x for x, y in enumerate(corpus) if y[0] == var]
    #             if var_idx:
    #                 for v in var_idx:
    #                     matches += 1
    #                     omop = corpus[v][0].split(str("|"))[0]
    #                     sme = "|".join(corpus[v][0].split(str("|"))[1:])
    #
    #                     # retrieve top_n similar variables
    #                     for idx, score in similarity_search(tfidf_matrix, v, top_n):
    #                         if 'http' in corpus[idx][0] and score > 0:
    #                             sim_res.append([omop, sme, row[label[0]],
    #                                             corpus[idx][0].split("|")[0],
    #                                             corpus[idx][0].split("|")[1], score])
    #                             break
    #         else:
    #             var_idx = [x for x, y in enumerate(corpus) if y[0] == var]
    #             if var_idx:
    #                 matches += 1
    #                 omop = corpus[var_idx[0]][0].split(str("|"))[0]
    #                 sme = corpus[var_idx[0]][0].split(str("|"))[1]
    #
    #                 # retrieve top_n similar variables
    #                 for idx, score in self.similarity_search(tfidf_matrix, var_idx[0], top_n):
    #                     if 'http' in corpus[idx][0] and score > 0:
    #                         sim_res.append([omop, sme, row[label[0]],
    #                                         corpus[idx][0].split("|")[0],
    #                                         corpus[idx][0].split("|")[1], score])
    #                         break
    #
    #     pbar.finish()
    #
    #     # create pandas dataframe
    #     scored_vars = pd.DataFrame(dict(OMOP_ID=[x[0] for x in sim_res],
    #                                     SNOMED_ID=[x[1] for x in sim_res],
    #                                     LABEL=[str(x[2].encode('ascii', 'ignore')) for x in sim_res],
    #                                     ONT_ID=[x[3] for x in sim_res],
    #                                     ONT_LABEL=[str(x[4].encode('ascii', 'ignore')) for x in sim_res],
    #                                     score=[x[5] for x in sim_res]))
    #
    #     return scored_vars

    def mapper(map_terms, dic, dict_syn, dict_db):

        widgets = [Percentage(), Bar(), FormatLabel('(elapsed: %(elapsed)s)')]
        pbar = ProgressBar(widgets=widgets, maxval=len(map_terms))
        matches = []

        for names, values in pbar(map_terms.iterrows()):
            omop = values['OMOP']
            sme = values['SNOMED']
            sn = str(values['SNOMED_LABEL'].encode("utf-8")).lower().rstrip()
            ac_map = values['ANCESTOR']
            al = re.sub(r"^\s+|\s+$", "", str(values['ANCESTOR_LABEL'].encode("utf-8")).lower())
            cui = values['CUI']
            ac_cui = values['ANCESTOR_CUI']

            ont0 = [];
            ont_id0 = [];
            map0 = [];
            ont1 = [];
            ont_id1 = [];
            map1 = [];
            ont2 = [];
            ont_id2 = [];
            map2 = [];
            ont3 = [];
            ont_id3 = [];
            map3 = [];
            ont4 = [];
            ont_id4 = [];
            map4 = [];
            ont5 = [];
            ont_id5 = [];
            map5 = [];
            ont6 = [];
            ont_id6 = [];
            map6 = [];
            ont7 = [];
            ont_id7 = [];
            map7 = []

            # for ac in str(ac_map).split("|"):
            if ("SNOMED:" + str(sme) in dict_db.keys()) or \
                    (sn in dict_syn.keys()) or (sn in dic.keys()) or \
                    (cui in dict_db.keys()) or \
                    (len([x for x in ac_cui.split("|") if str(x) in dict_db.keys()]) > 0) or \
                    (len([str(x) for x in str(ac_map).split("|") if "SNOMED:" + str(x) in dict_db.keys()]) > 0) or \
                    (len([str(x) for x in str(al).split(" | ") if str(x) in dic.keys()]) > 0) or \
                    (len([str(x) for x in str(al).split(" | ") if str(x) in dict_syn.keys()]) > 0):

                if "SNOMED:" + str(sme) in dict_db.keys():
                    ont1 += [" | ".join([x for x in dict_db["SNOMED:" + str(sme)] if 'http' in x])]
                    ont_id1 += [" | ".join([x for x in dict_db["SNOMED:" + str(sme)] if 'http' not in x])]
                    map1 += ["SNOMED_DbXRef"]
                if cui in dict_db.keys():
                    ont0 += [" | ".join([x for x in dict_db[cui] if 'http' in x])]
                    ont_id0 += [" | ".join([x for x in dict_db[cui] if 'http' not in x])]
                    map0 += ["UMLS_DbXRef"]
                if sn in dict_syn.keys():
                    ont2 += [" | ".join([x for x in dict_syn[sn] if 'http' in x])]
                    ont_id2 += [" | ".join([x for x in dict_syn[sn] if 'http' not in x])]
                    map2 += ["Synonym"]
                if sn in dic.keys():
                    ont3 += [dic[sn][0]]
                    ont_id3 += [sn]
                    map3 += ["Label"]

                if len(filter(None,
                              [x if "SNOMED:" + str(x) in dict_db.keys() else "" for x in str(ac_map).split("|")])) > 0:
                    res = [x for y in
                           [dict_db.get("SNOMED:" + str(x)) for x in str(ac_map).split("|") if "SNOMED:" + str(
                               x) in dict_db.keys()] for x in y]
                    ont4 += [" | ".join([x for x in res if 'http' in x])]
                    ont_id4 += [" | ".join([x for x in res if 'http' not in x])]
                    map4 += ["SNOMED_DbXRef - Ancestor"]
                if len(filter(None, [x if str(x) in dict_db.keys() else "" for x in ac_cui.split(" | ")])) > 0:
                    res = [x for y in [dict_db.get(str(x)) for x in ac_cui.split(" | ") if str(x) in dict_db.keys()] for
                           x in y]
                    ont7 += [" | ".join([x for x in res if 'http' in x])]
                    ont_id7 += [" | ".join([x for x in res if 'http' not in x])]
                    map7 += ["UMLS_DbXRef - Ancestor"]
                if len(filter(None, [x if str(x) in dict_syn.keys() else "" for x in al.split(" | ")])) > 0:
                    res = [x for y in [dict_syn.get(str(x)) for x in al.split(" | ") if str(x) in dict_syn.keys()] for x
                           in y]
                    ont5 += [" | ".join([x for x in res if 'http' in x])]
                    ont_id5 += [" | ".join([x for x in res if 'http' not in x])]
                    map5 += ["Synonym - Ancestor"]
                if len(filter(None, [x if x in dic.keys() else [] for x in al.split(" | ")])) > 0:
                    res = [x for y in [dic.get(x) for x in al.split(" | ") if str(x) in dic.keys()] for x in y]
                    ont6 += [" | ".join([x for x in res if 'http' in x])]
                    ont_id6 += [" | ".join([x for x in al.split(" | ") if str(x) in dic.keys()])]
                    map6 += ["Label - Ancestor"]

            # condense and group matches
            ids1 = [[x.split(" | ") if len(ont1) > 0 else "" for x in ont1]] + \
                   [[x.split(" | ") if len(ont0) > 0 else "" for x in ont0]] + \
                   [[x.split(" | ") if len(ont3) > 0 else "" for x in ont3]] + \
                   [[x.split(" | ") if len(ont2) > 0 else "" for x in ont2]]
            nts1 = [[x.lower().split(" | ") if len(ont_id1) > 0 else "" for x in ont_id1]] + \
                   [[x.lower().split(" | ") if len(ont_id0) > 0 else "" for x in ont_id0]] + \
                   [[x.lower().split(" | ") if len(ont_id3) > 0 else "" for x in ont_id3]] + \
                   [[x.lower().split(" | ") if len(ont_id2) > 0 else "" for x in ont_id2]]
            mps1 = [x.strip() + "(" + str(len(ids1[0][0])) + ")" if len(ids1) >= 1 else "" for x in map1] + \
                   [x.strip() + "(" + str(len(ids1[1][0])) + ")" if len(ids1) > 1 else "" for x in map0] + \
                   [x.strip() + "(" + str(len(ids1[2][0])) + ")" if len(ids1) > 2 else "" for x in map3] + \
                   [x.strip() + "(" + str(len(ids1[3][0])) + ")" if len(ids1) > 3 else "" for x in map2]
            ids2 = [[x.split(" | ") if len(ont4) > 0 else ont4 for x in ont4]] + \
                   [[x.split(" | ") if len(ont7) > 0 else ont7 for x in ont7]] + \
                   [[x.split(" | ") if len(ont6) > 0 else ont6 for x in ont6]] + \
                   [[x.split(" | ") if len(ont5) > 0 else ont5 for x in ont5]]
            nts2 = [[x.lower().split(" | ") if len(ont_id4) > 0 else "" for x in ont_id4]] + \
                   [[x.lower().split(" | ") if len(ont_id7) > 0 else "" for x in ont_id7]] + \
                   [[x.lower().split(" | ") if len(ont_id6) > 0 else "" for x in ont_id6]] + \
                   [[x.lower().split(" | ") if len(ont_id5) > 0 else "" for x in ont_id5]]
            mps2 = [x.strip() + "(" + str(len(ids2[0][0])) + ")" if len(ont4) > 0 else "" for x in map4] + \
                   [x.strip() + "(" + str(len(ids2[1][0])) + ")" if len(ont7) > 0 else "" for x in map7] + \
                   [x.strip() + "(" + str(len(ids2[2][0])) + ")" if len(ont6) > 0 else "" for x in map6] + \
                   [x.strip() + "(" + str(len(ids2[3][0])) + ")" if len(ont5) > 0 else "" for x in map5]

            sn_id = " | ".join(set(filter(None, [x.split("/")[-1] for y in [x for y in ids1 for x in y] for x in y])))
            sn_nt = " | ".join(set(filter(None, [x for y in [x for y in nts1 for x in y] for x in y])))
            sn_mp = " | ".join(set(filter(None, mps1)))
            an_id = " | ".join(set(filter(None, [x.split("/")[-1] for y in [x for y in ids2 for x in y] for x in y])))
            an_nt = " | ".join(set(filter(None, [x for y in [x for y in nts2 for x in y] for x in y])))
            an_mp = " | ".join(set(filter(None, mps2)))

            matches.append([omop, sme, sn, ac_map, ac_cui, al, sn_id, sn_nt, sn_mp, an_id, an_nt, an_mp])

        pbar.finish()

        # output results
        mapped = pd.DataFrame(dict(OMOP_ID=[x[0] for x in matches],
                                   ANCESTOR=[x[3] for x in matches],
                                   SNOMED=[x[1] for x in matches],
                                   SNOMED_LABEL=[x[2] for x in matches],
                                   ANCESTOR_LABEL=[x[5] for x in matches],
                                   ANCESTOR_CUI=[x[4] for x in matches],
                                   ONT_XREF_ID=[x[6] for x in matches],
                                   ONT_XREF=[x[7] for x in matches],
                                   ONT_XREF_MAP=[x[8] for x in matches],
                                   ONT_SYN_ID=[x[9] for x in matches],
                                   ONT_SYN=[x[10] for x in matches],
                                   ONT_SYN_MAP=[x[11] for x in matches]))

        mapped_terms = mapped[
            ['OMOP_ID', 'SNOMED', 'SNOMED_LABEL', 'ANCESTOR', 'ANCESTOR_LABEL', 'ANCESTOR_CUI', 'ONT_XREF_ID',
             'ONT_XREF', 'ONT_XREF_MAP', 'ONT_SYN_ID', 'ONT_SYN', 'ONT_SYN_MAP']]

        mapped_terms = mapped_terms.drop_duplicates(['OMOP_ID', 'SNOMED', 'SNOMED_LABEL', 'ANCESTOR', 'ANCESTOR_LABEL',
                                                     'ANCESTOR_CUI', 'ONT_XREF_ID', 'ONT_XREF', 'ONT_XREF_MAP',
                                                     'ONT_SYN_ID', 'ONT_SYN', 'ONT_SYN_MAP'], keep="first")

        return mapped_terms

    @abstractmethod
    def annotator_type(self):
        """"A string representing the type annotator."""
        pass


class Conditions(Annotator):
    """An annotator to map clinical condition codes to ontology terms."""

    def annotator_type(self):
        """"A string representing the type annotator."""
        return 'condition codes'


class Medications(Annotator):
    """An annotator to map clinical condition codes to ontology terms."""

    def annotator_type(self):
        """"A string representing the type annotator."""
        return 'medication codes'


class Procedures(Annotator):
    """An annotator to map clinical procedure codes to ontology terms."""

    def annotator_type(self):
        """"A string representing the type annotator."""
        return 'procedure codes'
