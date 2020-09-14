#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ontology Utility Functions.

Interacts with OWL Tools API
* gets_ontology_classes
* gets_deprecated_ontology_classes

"""

# import needed libraries
import os
import os.path
from rdflib import Graph, Literal, Namespace, URIRef  # type: ignore
from rdflib.namespace import RDF, OWL  # type: ignore
import subprocess

from tqdm import tqdm  # type: ignore
from typing import Dict, Set, Tuple

# set up environment variables
obo = Namespace('http://purl.obolibrary.org/obo/')
oboinowl = Namespace('http://www.geneontology.org/formats/oboInOwl#')
schema = Namespace('http://www.w3.org/2001/XMLSchema#')


def gets_ontology_classes(graph: Graph, ont_id: str) -> Set:
    """Queries a knowledge graph and returns a list of all non-deprecated owl:Class objects in the graph.

    Args:
        graph: An rdflib Graph object.
        ont_id: A string containing an ontology namespace.

    Returns:
        class_list: A set of all of the classes in the graph.

    Raises:
        ValueError: If the query returns zero nodes with type owl:ObjectProperty.
    """

    print('Querying Knowledge Graph to Obtain all OWL:Class Nodes')

    # find all classes in graph
    class_list = set([x for x in graph.subjects(RDF.type, OWL.Class) if ont_id.lower() in str(x).lower()])

    if len(class_list) > 0: return class_list
    else: raise ValueError('ERROR: No classes returned from query.')


def gets_ontology_class_labels(graph: Graph, cls: Set) -> Dict:
    """Queries a knowledge graph and returns a dictionary of all owl:Class objects and their labels in the graph.

    Args:
        graph: An rdflib Graph object.
        cls: A set of current (non-deprecated) ontology class identifiers. For example:
            {URIRef('http://purl.obolibrary.org/obo/SO_0001590)}

    Returns:
        class_list: A dictionary where keys are string labels and values are ontology URIs. An example is shown below:
            {'consensus_aflp_fragment': 'http://purl.obolibrary.org/obo/SO_0001991',
             'polypeptide_magnesium_ion_contact_site': 'http://purl.obolibrary.org/obo/SO_0001098',
             '5kb_downstream_variant': 'http://purl.obolibrary.org/obo/SO_0001633',
             'enhancer_blocking_element': 'http://purl.obolibrary.org/obo/SO_0002190', ...}
    """

    print('\nQuerying Knowledge Graph to Obtain all OWL:Class Nodes and Labels')

    # find all classes in graph
    class_list = {str(x[2]).lower(): str(x[0]) for x in tqdm(graph) if x[0] in cls and 'label' in str(x[1]).lower()}

    return class_list


def gets_ontology_class_definitions(graph: Graph, cls: Set) -> Dict:
    """Queries a knowledge graph and returns a dictionary that contains all owl:Class objects and their definitions
    in the graph.

    Args:
        graph: An rdflib Graph object.
        cls: A set of current (non-deprecated) ontology class identifiers. For example:
            {URIRef('http://purl.obolibrary.org/obo/SO_0001590)}

    Returns:
        class_list: A dictionary where keys are string definitions and values are ontology URIs. An example is shown
        below:
             {'a chromosome originating in a micronucleus.': 'http://purl.obolibrary.org/obo/SO_0000825',
              'a stop codon redefined to be a new amino acid.': 'http://purl.obolibrary.org/obo/SO_0000883',
              'a gene that is silenced by rna interference.': 'http://purl.obolibrary.org/obo/SO_0001224',
              'te that exists (or existed) in nature.': 'http://purl.obolibrary.org/obo/SO_0000797', ...}
    """

    print('\nQuerying Knowledge Graph to Obtain all OWL:Class Nodes and Definitions')

    # find all classes in graph
    class_list = {str(x[2]).lower(): str(x[0]) for x in tqdm(graph) if x[0] in cls and 'IAO_0000115' in str(x[1])}

    return class_list


def gets_ontology_class_synonyms(graph: Graph, cls: Set) -> Tuple:
    """Queries a knowledge graph and returns a tuple of dictionaries. The first dictionary contains all owl:Class
    objects and their synonyms in the graph. The second dictionary contains the synonyms and their OWL types.

    Args:
        graph: An rdflib Graph object.
        cls: A set of current (non-deprecated) ontology class identifiers. For example:
            {URIRef('http://purl.obolibrary.org/obo/SO_0001590)}

    Returns:
        A tuple of dictionaries:
            synonyms: A dictionary where keys are string synonyms and values are ontology URIs. An example is shown
                below:
                    {'modified l selenocysteine': 'http://purl.obolibrary.org/obo/SO_0001402',
                    'modified l-selenocysteine': 'http://purl.obolibrary.org/obo/SO_0001402',
                    'frameshift truncation': 'http://purl.obolibrary.org/obo/SO_0001910', ...}
            synonym_type: A dictionary where keys are string synonyms and values are OWL synonym types. An example is
                shown below:
                    {'susceptibility to herpesvirus': 'hasExactSynonym', 'full upper lip': 'hasExactSynonym'}
    """

    print('\nQuerying Knowledge Graph to Obtain all OWL:Class Nodes and Synonyms')

    # find all classes in graph
    class_list = [x for x in tqdm(graph) if x[0] in cls and 'synonym' in str(x[1]).lower()]
    synonyms = {str(x[2]).lower(): str(x[0]) for x in class_list}
    synonym_type = {str(x[2]).lower(): str(x[1]).split('#')[-1] for x in class_list}

    return synonyms, synonym_type


def gets_ontology_class_dbxrefs(graph: Graph, cls: Set) -> Tuple:
    """Queries a knowledge graph and returns a dictionary that contains all owl:Class objects and their database
    cross references (dbxrefs) in the graph. This function will also include concepts that have been identified as
    exact matches. The query returns a tuple of dictionaries where the first dictionary contains the dbxrefs and
    exact matches (URIs and labels) and the second dictionary contains the dbxref/exactmatch uris and a string
    indicating the type (i.e. dbxref or exact match).

    #TODO: This is not entirely correct. Type dicts need to be updated to include ontology ID in key.

    Assumption: That none of the hasdbxref ids overlap with any of the exactmatch ids.

    Args:
        graph: An rdflib Graph object.
        cls: A set of current (non-deprecated) ontology class identifiers. For example:
            {URIRef('http://purl.obolibrary.org/obo/SO_0001590)}

    Returns:
        dbxref: A dictionary where keys are dbxref strings and values are ontology URIs. An example is shown below:
            {'loinc:LA6690-7': 'http://purl.obolibrary.org/obo/SO_1000002',
             'RNAMOD:055': 'http://purl.obolibrary.org/obo/SO_0001347',
             'RNAMOD:076': 'http://purl.obolibrary.org/obo/SO_0001368',
             'loinc:LA6700-2': 'http://purl.obolibrary.org/obo/SO_0001590', ...}
        dbxref_type: A dictionary where keys are dbxref/exact match uris and values are string indicating if the uri
            is for a dbxref or an exact match. An example is shown below:
                {
    """

    print('\nQuerying Knowledge Graph to Obtain all OWL:Class Nodes and DbXRefs')

    # dbxrefs
    dbxref_res = [x for x in tqdm(graph) if x[0] in cls and 'hasdbxref' in str(x[1]).lower()]
    dbxref_uris = {str(x[2]).lower(): str(x[0]) for x in dbxref_res}
    dbxref_type = {str(x[2]).lower(): 'DbXref' for x in dbxref_res}

    # exact match
    exact_res = [x for x in tqdm(graph) if x[0] in cls and 'exactmatch' in str(x[1]).lower()]
    exact_uris = {str(x[2]).lower(): str(x[0]) for x in exact_res}
    exact_type = {str(x[2]).lower(): 'ExactMatch' for x in exact_res}

    # combine dictionaries
    uris = {**dbxref_uris, **exact_uris}
    types = {**dbxref_type, **exact_type}

    return uris, types


def gets_deprecated_ontology_classes(graph: Graph, ont_id: str) -> Set:
    """Queries a knowledge graph and returns a list of all deprecated owl:Class objects in the graph.

    Args:
        graph: An rdflib Graph object.
        ont_id: A string containing an ontology namespace.

    Returns:
        class_list: A list of all of the deprecated OWL classes in the graph.

    Raises:
        ValueError: If the query returns zero nodes with type owl:Class.
    """

    print('Querying Knowledge Graph to Obtain all Deprecated OWL:Class Nodes')

    # find all deprecated classes in graph
    dep_classes = list(graph.subjects(OWL.deprecated, Literal('true', datatype=URIRef(schema + 'boolean'))))
    class_list = set([x for x in dep_classes if ont_id.lower() in str(x).lower()])

    return class_list


def gets_ontology_statistics(file_location: str, owltools_location: str = './omop2obo/libs/owltools') -> None:
    """Uses the OWL Tools API to generate summary statistics (i.e. counts of axioms, classes, object properties, and
    individuals).

    Args:
        file_location: A string that contains the file path and name of an ontology.
        owltools_location: A string pointing to the location of the owl tools library.

    Returns:
        A set of all the deprecated ontology classes.

    Raises:
        TypeError: If the file_location is not type str.
        OSError: If file_location points to a non-existent file.
        ValueError: If file_location points to an empty file.
    """

    if not isinstance(file_location, str):
        raise TypeError('ERROR: file_location must be a string')
    elif not os.path.exists(file_location):
        raise OSError('The {} file does not exist!'.format(file_location))
    elif os.stat(file_location).st_size == 0:
        raise ValueError('FILE ERROR: input file: {} is empty'.format(file_location))
    else:
        output = subprocess.check_output([os.path.abspath(owltools_location), file_location, '--info'])

    # print stats
    res = output.decode('utf-8').split('\n')[-5:]
    cls, axs, op, ind = res[0].split(':')[-1], res[3].split(':')[-1], res[2].split(':')[-1], res[1].split(':')[-1]
    sent = '\nThe knowledge graph contains {0} classes, {1} axioms, {2} object properties, and {3} individuals\n'

    print(sent.format(cls, axs, op, ind))

    return None
