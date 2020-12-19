#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import glob  # type: ignore
import os
import pandas as pd  # type: ignore
import pickle  # type: ignore
import re
import regex  # type: ignore

from abc import ABCMeta, abstractmethod
from datetime import date, datetime  # type: ignore
from more_itertools import unique_everseen  # type: ignore
from rdflib import BNode, Graph, Literal, Namespace, URIRef  # type: ignore
from rdflib.namespace import OWL, RDF, RDFS  # type: ignore
from tqdm import tqdm  # type: ignore
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from omop2obo.utils import *


# set up environment variables
obo = Namespace('http://purl.obolibrary.org/obo/')
oboinowl = Namespace('http://www.geneontology.org/formats/oboInOwl#')
omop2obo = Namespace('https://github.com/callahantiff/omop2obo/')
skos = Namespace('http://www.w3.org/2004/02/skos/core#')


class SemanticTransformer(object):
    __metaclass__ = ABCMeta

    def __init__(self, ontology_list: List, omop2obo_data_file: str, domain: str, map_type: str = 'multi',
                 ontology_directory: Optional[str] = None, superclasses: Optional[Dict] = None,
                 primary_column: str = 'CONCEPT', secondary_column: Optional[str] = None,
                 root_directory: Optional[str] = None) -> None:

        """This class is designed to facilitate the transformation of OMOP2OBO mappings into semantic
        representations. To do this, the class includes several methods that assist with processing different aspects
        of the mapping data. The class currently enables two types of mappings to be created: (1) Single. A single
        mapping processes each OMOP2OBO mapping by ontology, within that ontology; (2) Multi. A multi mapping first
        merges all relevant ontologies and then constructs new OMOP2OBO classes that span multiple ontologies.

        For additional information on this approach please see the dedicated project wiki page:
            https://github.com/callahantiff/OMOP2OBO/wiki/Semantic-Mapping-Representation

        Attributes:
            ontology_list: A list of ontology identifiers (i.e. ['HP', 'MONDO']).
            omop2obo_data_file: A Pandas DataFrame containing OMOP2OBO mapping data. Assumes that the mapping data is
                stored in an xlsx file sheet called "Aggregated_Mapping_Results" and that no additional filtering or
                preprocessing is needed.
                needed
            ontology_directory: A string pointing to a directory that contains OWL ontology files.
            domain: A string specifying the clinical domain. Must be "condition", "measurement", or "drug".
            map_type: A string indicating whether to build single (i.e. 'single') or multi-ontology (i.e. 'multi')
                classes. The default type is "multi".
           superclasses: A dictionary where keys are clinical domains and values are either a dictionary or a URIRef
                object. For example:
                    {'condition': {'phenotype': URIRef('http://purl.obolibrary.org/obo/HP_0000118'),
                                    'disease': URIRef('http://purl.obolibrary.org/obo/MONDO_0000001')},
                                    'drug': URIRef('http://purl.obolibrary.org/obo/CHEBI_24431'),
                                    'measurement': URIRef('http://purl.obolibrary.org/obo/HP_0000118')}}
           primary_column: A string containing a keyword used to retrieve relevant columns (default="CONCEPT").
           secondary_column: A string containing a keyword used to retrieve relevant columns for the secondary set of
                OMOP concept_ids used in the mappings. This is an optional parameter. OMOP2OBO drug mappings use both
                the secondary and primary columns. In this example, the primary columns are used for ingredient data
                and the secondary columns are used for the drugs that map to each ingredient.

        Returns:
            None.
        """

        # CREATE CLASS ATTRIBUTES
        self.root = os.path.abspath(root_directory) if root_directory is not None else 'resources'
        self.graph: Graph = Graph()
        self.owltools_location = os.path.abspath('omop2obo/libs/owltools')
        self.write_location = self.root + '/mapping_semantics'
        self.timestamp = '_' + datetime.strftime(datetime.strptime(str(date.today()), '%Y-%m-%d'), '%d%b%Y').upper()
        self.ontology_data_dict: Dict = {}

        # EXISTING OMOP2OBO OWL FILE
        existing_mappings = glob.glob(self.write_location + '/omop2obo*.owl')
        self.current_omop2obo = None if len(existing_mappings) == 0 else existing_mappings[0]

        # ONTOLOGY LIST
        if not isinstance(ontology_list, List):
            raise TypeError('ontology_list must be type str')
        elif len(ontology_list) == 0:
            raise ValueError('ontology_list cannot be an empty list')
        else:
            self.ontologies = ontology_list

        # OMOP2OBO MAPPING DATA
        if not isinstance(omop2obo_data_file, str):
            raise TypeError('omop2obo_data_file must be type str.')
        elif not os.path.exists(omop2obo_data_file):
            raise OSError('The {} file does not exist!'.format(omop2obo_data_file))
        elif os.stat(omop2obo_data_file).st_size == 0:
            raise TypeError('Input file: {} is empty'.format(omop2obo_data_file))
        else:
            print('Loading Mapping Data')
            self.omop2obo_data = pd.read_excel(omop2obo_data_file, header=0, engine='openpyxl')
            self.omop2obo_data.fillna('N/A', inplace=True)

        # CLINICAL DOMAIN
        if not isinstance(domain, str):
            raise TypeError('domain must be type str.')
        elif domain.lower() not in ['condition', 'drug', 'measurement']:
            raise ValueError('domain must be one of following string: "condition", "drug", or "measurement"')
        else:
            self.domain = domain.lower()

        # ONTOLOGY DIRECTORY
        onts = '/ontologies' if ontology_directory is None else ontology_directory
        ont_data = glob.glob(onts + '/*.owl')
        if not os.path.exists(onts):
            raise OSError("Can't find 'ontologies/' directory, this directory is a required input")
        elif len(ont_data) == 0:
            raise TypeError('The ontologies directory is empty')
        else:
            # check for ontology data -- adds check for 'ext' to handle the fact that the uberon file is called 'ext'
            ont_list = [y.lower() if y.lower() != 'uberon' else 'ext' for y in self.ontologies]
            ont_check = [x for x in ont_data if x.split('/')[-1].split('_')[0] in ont_list]
            if len(ont_check) == 0:
                raise ValueError('No ontology owl files match provided ontology list')
            else:
                self.ont_directory = ont_check

        # CLASS CONSTRUCTION TYPE
        if not isinstance(map_type, str):
            raise TypeError('map_type must be type string')
        else:
            self.construction_type = 'single' if map_type != 'multi' else map_type

        # check subclass dict input
        if self.construction_type == 'multi':
            if superclasses is None:
                self.superclass_dict: Optional[Dict] = {
                    'condition': {'phenotype': URIRef('http://purl.obolibrary.org/obo/HP_0000118'),
                                  'disease': URIRef('http://purl.obolibrary.org/obo/MONDO_0000001')},
                    'drug': URIRef('http://purl.obolibrary.org/obo/CHEBI_24431'),
                    'measurement': URIRef('http://purl.obolibrary.org/obo/HP_0000118')}
            else:
                if not isinstance(superclasses, Dict):
                    raise TypeError('superclasses must be type Dict')
                else:
                    self.superclass_dict = superclasses
        else:
            self.superclass_dict = None

        # RO RELATIONS FOR MULTI-ONTOLOGY CLASSES
        if self.construction_type == 'multi':
            rel_data_loc = self.write_location + '/omop2obo_class_relations.txt'
            if not os.path.exists(rel_data_loc):
                raise OSError('The {} file does not exist!'.format(rel_data_loc))
            elif os.stat(rel_data_loc).st_size == 0:
                raise TypeError('Input file: {} is empty'.format(rel_data_loc))
            else:
                print('Loading Multi-Ontology Class Construction Relations')
                self.multi_class_relations: Optional[Dict] = {}
                with open(rel_data_loc, 'r') as f:
                    for x in f.read().splitlines()[1:]:
                        row = [i.strip() for i in x.split(',')]
                        key = row[1] + '-' + row[3]
                        if row[0] in self.multi_class_relations.keys():
                            self.multi_class_relations[row[0]]['relations'][key] = URIRef(row[2])
                        else:
                            self.multi_class_relations[row[0]] = {'relations': {}}
                            self.multi_class_relations[row[0]]['relations'] = {key: URIRef(row[2])}
                f.close()
        else:
            self.multi_class_relations = None

        # ONTOLOGY DICTIONARY
        if self.construction_type == 'multi':
            ont_dictionary = self.root + '/ontologies/master_ontology_dictionary.pickle'
            if not os.path.exists(ont_dictionary):
                raise OSError("Can't find master_ontology_dictionary.pickle please re-run the process ontology steps.")
            elif os.stat(ont_dictionary).st_size == 0:
                raise TypeError('Input file: {} is empty'.format(ont_dictionary))
            else:
                with open(ont_dictionary, 'rb') as handle:
                    self.ontology_metadata: Optional[Dict] = pickle.load(handle)
                handle.close()
        else:
            self.ontology_metadata = None

        # MAPPING COLUMNS
        if primary_column != 'CONCEPT':
            if not isinstance(primary_column, str):
                raise TypeError('primary_column must be type string')
            else:
                self.primary_column: str = primary_column.upper()
        else:
            self.primary_column = primary_column.upper()

        if secondary_column is not None:
            if not isinstance(secondary_column, str):
                raise TypeError('secondary_column must be type string')
            else:
                self.secondary_column: Optional[str] = secondary_column.upper()
        else:
            self.secondary_column = secondary_column

    def loads_ontology_data(self) -> Dict:
        """Method iterates over each ontology in the ontologies attribute and loads them as RDFLib Graph objects. For
        both "single" and "multi" class construction_types the ontology prefixes are used as dictionary keys and the
        RDFLib Graph objects are the values. If the construction_type is "multi" then an additional key is added to
        the dictionary where the value contains all of the ontologies merged together. For either

        Returns:
            ontology_data_dict:A dictionary containing ontology data. If construction_type is "single" or "multi" then
                the keys correspond to the entries in ontology_list and values are RDFLib Graph objects. If the
                construction_type is "multi" then an additional key is added to store the merged ontology data.
        """

        ontology_data: Dict = {}
        write_loc = os.path.relpath('/'.join(self.ont_directory[0].split('/')[:-1]))
        if self.construction_type == 'single':
            for ont in self.ontologies:
                print('Loading: {}'.format(ont.upper()))
                ont_data = 'ext' if ont == 'uberon' else ont
                ont_file = [x for x in self.ont_directory if ont_data in x][0]
                ontology_graph = Graph().parse(ont_file, format='xml')
                ontology_data[ont] = cleans_ontology(ontology_graph, [ont])
        else:  # merge all relevant ontologies and add to ontology_data dictionary
            omop2obo_merged_filepath = '/OMOP2OBO_MergedOntologies' + self.timestamp + '.owl'
            merges_ontologies(self.ont_directory, write_loc, omop2obo_merged_filepath, self.owltools_location)
            print('Loading merged ontology data: {}'.format(write_loc + omop2obo_merged_filepath))
            ontology_graph = Graph().parse(write_loc + omop2obo_merged_filepath, format='xml')
            ontology_data['merged'] = cleans_ontology(ontology_graph, self.ontologies)

        return ontology_data

    def gets_concept_id_data(self, row: pd.Series) -> Dict:
        """Takes a row of data from the omop2obo_data object and from that row creates a dictionary which contains
        data from columns that correspond to the primary_column and secondary_column class attributes. An example is
        shown under the Returns section below.

        Args:
            row: A Pandas Series containing a row of data from the omop2obo_data object.

        Returns:
            row_dict_data: A nested dictionary of data for a row from the omop2obo_data object. The outer dictionary
                is an omop concept id and the inner keys are 'primary_column' and 'secondary_column', where the values
                are dictionaries containing values for each data type. An example is shown below:
                    {27526:
                        'primary_key':
                            {'CONCEPT_LABEL': "Nezelof's syndrome", 'CONCEPT_SYNONYMS': "Nezelof's syndrome (disorder)",
                             'CONCEPT_VOCAB': 'SNOMED', 'CONCEPT_VOCAB_VERSION': 'SnomedCT Release 20180131',
                             'CONCEPT_SOURCE_CODE': 55602000, 'CONCEPT_CUI': 'C0152094',
                             'CONCEPT_SEMANTIC_TYPE': 'Disease or Syndrome'}
                        'secondary_data': None}
        """

        row_dict_data = {row[self.primary_column + '_ID']: {'primary_data': None, 'secondary_data': None}}
        # extract primary data as a dictionary
        primary_data = row[[x for x in row.keys() if x.startswith(self.primary_column)]].to_dict()
        row_dict_data[row[self.primary_column + '_ID']]['primary_data'] = primary_data
        # extract secondary data
        if self.secondary_column is not None:
            secondary_data = row[[x for x in row.keys() if x.startswith(self.primary_column)]].to_dict()
            row_dict_data[row[self.primary_column + '_ID']]['secondary_data'] = secondary_data

        return row_dict_data

    @staticmethod
    def orders_constructors(logic: str, result: List) -> List:
        """Method takes a logic string and a set of preprocessed logic lists and returns a list of the OWL constructors
        used in the logic string ordered by most inner to outer parentheses. An example is provided below:

        Example:
            input: 'OR(AND(0, 1, 2, 3), OR(AND(0, 1, 2), 3))'
            output: ['AND', 'AND', 'OR', 'OR']

        Args:
            logic: A string containing the OWL constructor logic and indexes (e.g. 'AND(0, OR(1, 2))').
            result: A list of pre-processed logical stubs representing the information extracted from logic string.

        Returns:
            constructors: A list of ordered OWL constructors.
        """

        constructors: List = []
        while len(result) != 0:
            res = result.pop(0)
            # find result in logic string
            formatted_stub = res.replace('(', '\\(').replace(')', '\\)').replace(',', '\\,').replace(' ', '\\s')
            matches = re.findall(r'[A-Z]{2,3}(?=' + formatted_stub + ')', logic)
            # update hits for all matches and decrements result list
            for match in matches:
                constructors += [match]
                if res in result: result.remove(res)

        return constructors

    @staticmethod
    def extracts_logic(logic: str, result: List, constructors: List, uri_info: Optional[List] = None) -> List:
        """Recursively parses a string containing logical constructor information (e.g. "AND(0,OR(1, 2))") with the
        goal of extracting each OWL constructor and the URI indexes it points to. The method returns a list of
        lists, where each inner list contains an OWL constructor and it's indexes or other OWL constructors if the logic
        string contains several chained constructors (e.g. "AND(OR(0, 1) ,OR(2, 3))").

        Args:
            logic: A string containing a logic statement that is updated on each run of the method.
            result: A list of all logic chunks extracted from the logic string.
            constructors: A list of OWL constructors (e.g. ['AND', 'OR']).
            uri_info: A nested list of OWL constructors and URI indexes (details on item under Returns). This is an
                optional parameter.

        Returns:
            uri_info: A nested list of OWL constructors and URI indexes. In each inner list there are two items
            where
                the first item contains a string representing an OWL constructor and the second item contains a
                comma-delimited string of URI indexes.
        """

        uri_info = [] if uri_info is None else uri_info

        if (constructors is None or len(constructors) == 0) and (result is None or len(result) == 0) or logic == 'N/A':
            return list(unique_everseen(uri_info))
        elif len(result) == 1 and len(constructors) == 1:  # processes most outer logic parentheses
            # check if statement only contains indexes (i.e. '(0, 2)') or a mix of indexes and OWL constructors
            const, inner = constructors.pop(0), finds_nonoverlapping_span_indexes(logic)
            if not any(x for x in ['AND', 'OR', 'NOT'] if x in result[0]): pattern = r'\d,\s.+(?=\)$)|\d'
            else: pattern = r'(?<=^\()\d.*?(?=\,\s[A-z])|(?<=\),\s)\d.*?(?=\,\s[A-z])|(?<=\,\s)[^\).]+(?=\)$)'
            extract = re.findall(pattern, result[0])  # returns empty list if no indexes in outer (), str if there is
            if len(extract) == 0: uri_info.append([const, ', '.join(inner)])  # when no index in outer ()s
            else: uri_info.append([const, ', '.join(extract + inner)])  # when outer () contains mixed data

            return SemanticTransformer.extracts_logic(logic, [], constructors, uri_info)
        else:
            # find constructor's statement
            const = constructors.pop(0)
            match = [(x, re.findall(const + re.sub(r'[\\(]', '\\(', x).replace(r')', '\\)'), logic)) for x in result]
            substr, filtered_match = [(x[0], x[1][0]) for x in match if len(x[1]) > 0][0]
            result.remove(substr)
            if not any(x for x in ['AND', 'OR', 'NOT'] if x in substr):  # extract const's content (e.g. '2' in NOT(2))
                idx = re.sub(r'[\\(|)]', '', substr)
            else:
                for x in [y for y in uri_info if y[0] + '(' + y[1] + ')' in filtered_match]:
                    str_idx = str(logic.index('{}({})'.format(x[0], x[1])))
                    substr = substr.replace(r'{}({})'.format(x[0], x[1]), x[0] + '-' + str_idx)
                idx = re.sub(r'(?<=[A-z])\(.*?\)|[\\()]', '', substr)
            uri_info.append([const, idx + ')' if '(' in idx and ')' not in idx else idx])

            return SemanticTransformer.extracts_logic(logic, result, constructors, uri_info)

    @staticmethod
    def complement_of_constructor(uri: str) -> Tuple:
        """Method takes a string containing an ontology identifier and returns a nested list of triples needed to
        create a OWL:complementOf semantic definition.

        Args:
            uri: A string containing an ontology identifier (e.g. 'MONDO_0001933').

        Returns:
            triples: A tuple, where the first item is a BNode that is needed to link the list of tuples, stored as the
                second item in the tuple, to other types of important metadata.
        """

        if not isinstance(uri, str): raise TypeError('OWL:complementOf constructors requires a single URI input.')
        else: triples = [(BNode('N' + str(uuid4().hex)), OWL.complementOf, uri)]

        return triples[0][0], triples

    @staticmethod
    def other_owl_constructor(uris: List, constructor: URIRef) -> Tuple:
        """Method takes a list of ontology identifiers and returns a nested list of triples needed to create an
        OWL:unionOf or OWL:intersectionOf semantic definition using the input URIs.

        Args:
            uris: A comma-separated list of ontology identifiers (e.g. ['HP_0004430', 'HP_0000007']).
            constructor: A URIRef object containing with the OWL:intersectionOf or OWL:unionOf constructors.

        Returns:
            triples: A tuple, where the first item is a BNode that is needed to link the list of tuples,
                stored as the second item in the tuple, to other types of important metadata.
        """

        if len(uris) < 2:
            raise ValueError('OWL:unionOf and OWL:intersectionOf constructors require at least 2 ontology identifiers.')
        else:
            uuid_constructor = BNode('N' + str(uuid4().hex))
            member_nodes = [BNode('N' + str(uuid4().hex)) for _ in range(len(uris))]
            triples: List = []
            # assemble class triples
            uuid_list = [uuid_constructor] + member_nodes
            for uri in uris:
                prior, current = uuid_list.pop(0), uuid_list[0]
                if uri == uris[0]: triples += [(prior, constructor, current), (current, RDF.first, uri)]
                elif uri != uris[-1]: triples += [(prior, RDF.rest, current), (current, RDF.first, uri)]
                else: triples += [(prior, RDF.rest, current), (current, RDF.first, uri), (current, RDF.rest, RDF.nil)]

            return uuid_constructor, triples

    @staticmethod
    def class_constructor(logic: str, logic_info: List, span: List, uri: List, triples: Optional[Dict] = None) -> Tuple:
        """Method is the primary directive which guides the transformation of each mapping into a semantic
        definition. This is done in the following four steps:

        Args:
            logic: A string containing a logic statement that is updated on each run of the method.
            logic_info: A nested list of OWL constructors and URI indexes. In each inner list there are two items where
                the first item contains a string representing an OWL constructor and the second item contains a
                comma-delimited string of URI indexes. This list is decremented with each loop.
            span: A nested list of logic spans from the original regular expression data. For example, if the logic
                str is 'AND(0, 1, 2, 3)' --> [['AND', '0, 1, 2, 3']]
            uri: A list of URIs needed to construct semantic definitions for a given mapping.
            triples: A nested list of constructed triples. The first item in the list is the RDFLib BNode used to link
                a set of triples to important class metadata (e.g. OMOP2OBO namespace identifier and label).

        Returns:
            triples: A tuple, where the first item is a BNode that is needed to link the list of tuples, stored as the
                second item in the tuple, to other types of important metadata.
        """

        triples = {'full_set': [], 'bridge_node': None} if triples is None else triples

        if len(logic_info) == 0:  # add heading triples (i.e. restriction, which accompanies all triple sets)
            uuid_key = BNode('N' + str(uuid4().hex))
            triples = [(uuid_key, RDF.type, OWL.Restriction), (uuid_key, OWL.onProperty, URIRef(obo + 'BFO_0000051')),
                       (uuid_key, OWL.someValuesFrom, triples['bridge_node']),
                       (triples['bridge_node'], RDF.type, OWL.Class)] + triples['full_set']

            return uuid_key, triples
        else:
            const, uri_idx = logic_info.pop(0)
            span_data = span.pop(0)
            uri_info = [triples[x] if x.split('-')[0] in ['AND', 'OR', 'NOT'] else URIRef(obo + uri[int(x)])
                        for x in uri_idx.split(', ')]
            # obtain constructor triples
            if const == 'AND': triple = SemanticTransformer.other_owl_constructor(uri_info, OWL.intersectionOf)
            elif const == 'OR': triple = SemanticTransformer.other_owl_constructor(uri_info, OWL.unionOf)
            else: triple = SemanticTransformer.complement_of_constructor(uri_info[0])
            # update triple dictionary
            triples['bridge_node'], triples[const + '-' + str(logic.index(const + span_data))] = triple[0], triple[0]
            triples['full_set'] = triple[1] + triples['full_set']

        return SemanticTransformer.class_constructor(logic, logic_info, span, uri, triples)

    def adds_class_metadata(self, class_info: Dict, ont: str, data_level: str) -> List:
        """Adds important metadata to triples output after running the class_constructor method. The method adds class
        identifier information (i.e. namespace, type, and label) and a domain-specific triple (only for multi
        construction types).

        Args:
            class_info: A nested dictionary with three primary keys (i.e. "primary_data", "secondary_data", and
                ontologies (e.g. "hp", "mondo"). The primary_data and secondary_data contains clinical data and the
                ontology dictionary contains the triples information for the class.
            ont: A string specifying an ontology prefix (e.g. "hp" or "mondo").
            data_level: A string, either "primary_data" or "secondary_data", indicating what level of data to process

        Returns:
            A list of modified triples for the input dictionary that has been extended to include identifier,
                namespace, and label information in addition to domain superclass content.
        """

        # preprocess data for use
        triples, keys = class_info[ont]['triples'], list(class_info[data_level].keys())
        primary_id = 'OMOP_' + str(class_info[data_level][[x for x in keys if 'ID' in x][0]])
        primary_label = class_info[data_level][[x for x in keys if 'LABEL' in x][0]]
        # add identifier information
        identifiers = [(URIRef(omop2obo + primary_id), URIRef(oboinowl + 'hasOBONamespace'), Literal('OMOP2OBO')),
                       (URIRef(omop2obo + primary_id), URIRef(oboinowl + 'id'), Literal(primary_id.replace('_', ':'))),
                       (URIRef(omop2obo + primary_id), RDF.type, OWL.Class),
                       (URIRef(omop2obo + primary_id), RDFS.label, Literal(primary_label))]
        # add domain-specific ontology root
        if self.construction_type != 'single' and self.superclass_dict is not None:
            if self.domain == 'condition':
                ont_data = [k for k, v in self.superclass_dict[self.domain].items()
                            if any([x for y in triples[1] for x in y if v.split('/')[-1].split('_')[0] in str(x)])][0]
                domain_root = self.superclass_dict[self.domain][ont_data]
            else:
                domain_root = self.superclass_dict[self.domain]
            superclass = [(URIRef(omop2obo + primary_id), RDFS.subClassOf, domain_root)]
        else:
            superclass = []
        # add the following triple to connect identifiers to class information
        triple_list = [(URIRef(omop2obo + primary_id), OWL.equivalentClass, triples[0])] + triples[1]

        return identifiers + superclass + triple_list

    def serializes_semantic_representation(self, ont: str, graph: Graph, write_location: str) -> None:
        """method serializes the semantic representation of the OMOP2OBO clinical mappings.

        Args:
            ont: A string containing a single ontology prefix (e.g. "hp") or the keyword "merged", which is used in
                the serialized file name.
            graph: An RDFLib Graph object containing ontology data.
            write_location: A string containing the file path for where to write the serialized data.

        Returns:
            None.
        """

        ont = ont.upper() if ont != 'merged' else 'Full'
        file_name = '/OMOP2OBO_' + self.domain.title() + '_SemanticRepresentation_' + ont + self.timestamp + '.owl'
        # serialize and save ontology
        print('Serializing Knowledge Graph')
        graph.serialize(destination=write_location + file_name, format='xml')
        # re-format ontology output to match OWL API standard
        ontology_file_formatter(write_location, file_name, self.owltools_location)

        return None

    def adds_triples_to_ontology(self, class_data: Dict) -> None:
        """Function takes a dictionary of processed clinical mappings and a list of ontologies, where each item in
        the ontology list is also a key in the nested class_dict input Dict object. Iterating over each ontology,
        this function updates the ontology with corresponding mapping triples. Once complete, the updated ontology is
        serialized.

        Args:
            class_data: A dictionary containing clinical concept data and triples for processed mappings.

        Returns:
            None.
        """

        for ont in self.ontologies:
            graph = self.ontology_data_dict[ont]
            org_edges, org_nodes = len(graph), len(set([i for j in [x[0::2] for x in graph] for i in j]))
            print('\nThe original {} ontology contains: {} edges and {} nodes'.format(ont, org_edges, org_nodes))
            # get all relevant triples and add them to ontology graph
            ont_triples = [i for j in [class_data[x][ont]['triples'] for x in tqdm(class_data.keys())] for i in j]
            for triple in ont_triples:
                graph.add(triple)
            # serialize updated ontologies
            up_edges, up_nodes = len(graph), len(set([i for j in [x[0::2] for x in graph] for i in j]))
            print('The updated {} ontology contains: {} edges and {} nodes'.format(ont, up_edges, up_nodes))
            self.serializes_semantic_representation(ont, graph, self.write_location)

        return None

    def transforms_mappings(self) -> None:
        """Method parses a Pandas DataFrame containing OMOP2OBO mappings and builds semantic representations of the
        mappings for single ontology or for a collection of ontologies. If the OMOP2OBO mapping file contains
        multiple ontologies, but the class construction type is "single" then an owl file is serialized for each
        ontology, otherwise a single merged set of ontologies is serialized. Additional details for each approach can
        be found below within each respective subclass.

        Returns:
            None.
        """

        pass

    @abstractmethod
    def gets_class_construction_type(self) -> str:
        """"A string detailing whether or not the classes are constructed using a single or multiple ontologies."""

        pass


