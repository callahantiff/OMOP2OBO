#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import click
import glob
import pandas as pd
import pickle

from datetime import date, datetime
from pandas import pd

from omop2obo import ConceptAnnotator, OntologyDownloader, OntologyInfoExtractor, SimilarStringFinder


@click.command()
@click.option('--ont_file', type=click.Path(exists=True), required=True,
              prompt='The file path and name containing the list of ontologies to process')
@click.option('--tfidf_mapping', type=click.Path(exists=True), required=True,
              prompt='Please pass "yes" if want to perform TF-IDF mapping.')
@click.option('--clinical_domain', required=True, prompt='The clinical domain of the input file')
@click.option('--ont_prefix', required=True,
              prompt='A comma-separated list (without spaces) of ontology prefixes to use (e.g. hp,mondo)')
@click.option('--clinical_data', type=click.Path(exists=True), required=True,
              prompt='The filepath to the clinical data needing mapping')
@click.option('--primary_key', required=True, prompt='The name of the file to use as the primary key (e.g. CONCEPT_ID)')
@click.option('--concept_codes', required=True, prompt='A comma-separated list (without spaces) of concept-level codes '
                                                       'to map to DbXRefs (e.g. CONCEPT_SOURCE_CODE)')
@click.option('--concept_strings', prompt='A comma-separated list (without spaces) of concept-level strings to map to '
                                          'use for exact string mapping (e.g. CONCEPT_LABEL,CONCEPT_SYNONYM)')
@click.option('--ancestor_codes', prompt='A comma-separated list (without spaces) of ancestor-level codes to map to '
                                         'DbXRefs (e.g. ANCESTOR_SOURCE_CODE)')
@click.option('--ancestor_strings', prompt='A comma-separated list (without spaces) of ancestor-level strings to map '
                                           'to use for exact string mapping (e.g. ANCESTOR_LABEL,ANCESTOR_SYNONYM)')
