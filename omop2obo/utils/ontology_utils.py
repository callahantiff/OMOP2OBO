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
from rdflib import Graph, Namespace, URIRef  # type: ignore
from rdflib.namespace import RDF, RDFS, OWL  # type: ignore
import subprocess

from tqdm import tqdm  # type: ignore
from typing import Dict, Set

# set up environment variables
obo = Namespace('http://purl.obolibrary.org/obo/')
oboinowl = Namespace('http://www.geneontology.org/formats/oboInOwl#')


def gets_ontology_classes(graph: Graph, ont_id: str) -> Set:
    """Queries a knowledge graph and returns a list of all non-deprecated owl:Class objects in the graph.

    Args:
        graph: An rdflib Graph object.
        ont_id: A string containing an ontology namespace.

    Returns:
        class_list: A list of all of the classes in the graph.

    Raises:
        ValueError: If the query returns zero nodes with type owl:ObjectProperty.
    """

    print('\nQuerying Knowledge Graph to Obtain all OWL:Class Nodes')

    # find all classes in graph
    kg_classes = graph.query(
        """SELECT DISTINCT ?c
             WHERE {
              ?c rdf:type owl:Class .
              MINUS {?c owl:deprecated true}}
        """, initNs={'rdf': RDF, 'owl': OWL}
    )

    # convert results to list of classes
    class_list = set([str(res[0]) for res in tqdm(kg_classes)
                      if isinstance(res[0], URIRef) and ont_id .lower() in str(res[0]).lower()])

    if len(class_list) > 0: return class_list
    else: raise ValueError('ERROR: No classes returned from query.')


def gets_ontology_class_labels(graph: Graph, ont_id: str) -> Dict:
    """Queries a knowledge graph and returns a dictionary of all owl:Class objects and their labels in the graph.

    Args:
        graph: An rdflib Graph object.
        ont_id: A string containing an ontology namespace.

    Returns:
        class_list: A dictionary where keys are string labels and values are ontology URIs. An example is shown below:
            {'consensus_aflp_fragment': 'http://purl.obolibrary.org/obo/SO_0001991',
             'polypeptide_magnesium_ion_contact_site': 'http://purl.obolibrary.org/obo/SO_0001098',
             '5kb_downstream_variant': 'http://purl.obolibrary.org/obo/SO_0001633',
             'enhancer_blocking_element': 'http://purl.obolibrary.org/obo/SO_0002190', ...}
    """

    print('\nQuerying Knowledge Graph to Obtain all OWL:Class Nodes and Labels')

    # find all classes in graph
    kg_classes = graph.query(
        """SELECT DISTINCT ?c ?c_label
             WHERE {
              ?c rdf:type owl:Class .
              ?c rdfs:label ?c_label . 
              MINUS {?c owl:deprecated true}}
        """, initNs={'rdf': RDF, 'rdfs': RDFS, 'owl': OWL}
    )

    # convert results to list of classes
    class_list = {str(res[1]).lower(): str(res[0]) for res in tqdm(kg_classes)
                  if isinstance(res[0], URIRef) and ont_id.lower() in str(res[0]).lower()}

    return class_list


