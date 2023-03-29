#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
from omop2obo import *


def main():
    """The OMOP2OBO package provides functionality to assist with mapping Observational Medical Outcomes Partnership
    (OMOP) clinical terminology concepts to Open Biomedical Ontology (OBO) terms.

    See the Wiki for details: https://github.com/callahantiff/OMOP2OBO/wiki/V2.0----beta.
    """

    ######################
    # PROCESS ONTOLOGIES #
    ######################
    # STEP 1: Download ontologies
    ont = OntologyDownloader('resources/ontology_source_list.txt')
    ont.downloads_data_from_url()

    # STEP 2: Prepare ontology data for mapping
    ont_explorer = OntologyInfoExtractor('resources/ontologies', ont.data_files)
    ont_explorer.ontology_processor()


    #################################
    # PROCESS CLINICAL VOCABULARIES #
    #################################
    # STEP 1: Process clinical vocabularies
    omop_data_processor = OMOPDataProcessor()
    omop_data_processor.data_processor()
    # # if already processed (uncomment and run)
    # omop_df = pickle.load(open('resources/clinical_data/OMOP_MAP_PANEL.pkl', 'rb'))
    # omop_anc_dict = pickle.load(open('resources/clinical_data/OMOP_MAP_Ancestor_Dictionary.pkl', 'rb'))
    # omop_data = {'omop_full': omop_df, 'concept_ancestors': omop_anc_dict}

    # STEP 2: Process UMLS data
    umls_data_processor = UMLSDataProcessor()
    umls_data_processor.data_processor()
    # # if already processed (uncomment and run)
    # umls_df = pickle.load(open('resources/umls_data/UMLS_MAP_PANEL.pkl', 'rb'))
    # umls_anc_dict = pickle.load(open('resources/umls_data/UMLS_MAP_Ancestor_Dictionary.pkl', 'rb'))
    # umls_data = {'umls_full': umls_df, 'aui_ancestors': umls_anc_dict}


    #####################
    # GENERATE MAPPINGS #
    #####################
    # an example is provided below using the HPO and a specific set of source vocabularies
    ont_alias = 'hp'
    filter_vocabs = ['umls', 'icd10', 'icd10cm', 'icd9', 'icd9cm', 'snomed', ont_alias]
    mapper = ConceptMapper(ontology_alias=ont_alias, id_list=None, filter_vocabs=filter_vocabs)
    mapper.generate_exact_mappings()


if __name__ == '__main__':
    main()
