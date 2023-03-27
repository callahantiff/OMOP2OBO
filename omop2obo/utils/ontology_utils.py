#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ontology Utility Functions.

Ontology Entity Retrieval Functions
* gets_ontology_classes
* gets_ontology_class_labels
* gets_ontology_class_definitions
* gets_ontology_class_synonyms
* gets_ontology_class_dbxrefs
* gets_deprecated_ontology_classes
* gets_obsolete_ontology_classes

Ontology Descriptive Statistics Functions
* gets_ontology_statistics

Ontology Search Functions
* entity_search

Other Ontology Functions
* clean_uri

"""

# import needed libraries
import os
import os.path
import re
import subprocess

from more_itertools import unique_everseen  # type: ignore
from rdflib import Graph, Literal, Namespace, URIRef  # type: ignore
from rdflib.namespace import OWL, RDF, RDFS  # type: ignore
from tqdm import tqdm  # type: ignore
from typing import Dict, Generator, List, Optional, Set, Union

# set up environment variables
obo = Namespace('http://purl.obolibrary.org/obo/')
oboinowl = Namespace('http://www.geneontology.org/formats/oboInOwl#')
schema = Namespace('http://www.w3.org/2001/XMLSchema#')
skos = Namespace('http://www.w3.org/2004/02/skos/core#')


def gets_ontology_classes(graph: Graph, ont_id: str) -> Set:
    """Queries an ontology and returns a list of all non-deprecated owl:Class objects in the graph.

    Args:
        graph: An rdflib Graph object.
        ont_id: A string containing an ontology namespace.

    Returns:
        class_list: A set of all the classes in the graph.

    Raises:
        ValueError: If the query returns zero nodes with type owl:ObjectProperty.
    """

    class_list = set([x for x in graph.subjects(RDF.type, OWL.Class) if ont_id.lower() in str(x).lower()])
    if len(class_list) > 0: return class_list
    else: raise ValueError('ERROR: No classes returned from query.')


def gets_ontology_class_labels(graph: Graph, cls: Set) -> Dict:
    """Queries an ontology and returns a dictionary of all owl:Class objects and their labels in the graph.

    Args:
        graph: An rdflib Graph object.
        cls: A set of current (non-deprecated) ontology class identifiers. For example:
            {URIRef('http://purl.obolibrary.org/obo/SO_0001590)}

    Returns:
        class_list: A dictionary where keys are ontology URIs and values are string labels. An example is shown below:
            {'http://purl.obolibrary.org/obo/HP_0025019': 'arterial rupture',
            'http://purl.obolibrary.org/obo/HP_0010680': 'elevated alkaline phosphatase of renal origin',
            'http://purl.obolibrary.org/obo/HP_0008458': 'progressive congenital scoliosis', ...}
    """

    class_list = {str(x[0]): re.sub(r'[^\w\s]', '', str(x[2]).lower()) for x in graph.triples((None, RDFS.label, None))
                  if x[0] in cls and ('@' not in x[2] or '@en' in x[2])}

    return class_list


def gets_ontology_class_definitions(graph: Graph, cls: Set) -> Dict:
    """Queries an ontology and returns a dictionary that contains all owl:Class objects and their definitions.

    Args:
        graph: An rdflib Graph object.
        cls: A set of current (non-deprecated) ontology class identifiers. For example:
            {URIRef('http://purl.obolibrary.org/obo/SO_0001590)}

    Returns:
        class_list: A dictionary where keys are ontology uris and values are string definitions. An example is shown
            below:
                 {'http://purl.obolibrary.org/obo/HP_0008480': 'the presence of arthrosis, i.e., of degenerative joint
                 disease, affecting the cervical vertebral column.',
                 'http://purl.obolibrary.org/obo/HP_0001996': 'longstanding metabolic acidosis.',
                 'http://purl.obolibrary.org/obo/HP_0007811': 'nystagmus consisting of horizontal to-and-fro
                 eye movements of equal velocity.', ...}
    """

    class_list = {str(x[0]): re.sub(r'[^\w\s]', '', str(x[2]).lower())
                  for x in graph.triples((None, obo.IAO_0000115, None))
                  if x[0] in cls and ('@' not in x[2] or '@en' in x[2])}

    return class_list


def gets_ontology_class_synonyms(graph: Graph, cls: Set) -> Dict:
    """Queries an ontology and returns a tuple of dictionaries. The first dictionary contains all owl:Class
    objects and their synonyms in the graph. The second dictionary contains the synonyms and their OWL types.

    Args:
        graph: An rdflib Graph object.
        cls: A set of current (non-deprecated) ontology class identifiers. For example:
            {URIRef('http://purl.obolibrary.org/obo/SO_0001590)}

    Returns:
        A dictionary where keys are ontology uris and values are lists of tuples containing the synonym string and
        synonym type. An example is shown below:
            {'http://purl.obolibrary.org/obo/HP_0032043': [('painful swallowing', 'oboInOwl:hasExactSynonym')],
            'http://purl.obolibrary.org/obo/HP_0002692': [('underdevelopment of facial bones',
            'oboInOwl:hasBroadSynonym')], ... }
    """

    synonyms: Dict = dict()
    cls_syns = [x for x in graph if x[0] in cls and ('synonym' in str(x[1]).lower() and isinstance(x[0], URIRef))]
    for x in tqdm(cls_syns):
        cls_id = str(x[0]); syn = re.sub(r'[^\w\s]', '', str(x[2]).lower())
        syn_type = str(x[1]).split('/')[-1].replace('#', ':')
        if cls_id in synonyms.keys(): synonyms[cls_id].append(tuple([syn, syn_type]))
        else: synonyms[cls_id] = [tuple([syn, syn_type])]

    return synonyms


def gets_ontology_class_dbxrefs(graph: Graph, cls: Set) -> Optional[Dict]:
    """Queries an ontology and returns a dictionary that contains all owl:Class objects and their database
    cross-references (dbxrefs) in the graph. This function will also include concepts that have been identified as
    exact matches. The query returns a tuple of dictionaries where the first dictionary contains the dbxrefs and
    exact matches (URIs and labels) and the second dictionary contains the dbxref/exactmatch uris and a string
    indicating the type (i.e. dbxref or exact match).

    Args:
        graph: An rdflib Graph object.
        cls: A set of current (non-deprecated) ontology class identifiers. For example:
            {URIRef('http://purl.obolibrary.org/obo/SO_0001590)}

    Returns:
        dbx_uris: A dictionary where keys are ontology uris and values are a list tuples that contain a dbxref strings,
        the type of dbxref, and the namespace of the dbxref code. An example is shown below:
            {'http://purl.obolibrary.org/obo/HP_0200128': [('c0281788', 'oboInOwl:hasDbXref', 'umls')],
            'http://purl.obolibrary.org/obo/HP_0100633': [('16761005', 'oboInOwl:hasDbXref', 'snomedct_us')] ...}
    """

    dbx1 = set(graph.triples((None, oboinowl.hasDbXref, None)))
    dbx2 = set(graph.triples((None, skos.exactMatch, None)))
    dbx3 = set(graph.triples((None, skos.closeMatch, None)))
    dbx4 = set(graph.triples((None, oboinowl.hasAlternativeId, None)))
    dbxref_res = [x for x in (dbx1 | dbx2 | dbx3 | dbx4) if x[0] in cls]

    if len(dbxref_res) > 0:
        dbx_uris: Dict = dict(); k = str(list(cls)[0]).split('/')[-1].split('_')[0]
        for x in tqdm(dbxref_res):
            cls_id, dbx_type = str(x[0]), str(x[1]).split('/')[-1].replace('#', ':')
            if 'http' not in str(x[2]):
                if 'hasdbxref' in dbx_type.lower():
                    dbx, dbx_src = str(x[2]).split(':')[1], str(x[2]).lower().split(':')[0]
                elif 'exactmatch' in dbx_type.lower():
                    dbx, dbx_src = str(x[2]).split(':')[1], str(x[2]).lower().split(':')[0]
                elif 'hasalternativeid' in dbx_type.lower():
                    dbx = str(x[2]) if k in str(x[2]) else str(x[2]).split(':')[1]
                    dbx_src = str(x[2]).lower().split(':')[0]
                else: continue
                # add identified cross-reference to dictionary
                if cls_id in dbx_uris.keys(): dbx_uris[cls_id].append(tuple([dbx, dbx_type, dbx_src]))
                else: dbx_uris[cls_id] = [tuple([dbx, dbx_type, dbx_src])]
        return dbx_uris

    else: return None


def gets_deprecated_ontology_classes(graph: Graph, ont_id: str) -> Set:
    """Obtains a list of all deprecated owl:Class objects in an ontology.

    Args:
        graph: An rdflib Graph object.
        ont_id: A string containing an ontology namespace (e.g., "hp").

    Returns:
        class_list: A list of all the deprecated OWL classes in the graph.
    """

    # find all deprecated classes in graph
    dep_classes = list(graph.subjects(OWL.deprecated, Literal('true', datatype=URIRef(schema + 'boolean'))))
    class_list = set([x for x in dep_classes if ont_id.lower() in str(x).lower()])

    return class_list


def gets_obsolete_ontology_classes(graph: Graph, ont_id: str) -> Set:
    """Obtains a list of all obsolete owl:Class objects in an ontology.

    Args:
        graph: An rdflib Graph object.
        ont_id: A string containing an ontology namespace (e.g., "hp").

    Returns:
        class_list: A list of all the obsolete OWL classes in the graph.
    """

    # find all deprecated classes in graph
    obs_classes = list(graph.subjects(RDFS.subClassOf, oboinowl.ObsoleteClass))
    class_list = set([x for x in obs_classes if ont_id.lower() in str(x).lower()])

    return class_list


def gets_ontology_statistics(file_location: str, owltools_location: str = './omop2obo/libs/owltools') -> str:
    """Uses the OWLTools API to generate summary statistics for a downloaded OWL ontology.

    Args:
        file_location: A string that contains the file path and name of an ontology.
        owltools_location: A string pointing to the location of the owl tools library.

    Returns:
        A string containing ontology statistics.

    Raises:
        TypeError: If the file_location is not type str.
        OSError: If file_location points to a non-existent file.
        ValueError: If file_location points to an empty file.
    """

    # verify file before processing
    if not isinstance(file_location, str): raise TypeError('ERROR: file_location must be a string')
    elif not os.path.exists(file_location): raise OSError('The {} file does not exist!'.format(file_location))
    elif os.stat(file_location).st_size == 0: raise ValueError('FILE ERROR: file: {} is empty'.format(file_location))
    else: output = subprocess.check_output([os.path.abspath(owltools_location), file_location, '--info'])

    # print stats
    res = output.decode('utf-8').split('\n')[-5:]
    cls, axs, op, ind = res[0].split(':')[-1], res[3].split(':')[-1], res[2].split(':')[-1], res[1].split(':')[-1]
    sent = 'The ontology contains {0} classes, {1} axioms, {2} object properties, and {3} individuals'

    return sent.format(cls, axs, op, ind)


def clean_uri(entity_list: Generator) -> List:
    """Ensures that a Generator contains only RDFLib URIRef objects.

    Args:
        entity_list: A Generator of RDFLib Graph objects.

    Returns:
        cleaned_entity_list: A list of cleaned RDFLib URIRef objects.
    """

    cleaned_entity_list = [entity for entity in entity_list if isinstance(entity, URIRef)]

    return cleaned_entity_list


def entity_search(graph: Graph, uri: Union[URIRef, str], search_type: str = 'ancestors',
                  filtered_search: Optional[str] = None, rel: Union[URIRef, str] = RDFS.subClassOf) -> Optional[Dict]:
    """Recursively searches an ontology hierarchy to pull all ancestor or children concepts for an input entity. The
    function returns a nested dictionary where the outer keys are ontology URIs and the inner dictionary keys are
    string levels, where each level is a number (0-N) that represents the distance in the hierarchy from the class
    and the values contain lists of URLs for classes at that level.

    Args:
        graph: An RDFLib graph object assumed to contain ontology data.
        uri: A list of at least one ontology RDFLib URIRef object or string.
        search_type: A string specifying whether ancestors or children should be returned.
        filtered_search: A value that specifies whether the search should remove classes that are not from the
            ontology namespace (i.e., only include HP concepts when search HPO). If None (default), all ontology
            classes ancestors/descendants will be returned.
        rel: A string or RDFLib URI object containing a predicate.

    Returns:
        entities: A dictionary where the keys are levels (0-N) as and values are lists of urls.

    Example output for HP_0003743:
        Ancestors: {'0':  ['http://purl.obolibrary.org/obo/HP_0000005'],
                    '1': ['http://purl.obolibrary.org/obo/HP_0000001']}
        Children: {'0':  ['http://purl.obolibrary.org/obo/HP_0003744']}
    """

    if search_type not in ['ancestors', 'children']: raise ValueError('search_type must be "ancestors" or "children"')
    prop = rel if isinstance(rel, URIRef) else URIRef(rel); uri = uri if isinstance(uri, URIRef) else URIRef(uri)
    node_level: Dict = dict(); ents: Dict = dict(); master: Set = set(); level_list = list()
    if search_type == 'ancestors': uris = [('0', x) for x in list(unique_everseen(clean_uri(graph.objects(uri, prop))))]
    else: uris = [('0', x) for x in list(unique_everseen(clean_uri(graph.subjects(prop, uri))))]
    if filtered_search is not None: uris = [x for x in uris if filtered_search in str(x[1])]

    if len(uris) == 0: return None
    else:
        while len(uris) != 0:
            level, node = uris.pop(0); master |= {node}
            if search_type == 'ancestors': entities_ids = list(unique_everseen(clean_uri(graph.objects(node, prop))))
            else: entities_ids = list(unique_everseen(clean_uri(graph.subjects(prop, node))))
            if filtered_search is not None: entities_ids = [x for x in entities_ids if filtered_search in str(x)]
            if len(entities_ids) == 0 and len(uris) == 0:
                if node in node_level.keys(): node_level[node] += [level]
                else: node_level[node] = [level]
            else:
                if node in node_level.keys(): node_level[node] += [level]
                else: node_level[node] = [level]
                uris = list(unique_everseen(uris + [(str(int(level) + 1), x) for x in entities_ids]))
            level_list += [int(level), int(level) + 1]
        # update hierarchy level for each node
        level_list = sorted(set(level_list))
        for k, v in node_level.items():
            level = str(sorted([int(i) for i in v])[-1])
            if level in ents.keys(): ents[level].append(str(k)); ents[level] = list(unique_everseen(ents[level]))
            else: ents[level] = [str(k)]
        if sorted([int(i) for i in ents.keys()]) == list(range(level_list[0], level_list[-1])): return ents
        else: raise ValueError('ERROR!!!')