class SingleOntologyConstruction(SemanticTransformer):
    """The Single Ontology Construction workflow is designed to create ontology-specific semantic definitions for
    each mapping rather than creating semantic definitions that span multiple ontologies. This approach is primarily
    used to determine the logical consistency of the mappings for each ontology."""

    def gets_class_construction_type(self) -> str:
        """"A string representing the type of knowledge graph being built."""

        return 'Single Ontology Construction'

    def transforms_mappings(self) -> None:
        """Method converts the clinical mappings, which are read in and stored as a Pandas DataFrame into a
        semantic representation, for each individual input ontology, and outputs each ontology containing the
        semantic representations as a serialized RDF/XML file. This work is completed by performing 3 steps:
            (1) Load and Preprocess Ontology Data
            (2) Construct Semantic Representations
            (3) Add Classes and Serialize Updated Ontology

        Returns:
             None.
        """

        # STEP 1 - Load Ontology Data
        print('\n*** STEP 1: Loading and Cleaning Ontologies')
        self.ontology_data_dict = self.loads_ontology_data()

        # STEP 2 - Process Clinical Data
        print('\n*** STEP 2: Transforming Mappings into Semantic Definitions')
        class_data: Dict = {}
        for idx, row in tqdm(self.omop2obo_data.iterrows(), total=self.omop2obo_data.shape[0]):
            # STEP 2A - Get Primary and Secondary Data
            primary_key = row[self.primary_column + '_ID']
            class_data[primary_key] = self.gets_concept_id_data(row)[primary_key]
            # STEP 2B - Get Ontology Information to Needed to Build Classes
            for ont in self.ontologies:
                uri, logic = row[ont.upper() + '_URI'].split(' | '), row[ont.upper() + '_LOGIC']
                # STEP 2C - Construct Semantic Representation
                if logic != 'N/A':
                    if '(' not in logic: logic = '{}({})'.format(logic, ', '.join([str(x) for x in range(len(uri))]))
                    # STEP 2C - Extract OWL Constructors and Order Inside Out (Inner Constructors Appear First)
                    result = regex.search(r'(?<grp>\((?:[^()]++|(?&grp))*\))', logic).captures('grp')
                    span_data = regex.search(r'(?<grp>\((?:[^()]++|(?&grp))*\))', logic).captures('grp')
                    constructors = self.orders_constructors(logic, result.copy())
                    logic_info = SemanticTransformer.extracts_logic(logic, result.copy(), constructors)
                    # STEP 2D - Construct Classes
                    triples = SemanticTransformer.class_constructor(logic, logic_info.copy(), span_data, uri)
                    class_data[primary_key][ont] = {'triples': triples}
                else:
                    class_data[primary_key][ont] = {'triples': (URIRef(obo + uri[0]), [])}

                # STEP 2E - Add Primary Data Metadata
                updated_triples = self.adds_class_metadata(class_data[primary_key], ont, 'primary_data')
                class_data[primary_key][ont]['triples'] = updated_triples

        # STEP 3 - Add Classes and Serialize Updated Ontology
        print('\n*** STEP 3: Add Classes and Serialize Updated Ontologies')
        self.adds_triples_to_ontology(class_data)

        return None