def gets_ontology_class_definitions(graph: Graph, ont_id: str) -> Dict:
    """Queries a knowledge graph and returns a dictionary that contains all owl:Class objects and their definitions
    in the graph.

    Args:
        graph: An rdflib Graph object.
        ont_id: A string containing an ontology namespace.

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
    kg_classes = graph.query(
        """SELECT DISTINCT ?c ?c_defn
             WHERE {
              ?c rdf:type owl:Class .
              ?c obo:IAO_0000115 ?c_defn .
              MINUS {?c owl:deprecated true}}
        """, initNs={'rdf': RDF, 'obo': obo, 'owl': OWL}
    )

    # convert results to list of classes
    class_list = {str(res[1]).lower(): str(res[0]) for res in tqdm(kg_classes)
                  if isinstance(res[0], URIRef) and ont_id.lower() in str(res[0]).lower()}

    return class_list


def gets_ontology_class_synonyms(graph: Graph, ont_id: str) -> Dict:
    """Queries a knowledge graph and returns a dictionary that contains all owl:Class objects and their synonyms in the
    graph.

    Args:
        graph: An rdflib Graph object.
        ont_id: A string containing an ontology namespace.

    Returns:
        class_list: A dictionary where keys are strng synonyms and values are ontology URIs. An example is shown below:
            {'modified l selenocysteine': 'http://purl.obolibrary.org/obo/SO_0001402',
            'modified l-selenocysteine': 'http://purl.obolibrary.org/obo/SO_0001402',
            'frameshift truncation': 'http://purl.obolibrary.org/obo/SO_0001910', ...}
    """

    print('\nQuerying Knowledge Graph to Obtain all OWL:Class Nodes and Synonyms')

    # find all classes in graph
    kg_classes = graph.query(
        """SELECT DISTINCT ?c ?syn
             WHERE {
              ?c rdf:type owl:Class .
              ?c ?p ?syn .
              FILTER (CONTAINS(str(?p), "Synonym"))
              FILTER(?p in (oboInOwl:hasSynonym, oboInOwl:hasExactSynonym, oboInOwl:hasBroadSynonym, 
                            oboInOwl:hasNarrowSynonym, oboInOwl:hasRelatedSynonym))
            MINUS {?c owl:deprecated true}}
           """, initNs={'rdf': RDF, 'owl': OWL, 'oboInOwl': oboinowl})

    # convert results to list of classes
    class_list = {str(res[1]).lower(): str(res[0]) for res in tqdm(kg_classes)
                  if isinstance(res[0], URIRef) and ont_id.lower() in str(res[0]).lower()}

    return class_list


def gets_ontology_class_dbxrefs(graph: Graph, ont_id: str) -> Dict:
    """Queries a knowledge graph and returns a dictionary that contains all owl:Class objects and their database
    cross references (dbxrefs) in the graph.

    Args:
        graph: An rdflib Graph object.
        ont_id: A string containing an ontology namespace.

    Returns:
        class_list: A dictionary where keys are dbxref strings and values are ontology URIs. An example is shown below:
            {'loinc:LA6690-7': 'http://purl.obolibrary.org/obo/SO_1000002',
             'RNAMOD:055': 'http://purl.obolibrary.org/obo/SO_0001347',
             'RNAMOD:076': 'http://purl.obolibrary.org/obo/SO_0001368',
             'loinc:LA6700-2': 'http://purl.obolibrary.org/obo/SO_0001590', ...}
    """

    print('\nQuerying Knowledge Graph to Obtain all OWL:Class Nodes and DbXRefs')

    # find all classes in graph
    kg_classes = graph.query(
        """SELECT DISTINCT ?c ?dbxref
             WHERE {
              ?c rdf:type owl:Class .
              ?c oboInOwl:hasDbXref ?dbxref .
             MINUS {?c owl:deprecated true}}
           """, initNs={'rdf': RDF, 'owl': OWL, 'oboInOwl': oboinowl})

    # convert results to list of classes
    class_list = {str(res[1]): str(res[0]) for res in tqdm(kg_classes)
                  if isinstance(res[0], URIRef) and ont_id.lower() in str(res[0]).lower()}

    return class_list


def gets_deprecated_ontology_classes(graph: Graph) -> Set:
    """Queries a knowledge graph and returns a list of all deprecated owl:Class objects in the graph.

    Args:
        graph: An rdflib Graph object.

    Returns:
        class_list: A list of all of the deprecated OWL classes in the graph.

    Raises:
        ValueError: If the query returns zero nodes with type owl:Class.
    """

    print('\nQuerying Knowledge Graph to Obtain all deprecated OWL:Class Nodes')

    # find all classes in graph
    kg_classes = graph.query(
        """SELECT DISTINCT ?c
             WHERE {?c owl:deprecated true . }
        """, initNs={'owl': OWL}
    )

    # convert results to list of classes
    class_list = set([res[0] for res in tqdm(kg_classes) if isinstance(res[0], URIRef)])

    return class_list


def gets_ontology_statistics(file_location: str, owltools_location: str = './omop2obo/libs/owltools') -> None:
    """Uses the OWL Tools API to generate summary statistics (i.e. counts of axioms, classes, object properties, and
    individuals).

    Args:
        file_location: A string that contains the file path and name of an ontology.
        owltools_location: A string pointing to the location of the owl tools library.

    Returns:
        None.

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
