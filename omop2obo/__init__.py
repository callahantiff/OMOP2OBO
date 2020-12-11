#!/usr/bin/env python
# -*- coding: utf-8 -*-


""" A Library for mapping OMOP concepts to OBO

OMOP2OBO is the first health system-wide, disease-agnostic mappings between standardized clinical terminologies in
the [Observational Medical Outcomes Partnership (OMOP) common data model and several Open Biomedical Ontologies (OBO)
foundry ontologies. These mappings were validated by domain experts and their coverage was examined in several health
systems.

There are two ways to run PheKnowLator:
  1. Command line via argparse (Main.py)
  2. Jupyter Notebook (omop2obo_mapping_validation.ipynb)
"""

__all__ = [
    'ConceptAnnotator',

    'OntologyDownloader',

    'OntologyInfoExtractor',

    'SemanticTransformer',

    'SimilarStringFinder'
]

from omop2obo.clinical_concept_annotator import ConceptAnnotator
from omop2obo.ontology_downloader import OntologyDownloader
from omop2obo.ontology_explorer import OntologyInfoExtractor
from omop2obo.semantic_mapping_representation import SemanticTransformer
from omop2obo.string_similarity import SimilarStringFinder
