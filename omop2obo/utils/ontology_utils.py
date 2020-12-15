#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ontology Utility Functions.

Interacts with OWL Tools API
* gets_ontology_statistic
* merges_ontologies
* ontology_file_formatter

Obtains Graph Information
* cleans_ontology
* gets_ontology_classes
* gets_ontology_class_labels
* gets_ontology_class_definitions
* gets_ontology_class_synonyms
* gets_ontology_class_dbxrefs
* gets_deprecated_ontology_classes
* finds_class_ancestors

"""

# import needed libraries
import glob
import os
import os.path
from rdflib import Graph, Literal, Namespace, URIRef  # type: ignore
from rdflib.namespace import OWL, RDF, RDFS  # type: ignore
import subprocess

from tqdm import tqdm  # type: ignore
from typing import Dict, List, Optional, Set, Tuple, Union

# set up environment variables
obo = Namespace('http://purl.obolibrary.org/obo/')
oboinowl = Namespace('http://www.geneontology.org/formats/oboInOwl#')
schema = Namespace('http://www.w3.org/2001/XMLSchema#')


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


def merges_ontologies(ontology_files: List[str], write_location: str, merged_ont_kg: str,
                      owltools_location: str = './omop2obo/libs/owltools') -> Optional[Graph]:
    """Using the OWLTools API, each ontology listed in in the ontologies attribute is recursively merged with into a
    master merged ontology file and saved locally to the provided file path via the merged_ontology attribute. The
    function assumes that the file is written to the directory specified by the write_location attribute.

    Args:
        ontology_files: A list of ontology file paths.
        write_location: A string pointing to a local directory for writing data.
        merged_ont_kg: A string pointing to the location of the merged ontology file.
        owltools_location: A string pointing to the location of the owl tools library.

    Returns:
        None.
    """

    if not ontology_files:
        return None
    else:
        if write_location + merged_ont_kg in glob.glob(write_location + '/*.owl'):
            ont1, ont2 = ontology_files.pop(), write_location + merged_ont_kg
        else:
            ont1, ont2 = ontology_files.pop(), ontology_files.pop()

        try:
            print('\nMerging Ontologies: {ont1}, {ont2}'.format(ont1=ont1.split('/')[-1], ont2=ont2.split('/')[-1]))
            # call to OWL API to merge ontologies
            subprocess.check_call([os.path.abspath(owltools_location), str(ont1), str(ont2),
                                   '--merge-support-ontologies',
                                   '-o', write_location + merged_ont_kg])
        except subprocess.CalledProcessError as error:
            print(error.output)

        return merges_ontologies(ontology_files, write_location, merged_ont_kg)


def ontology_file_formatter(write_location: str, full_kg: str,
                            owltools_location: str = './omop2obo/libs/owltools') -> None:
    """Reformat an .owl file to be consistent with the formatting used by the OWL API. To do this, an ontology
    referenced by graph_location is read in and output to the same location via the OWLTools API.

    Args:
        write_location: A string pointing to a local directory for writing data.
        full_kg: A string containing the subdirectory and name of the the knowledge graph file.
        owltools_location: A string pointing to the location of the owl tools library.

    Returns:
        None.

    Raises:
        TypeError: If something other than an .owl file is passed to function.
        IOError: If the graph_location file is empty.
        TypeError: If the input file contains no data.
    """

    print('Applying OWL API Formatting to Ontology OWL File')
    graph_write_location = write_location + full_kg

    # check input owl file
    if '.owl' not in graph_write_location:
        raise TypeError('ERROR: The provided file is not type .owl')
    elif not os.path.exists(graph_write_location):
        raise IOError('The {} file does not exist!'.format(graph_write_location))
    elif os.stat(graph_write_location).st_size == 0:
        raise TypeError('ERROR: input file: {} is empty'.format(graph_write_location))
    else:
        try:
            subprocess.check_call([os.path.abspath(owltools_location),
                                   graph_write_location,
                                   '-o', graph_write_location])
        except subprocess.CalledProcessError as error:
            print(error.output)

    return None


def cleans_ontology(ontology: Graph, onts: List) -> Graph:
    """Method cleans a single ontology or merged set of ontologies to remove all deprecated and obsolete information.

    Args:
        ontology: An RDFLib Graph object containing ontology data.
        onts: A list of ontology prefixes.

    Returns:
        ontology: An updated RDFLib Graph object with all obsolete and deprecated information removed.
    """

    print('Cleaning Ontology')
    ont_updated = [x if x != 'ext' else 'uberon' for x in onts]
    ont_prefix = ['http://purl.obolibrary.org/obo/' + ont.upper() for ont in ont_updated]

    # get deprecated classes and triples
    dep_cls = [x[0] for x in list(ontology.triples((None, OWL.deprecated, Literal('true', datatype=schema.boolean))))]
    dep_triples = [(s, p, o) for s, p, o in ontology
                   if 'deprecated' in ', '.join([str(s).lower(), str(p).lower(), str(o).lower()])
                   and any(str(s).startswith(ont) for ont in ont_prefix)]
    oth_dep_triple_classes = [x[0] for x in dep_triples]
    deprecated_classes = set(dep_cls + oth_dep_triple_classes)

    # get obsolete classes and triples
    obs_cls = [x[0] for x in list(ontology.triples((None, RDFS.subClassOf, oboinowl.ObsoleteClass)))]
    obs_triples = [(s, p, o) for s, p, o in ontology if 'OBSOLETE:' in ', '.join([str(s), str(o)])]
    oth_obs_triple_classes = [x[0] for x in obs_triples]
    obsolete_classes = set(obs_cls + oth_obs_triple_classes)

    # remove deprecated/obsolete classes and triples
    for node in list(deprecated_classes) + list(obsolete_classes):
        ontology.remove((node, None, None))  # remove all triples about node
        ontology.remove((None, None, node))  # remove all triples pointing to node
    for triple in dep_triples + obs_triples:
        ontology.remove(triple)

    return ontology


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
    """

    print('Querying Knowledge Graph to Obtain all Deprecated OWL:Class Nodes')

    # find all deprecated classes in graph
    dep_classes = list(graph.subjects(OWL.deprecated, Literal('true', datatype=URIRef(schema + 'boolean'))))
    class_list = set([x for x in dep_classes if ont_id.lower() in str(x).lower()])

    return class_list


def gets_class_ancestors(graph: Graph, class_uris: List[Union[URIRef, str]], class_list: Optional[List] = None) -> List:
    """A method that recursively searches an ontology hierarchy to pull all ancestor concepts for an input class.

    Args:
        graph: An RDFLib graph object assumed to contain ontology data.
        class_uris: A list of at least one ontology class RDFLib URIRef object.
        class_list: A list of URIs representing the ancestor classes found for the input class_uris.

    Returns:
        A list of ontology class ordered by the ontology hierarchy.
    """

    # instantiate list object if none passed to function
    class_list = [] if class_list is None else class_list

    # check class uris are formatted correctly
    class_uris = [x if isinstance(x, URIRef) else URIRef('http://purl.obolibrary.org/obo/' + x) for x in class_uris]

    # gets ancestors
    ancestor_classes = [j for k in [list(graph.objects(x, RDFS.subClassOf)) for x in class_uris] for j in k]

    if len(ancestor_classes) == 0:
        return [str(x) for x in class_list][::-1]
    else:
        class_list += ancestor_classes
        return gets_class_ancestors(graph, ancestor_classes, class_list)
