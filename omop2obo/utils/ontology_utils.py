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
from rdflib import Graph, URIRef  # type: ignore
from rdflib.namespace import RDF, OWL  # type: ignore
import subprocess

from tqdm import tqdm  # type: ignore
from typing import Set


def gets_ontology_classes(graph: Graph) -> Set:
    """Queries a knowledge graph and returns a list of all owl:Class objects in the graph.

    Args:
        graph: An rdflib Graph object.

    Returns:
        class_list: A list of all of the classes in the graph.

    Raises:
        ValueError: If the query returns zero nodes with type owl:ObjectProperty.
    """

    print('\nQuerying Knowledge Graph to Obtain all OWL:Class Nodes')

    # find all classes in graph
    kg_classes = graph.query(
        """SELECT DISTINCT ?c
             WHERE {?c rdf:type owl:Class . }
        """, initNs={'rdf': RDF, 'owl': OWL}
    )

    # convert results to list of classes
    class_list = set([res[0] for res in tqdm(kg_classes) if isinstance(res[0], URIRef)])

    if len(class_list) > 0:
        return class_list
    else:
        raise ValueError('ERROR: No classes returned from query.')


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