@click.option('--outfile', required=True, prompt='The filepath for where to write output data to')
def main(ont_file: str, tfidf_mapping: str, clinical_domain: str, ont_prefix: str, clinical_data: str,
         primary_key: str, concept_codes: str, concept_strings: str, ancestor_codes: str, ancestor_strings: str,
         outfile: str):
    ######################
    # PROCESS ONTOLOGIES #
    ######################

    # download ontologies
    # ontology_resource_file = 'resources/ontology_source_list.txt'
    ont = OntologyDownloader(ont_file)
    ont.downloads_data_from_url()

    # process ontologies
    ont_explorer = OntologyInfoExtractor('resources/ontologies', ont.data_files)
    ont_explorer.ontology_processor()

    # create master dictionary of processed ontologies
    ont_explorer.ontology_loader()

    # read in ontology data
    with open('resources/ontologies/master_ontology_dictionary.pickle', 'rb') as handle:
        ont_data = pickle.load(handle)
    handle.close()

    #########################
    # PROCESS CLINICAL DATA #
    ########################

    # STEP 1 - download clinical data from GCS (or put data files in the resources/clinical_data repo)
    # see README in 'resources/clinical_data'; assumes all clinical data will be located in "resources/clinical_data"

    # STEP 2 - download MRCONSO.RRF and MRSTY.RRF files from the NLM UMLS and put data in "resources/mappings"
    # see README for more details - make sure "MRCONSO" and "MRSTY" are included in the filename

    # STEP 3 - perform clinical concept mapping
    date_today = '_' + datetime.strftime(datetime.strptime(str(date.today()), '%Y-%m-%d'), '%d%b%Y').upper()

    # clinical_domain = 'CONDITIONS'
    # ont_prefix = ['hp', 'mondo']
    # clinical_data, primary_key = 'resources/clinical_data/omop2obo_conditions_june2020.csv', 'CONCEPT_ID'
    # concept_codes, concept_strings = ['CONCEPT_SOURCE_CODE'], ['CONCEPT_LABEL', 'CONCEPT_SYNONYM']
    # ancestor_codes, ancestor_strings = ['ANCESTOR_SOURCE_CODE'], ['ANCESTOR_LABEL']
    # outfile = 'resources/mappings/condition_codes/July2020/OMOP2OBO_MAPPED_'

    # clinical_domain = 'DRUGS'
    # ont_prefix = ['chebi', 'pr', 'ncbitaxon', 'vo']
    # clinical_data ='resources/clinical_data/omop2obo_drug_exposure_june2020.csv'
    # primary_key = 'INGREDIENT_CONCEPT_ID'
    # concept_codes, concept_strings = ['INGREDIENT_SOURCE_CODE'], ['INGREDIENT_LABEL', 'INGREDIENT_SYNONYM']
    # ancestor_codes, ancestor_strings = ['INGRED_ANCESTOR_SOURCE_CODE'], ['INGRED_ANCESTOR_LABEL']
    # outfile = 'resources/mappings/medication_codes/July2020/OMOP2OBO_MAPPED_'

    # clinical_domain = 'LABS'
    # ont_prefix = ['hp', 'ext', 'cl', 'chebi', 'pr', 'ncbitaxon']
    # clinical_data, primary_key = 'resources/clinical_data/omop2obo_measurements_june2020.csv', 'CONCEPT_ID'
    # concept_codes, concept_strings = ['CONCEPT_SOURCE_CODE'], ['CONCEPT_LABEL', 'CONCEPT_SYNONYM']
    # ancestor_codes, ancestor_strings = ['ANCESTOR_SOURCE_CODE'], ['ANCESTOR_LABEL']
    # outfile = 'resources/mappings/laboratory_tests/July2020/OMOP2OBO_MAPPED_'

    mapper = ConceptAnnotator(clinical_file=clinical_data,
                              ontology_dictionary={k: v for k, v in ont_data.items() if k in ont_prefix.split(',')},
                              primary_key=primary_key,
                              concept_codes=concept_codes.split(','),
                              concept_strings=concept_strings.split(','),
                              ancestor_codes=ancestor_codes.split(','),
                              ancestor_strings=ancestor_strings.split(','),
                              umls_mrconso_file=glob.glob('resources/mappings/*MRCONSO*')[0]
                              if len(glob.glob('resources/mappings/*MRCONSO*')) > 0 else None,
                              umls_mrsty_file=glob.glob('resources/mappings/*MRCONSO*')[0]
                              if len(glob.glob('resources/mappings/*MRCONSO*')) > 0 else None)

    exact_mappings = mapper.clinical_concept_mapper()
    exact_mappings.to_csv(outfile + clinical_domain.upper() + date_today + '.csv', sep=',', index=False, header=True)
    # get column names -- used later to organize output
    start_cols = [i for i in exact_mappings.columns if not any(j for j in ['STR', 'DBXREF', 'EVIDENCE'] if j in i)]
    exact_cols = [i for i in exact_mappings.columns if i not in start_cols]

    # STEP 4: TF-IDF SIMILARITY MAPPING
    if tfidf_mapping is not None:
        sim = SimilarStringFinder(clinical_file=outfile + clinical_domain.upper() + date_today + '.csv',
                                  ontology_dictionary={k: v for k, v in ont_data.items()
                                                       if k in ont_prefix},
                                  primary_key=primary_key,
                                  concept_strings=concept_strings)

        sim_mappings = sim.performs_similarity_search()
        sim_mappings = sim_mappings[[primary_key] + [x for x in sim_mappings.columns if 'SIM' in x]].drop_duplicates()
        # get column names -- used later to organize output
        sim_cols = [i for i in sim_mappings.columns if not any(j for j in start_cols if j in i)]

        # merge dbXref, exact string, and TF-IDF similarity results
        merged_scores = pd.merge(exact_mappings, sim_mappings, how='left', on=primary_key)
        # re-order columns and write out data
        merged_scores = merged_scores[start_cols + exact_cols + sim_cols]
        merged_scores.to_csv(outfile + clinical_domain.upper() + date_today + '.csv', sep=',', index=False, header=True)
