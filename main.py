#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import click
import glob
import pickle

from omop2obo import ConceptAnnotator, OntologyDownloader, OntologyInfoExtractor


@click.command()
@click.option('--ontology_file', type=click.Path(exists=True), required=True,
              prompt='The file path and name containing the list of ontologies to process')
@click.option('--clinical_domain', required=True, prompt='The clinical domain of the input file')
@click.option('--clinical_data', type=click.Path(exists=True), required=True,
              prompt='The filepath to the clinical data needing mapping')
@click.option('--primary_key', required=True, prompt='The name of the file to use as the primary key (e.g. CONCEPT_ID)')
@click.option('--concept_codes', required=True, prompt='A comma-separated list (without spaces) of concept-level codes '
                                                       'to map to DbXRefs (e.g. CONCEPT_SOURCE_CODE)')
@click.option('--concept_strings', prompt='A comma-separated list (without spaces) of concept-level strings to map to '
                                          'use for exact string mapping (e.g. CONCEPT_LABEL, CONCEPT_SYNONYM)')
@click.option('--ancestor_codes', prompt='A comma-separated list (without spaces) of ancestor-level codes to map to '
                                         'DbXRefs (e.g. ANCESTOR_SOURCE_CODE)')
@click.option('--ancestor_strings', prompt='A comma-separated list (without spaces) of ancestor-level strings to map '
                                           'to use for exact string mapping (e.g. ANCESTOR_LABEL, ANCESTOR_SYNONYM)')
def main(ontology_file: str, clinical_domain: str, clinical_data: str, primary_key: str, concept_codes: str,
         concept_strings: str, ancestor_codes: str, ancestor_strings: str):
    ######################
    # PROCESS ONTOLOGIES #
    ######################

    # download ontologies
    # ontology_resource_file = 'resources/ontology_source_list.txt'
    ont = OntologyDownloader(ontology_file)
    ont.downloads_data_from_url()

    # data_files = {'cl': 'resources/ontologies/cl_without_imports.owl',
    #  'chebi': 'resources/ontologies/chebi_without_imports.owl',
    #  'hp': 'resources/ontologies/hp_without_imports.owl',
    #  'mondo': 'resources/ontologies/mondo_without_imports.owl',
    #  'ncbitaxon': 'resources/ontologies/ncbitaxon_without_imports.owl',
    #  'pr': 'resources/ontologies/pr_without_imports.owl',
    #  'uberon': 'resources/ontologies/ext_without_imports.owl',
    #  'vo': 'resources/ontologies/vo_without_imports.owl'}

    # process ontologies
    ont_explorer = OntologyInfoExtractor('resources/ontologies', ont.data_files)
    ont_explorer.ontology_processor()

    # create master dictionary of processed ontologies
    ont_explorer.ontology_loader()

    # read in ontology data
    with open('resources/ontologies/master_ontology_dictionary.pickle', 'rb') as handle:
        ontology_data = pickle.load(handle)
    handle.close()

    #########################
    # PROCESS CLINICAL DATA #
    ########################

    # STEP 1 - download clinical data from GCS (or put data files in the resources/clinical_data repo)
    # see README in 'resources/clinical_data'; assumes all clinical data will be located in "resources/clinical_data"

    # STEP 2 - download MRCONSO.RRF and MRSTY.RRF files from the NLM UMLS and put data in "resources/mappings"
    # see README for more details - make sure "MRCONSO" and "MRSTY" are included in the filename

    # STEP 3 - perform clinical concept mapping
    if clinical_domain.lower() == 'condition':
        # Condition Occurrence Data
        cond_ont = {k: v for k, v in ontology_data.items() if k in ['hp', 'mondo']}
        # clinical_data = 'resources/clinical_data/omop2obo_conditions_june2020.csv'
        # primary_ket = 'CONCEPT_ID'
        # concept_codes = ['CONCEPT_SOURCE_CODE']
        # concept_strings = ['CONCEPT_LABEL', 'CONCEPT_SYNONYM']
        # anscestor_codes = ['ANCESTOR_SOURCE_CODE']
        # ancestor_strings = ['ANCESTOR_LABEL']
        condition_map = ConceptAnnotator(clinical_data, cond_ont, primary_key, concept_codes.split(','),
                                         concept_strings.split(','), ancestor_codes.split(','),
                                         ancestor_strings.split(','),
                                         glob.glob('resources/mappings/*MRCONSO*')[0]
                                         if len(glob.glob('resources/mappings/*MRCONSO*')) > 0 else None,
                                         glob.glob('resources/mappings/*MRCONSO*')[0]
                                         if len(glob.glob('resources/mappings/*MRCONSO*')) > 0 else None)

        conds = condition_map.clinical_concept_mapper()
        conds.to_csv('mappings/condition_codes/OMOP2OBO_MAPPED_CONDS.csv', sep=',', index=False, header=True)
    elif clinical_domain == 'labs':
        # Measurement Data
        lab_ont = {k: v for k, v in ontology_data.items() if k in ['hp', 'ext', 'cl', 'chebi', 'pr', 'ncbitaxon']}
        measurement_map = ConceptAnnotator(clinical_data, lab_ont, primary_key, concept_codes.split(','),
                                           concept_strings.split(','), ancestor_codes.split(','),
                                           ancestor_strings.split(','),
                                           glob.glob('resources/mappings/*MRCONSO*')[0]
                                           if len(glob.glob('resources/mappings/*MRCONSO*')) > 0 else None,
                                           glob.glob('resources/mappings/*MRCONSO*')[0]
                                           if len(glob.glob('resources/mappings/*MRCONSO*')) > 0 else None)

        labs = measurement_map.clinical_concept_mapper()
        labs.to_csv('mappings/condition_codes/OMOP2OBO_MAPPED_LABS.csv', sep=',', index=False, header=True)
    else:
        # Drug Exposure Data
        drug_ont = {k: v for k, v in ontology_data.items() if k in ['chebi', 'pr', 'ncbitaxon', 'vo']}
        drug_exposure_map = ConceptAnnotator(clinical_data, drug_ont, primary_key, concept_codes.split(','),
                                             concept_strings.split(','), ancestor_codes.split(','),
                                             ancestor_strings.split(','),
                                             glob.glob('resources/mappings/*MRCONSO*')[0]
                                             if len(glob.glob('resources/mappings/*MRCONSO*')) > 0 else None,
                                             glob.glob('resources/mappings/*MRCONSO*')[0]
                                             if len(glob.glob('resources/mappings/*MRCONSO*')) > 0 else None)

        drugs = drug_exposure_map.clinical_concept_mapper()
        drugs.to_csv('mappings/condition_codes/OMOP2OBO_MAPPED_DRUGS.csv', sep=',', index=False, header=True)
