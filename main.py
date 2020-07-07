#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
# from more_itertools import unique_everseen
# import pandas as pd

from omop2obo.ontology_downloader import OntologyDownloader
# from omop2obo.concept_annotator import *
from omop2obo.ontology_explorer import OntologyInfoExtractor


# def preprocess_sentences(sentence):
#     """Preprocess an input sentence by: lowering the case, removing non-alphanumeric characters, tokenizing, and
#     removing English stop words.
#
#     Args:
#         sentence: A string representing a sentence of text
#
#     Returns:
#         A string of text which has been preprocessed
#     """
#
#     # replace all non-alphanumeric characters with spaces
#     lower_nopunct = re.sub(' +', ' ', re.sub(r'[^a-zA-Z0-9\s\-]', ' ', sentence.lower()))
#
#     # tokenize & remove punctuation
#     token = list(unique_everseen(RegexpTokenizer(r'\w+').tokenize(lower_nopunct)))
#
#     # remove stop words & perform lemmatization
#     token_stop = [str(x) for x in token if x not in stopwords.words('english')]
#     # token_lemma = [str(WordNetLemmatizer().lemmatize(x)) for x in token if x not in stopwords.words('english')]
#
#     return token


def main():

    ######################
    # PROCESS ONTOLOGIES #
    ######################

    # download ontologies
    ont = OntologyDownloader('resources/ontology_source_list.txt')
    ont.downloads_data_from_url()

    # process ontologies
    ont_explorer = OntologyInfoExtractor('resources/ontologies', ont.data_files)
    ont_explorer.ontology_processor()

    # load ontologies
    ontology_data = ont_explorer.ontology_loader()

    for key in ontology_data.keys():
        print(key)
        for key2 in ontology_data[key].keys():
            print(key2, len(ontology_data[key][key2]))

    #########################
    # PROCESS CLINICAL DATA #
    ########################

    # STEP 1 - download clinical data from GCS (or put data files in the resources/clinical_data repo)
    # see README in 'resources/clinical_data'; assumes all clinical data will be located in "resources/clinical_data"

    # STEP 2 - download MRCONSO.RRF from NLM UMLS and put data in "resources/mappings"
    # see README for more details - make sure "MRCONSO" is included in the filename

    # STEP 3 - perform clinical concept mapping
    # This step consists of four steps and will be performed for each clinical domain:
    #    a - UMLS Semantic Typing
    #    b - DbXRef mapping
    #    c - Exact String Mapping to concept labels and/or synonyms
    #    d - Similarity distance mapping

    # CONDITION_OCCURRENCE CONCEPTS
    # reduce ontology dictionary to relevant ontologies
    cond_onts = {k: v for k, v in ontology_data.items() if k in ['hp', 'mondo']}
    omop_conditions = 'resources/clinical_data/omop2obo_conditions_june2020.csv'


    # step a - semantic typing

    # step b - dbXRef mapping

    # step c - exact string mapping

    # step d - similarity distance mapping

    # MEASUREMENT CONCEPTS
    # reduce ontology dictionary to relevant ontologies
    lab_onts = {k: v for k, v in ontology_data.items() if k in ['hp', 'uberon', 'cl', 'chebi', 'pr', 'ncbitaxon']}

    # DRUG_EXPOSURE CONCEPTS
    # reduce ontology dictionary to relevant ontologies
    med_onts = {k: v for k, v in ontology_data.items() if k in ['chebi', 'pr', 'ncbitaxon', 'vo']}