# class MultipleOntologyConstruction(SemanticTransformer):
#     """The Multiple Ontology Construction workflow is designed to create semantic definitions that span multiple
#     ontologies. This approach is the default method for creating semantic definitions within the OMOP2OBO framework."""
#
#     def gets_class_construction_type(self) -> str:
#         """"A string representing the type of knowledge graph being built."""
#
#         return 'Multiple Ontology Construction'
#
#     def constructs_multi_ontology_definitions(self, class_dict: Dict):
#         """
#
#         Args:
#             class_dict: A dict
#
#         - creates multiple ontology definitions
#         - if hpo == mondo then use equivalence class
#         - checks for CHEBI role vs entity
#         - checks for lab test allergen vs. antigen vs. neither
#
#         Return:
#
#         """
#
#         # pull dbxrefs from the ont dictionary to check for equiv or exact matches to other ontologies. This is
#         # particularly important for HP-MONDO mappings
#         # self.ontology_metadata
#
#         # obtain ontology ancestors -- only done for CHEBI
#         # if ont.upper() == 'CHEBI':
#         #     roots = {x: gets_class_ancestors(self.ontology_data_dict[ont], [x]) for x in uri.split(' | ')}
#         # else:
#         #     root_nodes = None
#
#         # CHEBI allergen vs. antigen
#
#         return None
#
#     def adds_secondary_data(self):
#         """
#         - if ingredient and drug are the same then set them as equivalent classes
#
#         :return:
#         """
#
#         return None
#
#     def adds_mapping_annotations(self):
#         """
#         - adds mapping categories, evidence
#         - adds synonyms (should work for primary and secondary data)
#
#         :return:
#         """
#
#         return None

    # def transforms_mappings(self):
    #     """Method converts the clinical mappings, which are read in and stored as a Pandas DataFrame into a semantic
    #     representation, for the merged ontologies, and outputs each ontology containing the semantic representation as
    #     a serialized RDF/XML file. This work is completed by performing 3 steps:
    #         (1) Load and Preprocess Ontology Data
    #         (2) Construct Semantic Representations
    #         (3) Add Classes and Serialize Updated Ontology
    #
    #     Returns:
    #          None.
    #     """
    #
    #     # STEP 1 - Load Ontology Data
    #     print('\n*** STEP 1: Loading, Cleaning and Merging Ontologies')
    #     self.ontology_data_dict = self.loads_ontology_data()
    #
    #     # STEP 2 - Process Clinical Data
    #     print('\n*** STEP 2: Transforming Mappings into Semantic Definitions')
    #     class_data: Dict = {}
    #     # for idx, row in tqdm(self.omop2obo_data.iterrows(), total=self.omop2obo_data.shape[0]):
    #     for idx, row in tqdm(omop2obo_data.iterrows(), total=omop2obo_data.shape[0]):
    #         # STEP 2A - Get Primary and Secondary Data
    #         primary_key = row[self.primary_column + '_ID']
    #         class_data[primary_key] = gets_concept_id_data(row)[primary_key]
    #         # STEP 2B - Get Ontology Information to Needed to Build Classes
    #         # for ont in self.ontologies:
    #         for ont in ontologies:
    #             uri, logic = row[ont.upper() + '_URI'].split(' | '), row[ont.upper() + '_LOGIC']
    #             # STEP 2C - Construct Semantic Representation
    #             if logic != 'N/A':
    #                 if '(' not in logic: logic = '{}({})'.format(logic, ', '.join([str(x) for x in range(len(uri))]))
    #                 # STEP 2C - Extract OWL Constructors and Order Inside Out (Inner Constructors Appear First)
    #                 result = regex.search(r'(?<grp>\((?:[^()]++|(?&grp))*\))', logic).captures('grp')
    #                 span_data = regex.search(r'(?<grp>\((?:[^()]++|(?&grp))*\))', logic).captures('grp')
    #                 # constructors = self.orders_constructors(logic, result.copy())
    #                 # logic_info = SemanticTransformer.extracts_logic(logic, result.copy(), constructors)
    #                 constructors = orders_constructors(logic, result.copy())
    #                 logic_info = extracts_logic(logic, result.copy(), constructors)
    #                 # STEP 2D - Construct Classes
    #                 # triples = SemanticTransformer.class_constructor(logic, logic_info.copy(), span_data, uri)
    #                 triples = class_constructor(logic, logic_info.copy(), span_data, uri)
    #                 class_data[primary_key][ont] = {'triples': triples}
    #             else:
    #                 class_data[primary_key][ont] = {'triples': (URIRef(obo + uri[0]), [])}
    #
    #             # STEP 3 - Assemble Multi-Ontology Definition
    #             self.
    #
    #             # STEP 4 - Add Primary Data Metadata
    #             # updated_triples = self.adds_class_metadata(class_data[primary_key][ont], 'primary_data')
    #             updated_triples = adds_class_metadata(class_data[primary_key][ont], 'primary_data')
    #             class_data[primary_key][ont]['triples'] = updated_triples
    #
    #     # STEP 3 - Add Classes and Serialize Updated Ontology
    #     print('\n*** STEP 3: Add Classes and Serialize Updated Ontologies')
    #     self.adds_triples_to_ontology(class_data, list(self.ontology_data_dict.keys()))
    #
    #     # omop2obo_data = pd.read_excel(omop2obo_data_file, sep=',', header=0)
    #     # omop2obo_data.fillna('N/A', inplace=True)
    #
    #     return None
