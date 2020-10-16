#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import click
import glob
import pandas as pd
import pickle

from datetime import date, datetime
from typing import Tuple

from omop2obo import ConceptAnnotator, OntologyDownloader, OntologyInfoExtractor, SimilarStringFinder
from omop2obo.utils import aggregates_mapping_results


@click.command()
@click.option('--ont_file', type=click.Path(exists=True), required=True, default='resources/ontology_source_list.txt')
@click.option('--tfidf_mapping', required=True, default='no')
@click.option('--clinical_domain', required=True)
@click.option('--merge', required=True, multiple=True, default='True or False - UMLS Expanded Merge')
@click.option('--onts', required=True, multiple=True, default=['List'])
@click.option('--clinical_data', type=click.Path(exists=True), required=True)
@click.option('--primary_key', required=True, default='CONCEPT_ID')
@click.option('--concept_codes', required=True, multiple=True, default=['CONCEPT_SOURCE_CODE'])
@click.option('--concept_strings', multiple=True, default=['CONCEPT_LABEL', 'CONCEPT_SYNONYM'])
@click.option('--ancestor_codes', multiple=True, default=['ANCESTOR_SOURCE_CODE'])
@click.option('--ancestor_strings', multiple=True, default=['ANCESTOR_LABEL', 'ANCESTOR_SYNONYM'])
@click.option('--outfile', required=True, default='./resources/mapping/OMOP2OBO_MAPPED_')
def main(ont_file: str, tfidf_mapping: str, clinical_domain: str, onts: list, clinical_data: str, primary_key: str,
         concept_codes: Tuple, concept_strings: Tuple, ancestor_codes: Tuple, ancestor_strings: Tuple,
         merge: bool, outfile: str):
    """The OMOP2OBO package provides functionality to assist with mapping OMOP standard clinical terminology concepts to
    OBO terms. Successfully running this program requires several input parameters, which are specified below:

    PARAMETERS:

        ont_file: 'resources/oontology_source_list.txt'
        tfidf_mapping: "yes" if want to perform cosine similarity mapping using a TF-IDF matrix.
        clinical_domain: clinical domain of input data (i.e. "conditions", "drugs", or "measurements").
        onts: A comma-separated list of ontology prefixes that matches 'resources/oontology_source_list.txt'.
        clinical_data: The filepath to the clinical data needing mapping.
        primary_key: The name of the file to use as the primary key.
        concept_codes: A comma-separated list of concept-level codes to use for DbXRef mapping.
        concept_strings: A comma-separated list of concept-level strings to map to use for exact string mapping.
        ancestor_codes: A comma-separated list of ancestor-level codes to use for DbXRef mapping.
        ancestor_strings: A comma-separated list of ancestor-level strings to map to use for exact string mapping.
        merge: A bool specifying whether to merge UMLS SAB codes with OMOP source codes once or twice.
            Merging once will only align OMOP source codes to UMLS SAB, twice with take the CUIs from the first merge
            and merge them again with the full UMLS SAB set resulting in a larger set of matches. The default value
            is True, which means that the merge will be performed twice.
        outfile: The filepath for where to write output data to.

    Several dependencies must be addressed before running this file. Please see the README for instructions.
    """

    ######################
    # PROCESS ONTOLOGIES #
    ######################

    # download ontologies
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

    date_today = '_' + datetime.strftime(datetime.strptime(str(date.today()), '%Y-%m-%d'), '%d%b%Y').upper()

    mapper = ConceptAnnotator(clinical_file=clinical_data,
                              ontology_dictionary={k: v for k, v in ont_data.items() if k in onts},
                              umls_expand=merge,
                              primary_key=primary_key,
                              concept_codes=concept_codes,
                              concept_strings=concept_strings,
                              ancestor_codes=ancestor_codes,
                              ancestor_strings=ancestor_strings,
                              umls_mrconso_file=glob.glob('resources/mappings/*MRCONSO*')[0]
                              if len(glob.glob('resources/mappings/*MRCONSO*')) > 0 else None,
                              umls_mrsty_file=glob.glob('resources/mappings/*MRSTY*')[0]
                              if len(glob.glob('resources/mappings/*MRSTY*')) > 0 else None)

    mappings = mapper.clinical_concept_mapper()

    # get column names -- used later to organize output
    start_cols = [i for i in mappings.columns if not any(j for j in ['STR', 'DBXREF', 'EVIDENCE'] if j in i)]
    exact_cols = [i for i in mappings.columns if i not in start_cols]

    print('\nSaving Results: {}'.format('Exact Match'))
    mappings.to_csv(outfile + clinical_domain.upper() + date_today + '.csv', sep=',', index=False, header=True)

    # STEP 4: TF-IDF SIMILARITY MAPPING
    # searches top 10 highest results and currently keeps the top 75th percentile among scores >=0.25
    if tfidf_mapping is not None:
        sim = SimilarStringFinder(clinical_file=clinical_data,
                                  ontology_dictionary={k: v for k, v in ont_data.items() if k in onts},
                                  primary_key=primary_key,
                                  concept_strings=concept_strings)

        sim_mappings = sim.performs_similarity_search()
        # get column names -- used later to organize output
        sim_mappings = sim_mappings[[primary_key] + [x for x in sim_mappings.columns if 'SIM' in x]].drop_duplicates()
        sim_cols = [i for i in sim_mappings.columns if not any(j for j in start_cols if j in i)]

        # merge dbXref, exact string, and TF-IDF similarity results
        merged_scores = pd.merge(mappings, sim_mappings, how='left', on=primary_key)
        mappings = merged_scores[start_cols + exact_cols + sim_cols]

        print('\nSaving Results: {}'.format('TF-IDF Cosine Similarity'))
        mappings.to_csv(outfile + clinical_domain.upper() + date_today + '.csv', sep=',', index=False, header=True)

    # clean up output
    if clinical_domain == 'LABS':
        result_type_idx, updated_data = list(mappings.columns).index('RESULT_TYPE'), []
        for idx, row in mappings.iterrows():
            if row['RESULT_TYPE'] == 'Normal/Low/High' or row['RESULT_TYPE'] == 'Negative/Positive':
                for x in row['RESULT_TYPE'].split('/'):
                    updated = list(row)
                    updated[result_type_idx] = x
                    updated_data.append(updated)
            else:
                updated_data.append(list(row))

        # replace values
        data_expanded = pd.DataFrame(updated_data, columns=list(mappings.columns))
    else:
        data_expanded = mappings.copy()
    data_expanded.fillna('', inplace=True)

    updated_maps = aggregates_mapping_results(primary_key, data_expanded, onts, ont_data, mapper.source_code_map, 0.25)
    updated_maps.to_csv(outfile + clinical_domain.upper() + date_today + '.csv', sep=',', index=False, header=True)


if __name__ == '__main__':
    main()
