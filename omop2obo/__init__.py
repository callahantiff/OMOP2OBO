#!/usr/bin/env python
# -*- coding: utf-8 -*-


""" A Library for mapping OMOP concepts to OBO

Precision medicine requires timely synthesis of clinical and genomic data. Despite large-scale biobanking efforts,
most electronic health records (EHRs) do not systematically integrate nor have the infrastructure to incorporate
genomic data. Common data models (CDMs) have solved many of the challenges of utilizing EHR data, yet they do not
include resources needed to integrate or interpret clinical and genomic data. Biomedical ontologies provide accurate
and semantically computable representations of biological knowledge. Aligning patient data to open biomedical ontologies
(OBO) requires manual and/or semi-automated curation and domain expertise, limiting existing efforts to specific
diseases and clinical data.

We introduce OMOP2OBO - the first health system-wide, disease-agnostic mappings between standardized clinical
terminologies in the Observational Medical Outcomes Partnership (OMOP) CDM and several OBO foundry ontologies. These
mappings were validated by domain experts and their coverage was examined in several health systems.

There is one way to run PheKnowLator (NEEDS TO BE FINISHED):
  1. Command line via argparse (Main.py)
"""

__all__ = [
    'OntologyDownloader'
]

from omop2obo.ontology_downloader import OntologyDownloader
