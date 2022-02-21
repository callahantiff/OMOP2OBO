#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import glob
import json
import os
import pandas
import pickle
import sys

from rdflib import Graph, Literal, Namespace, URIRef  # type: ignore
from rdflib.namespace import RDF, RDFS, OWL  # type: ignore
from tqdm import tqdm
from typing import Dict, Optional

from omop2obo.utils import *

# set up environment variables
obo = Namespace('http://purl.obolibrary.org/obo/')
oboinowl = Namespace('http://www.geneontology.org/formats/oboInOwl#')
schema = Namespace('http://www.w3.org/2001/XMLSchema#')


class OntologyInfoExtractor(object):
    """Class creates an RDF graph from an OWL file and then performs queries to return DbXRefs, synonyms, and labels.

    Attributes:
        graph: An rdflib graph object.
        ont_dictionary: A dictionary, where keys are a string aliasing an ontology and values are a string pointing
            the local location where the ontology was downloaded.
        ont_directory: A string containing the filepath to the ontology data directory.

    Raises:
        OSError: If the ontology_dictionary cannot be found.
        TypeError: If ontology_dictionary is empty.
    """

    def __init__(self, ontology_directory: str, ont_dictionary: Dict) -> None:
        self.graph: Graph = Graph()
        self.ont_dictionary = ont_dictionary
        self.master_ontology_dictionary: Optional[Dict] = {}

        # check for ontology data
        if not os.path.exists(ontology_directory):
            raise OSError("Can't find 'ontologies/' directory, this directory is a required input")
        elif len(glob.glob(ontology_directory + '/*.owl')) == 0:
            raise TypeError('The ontologies directory is empty')
        else:
            self.ont_directory = ontology_directory

    def get_ontology_information(self, ont_id: str) -> Dict:
        """Function queries an RDF graph and returns labels, definitions, dbXRefs, and synonyms for all
        non-deprecated ontology classes.

        Args:
            ont_id: A string containing an ontology namespace.

        Returns: A dict mapping each DbXRef to a list containing the corresponding class ID and label. For example:
            {'label': {'narrow naris': 'http://purl.obolibrary.org/obo/HP_0009933'},
            'definition': {'agenesis of lower primary incisor.': 'http://purl.obolibrary.org/obo/HP_0011047'},
            'dbxref': {'SNOMEDCT_US:88598008': 'http://purl.obolibrary.org/obo/HP_0000735'},
            'synonyms': { 'open bite': 'http://purl.obolibrary.org/obo/HP_0010807'}}
        """

        # get class information
        deprecated = gets_deprecated_ontology_classes(self.graph, ont_id)
        obsolete = gets_obsolete_ontology_classes(self.graph, ont_id)
        filter_classes = set([x for x in gets_ontology_classes(self.graph, ont_id) if x not in deprecated | obsolete])

        # filter results and add to dictionary
        res: Dict = {
            'label': gets_ontology_class_labels(self.graph, filter_classes),
            'definition': gets_ontology_class_definitions(self.graph, filter_classes),
            'dbxref': gets_ontology_class_dbxrefs(self.graph, filter_classes),
            'synonym': gets_ontology_class_synonyms(self.graph, filter_classes)
        }

        return res

    def creates_pandas_dataframe(self, res: Dict, ont_id: str) -> pandas.DataFrame:
        """Takes information about an ontology, processes it, adn then outputs it as a Pandas DataFrame object.

        Args:
            res: A dict mapping each DbXRef to a list containing the corresponding class ID and label. For example:
                {'label': {'narrow naris': 'http://purl.obolibrary.org/obo/HP_0009933'},
                'definition': {'agenesis of lower primary incisor.': 'http://purl.obolibrary.org/obo/HP_0011047'},
                'dbxref': {'SNOMEDCT_US:88598008': 'http://purl.obolibrary.org/obo/HP_0000735'},
                'synonyms': { 'open bite': 'http://purl.obolibrary.org/obo/HP_0010807'}}
            ont_id: A string containing an ontology namespace.

        Returns:
             ont_df: A pandas DataFrame object containing ontology metadata.
        """

        # get needed ontology metadata
        ns = list(self.graph.triples((None, URIRef(oboinowl + 'default-namespace'), None)))
        ns = str(ns[0][2]) if len(ns) > 0 else ont_id
        sab = str(list(self.graph.triples((None, OWL.versionIRI, None)))[0][2])

        # convert data to mapping structure -- ontology labels
        print('\nConverting Merged Data into Mapping Format')
        ont_data = pandas.DataFrame({'ontology_id': k, 'CODE': k.split('/')[-1].replace('_', ':'), 'STRING': v,
                                     'STRING_TYPE': 'class label'} for k, v in res['label'].items())
        ont_defs = pandas.DataFrame({'ontology_id': k, 'CODE': k.split('/')[-1].replace('_', ':'), 'STRING': v,
                                     'STRING_TYPE': 'class definition'} for k, v in res['definition'].items())
        # merge ontology classes and definitions
        ont_base = pandas.concat([ont_data, ont_defs]).drop_duplicates()
        # process synonyms
        ont_syn = pandas.DataFrame({'ontology_id': y[0], 'CODE': y[0].split('/')[-1].replace('_', ':'), 'STRING': x[0],
                                    'STRING_TYPE': x[1]}
                                   for y in [(k, v) for k, v in res['synonym'].items()] for x in y[1])
        ont_base_syn = ont_base.merge(ont_syn, on=list(set(ont_base).intersection(set(ont_syn))),
                                      how='outer').drop_duplicates()
        # process dbxrefs
        ont_dbx = pandas.DataFrame({'ontology_id': y[0], 'CODE': y[0].split('/')[-1].replace('_', ':'), 'DBXREF': x[0],
                                    'DBXREF_TYPE': x[1], 'DBXREF_SAB_NAME': x[2]}
                                   for y in [(k, v) for k, v in res['dbxref'].items()] for x in y[1])
        ont_base_syn_dbx = ont_base_syn.merge(ont_dbx, on=list(set(ont_base_syn).intersection(set(ont_dbx))),
                                              how='outer').drop_duplicates()
        # add metadata
        ont_base_syn_dbx['SAB'] = sab; ont_base_syn_dbx['SAB_NAME'] = sab; ont_base_syn_dbx['SEMANTIC_TYPE'] = ns
        # rename columns
        ont_df = ont_base_syn_dbx
        ont_df.rename(columns={'ontology_id': 'OBO_ontology_id', 'STRING_TYPE': 'OBO_STRING_TYPE',
                               'SEMANTIC_TYPE': 'OBO_SEMANTIC_TYPE', 'SAB': 'OBO_SAB', 'SAB_NAME': 'OBO_SAB_NAME',
                               'DBXREF_TYPE': 'OBO_DBXREF_TYPE', 'DBXREF_SAB_NAME': 'OBO_DBXREF_SAB_NAME'},
                      inplace=True)
        ont_df['OBO_DBXREF_SAB'] = ont_df['OBO_DBXREF_SAB_NAME']
        ont_df = ont_df.fillna('None').drop_duplicates()

        # save data
        file_str = '{}/{}_ontology_hierarchy_information.pkl'
        max_bytes, bytes_out = 2 ** 31 - 1, pickle.dumps(ont_df); n_bytes = sys.getsizeof(bytes_out)
        with open(file_str.format(self.ont_directory, ont_id), 'wb') as f_out:
            for idx in range(0, n_bytes, max_bytes):
                f_out.write(bytes_out[idx:idx + max_bytes])

        return ont_df

    def ontology_entity_finder(self, ont_df: pandas.DataFrame, ont_id: str) -> None:
        """Function takes an ontology and finds all ancestors and children for each ontology class. The function
        returns a separate dictionary for each entity type/

        Args:
            ont_df: A Pandas DataFrame containing information which has been processed to ensure ease of processing
                in the current library.
            ont_id: A string containing an ontology namespace.

        Return:
            None.
        """

        sab = str(list(self.graph.triples((None, OWL.versionIRI, None)))[0][2])

        # process ancestors
        print('\t- Obtaining Concept Ancestors and Children. This Process Takes Several Minutes')
        obo_ancs = {
            x: entity_search(self.graph, x, 'ancestors', sab.split('/')[-1].split('.')[0].upper(), RDFS.subClassOf)
            for x in tqdm(set(ont_df['OBO_ontology_id']))}
        obo_kids = {
            x: entity_search(self.graph, x, 'children', sab.split('/')[-1].split('.')[0].upper(), RDFS.subClassOf)
            for x in tqdm(set(ont_df['OBO_ontology_id']))}

        # write data
        anc_file_str, kid_file_str = '{}/{}_ontology_ancestors.json', '{}/{}_ontology_children.json'
        json.dump(obo_ancs, open(anc_file_str.format(self.ont_directory, ont_id), 'w'))
        json.dump(obo_kids, open(kid_file_str.format(self.ont_directory, ont_id), 'w'))

        return None

    def ontology_processor(self) -> None:
        """Using different information from the user, this function retrieves all class labels, definitions,
        synonyms, and database cross-references (dbXref). The function expects a dictionary as input where the keys are
        short nick-names or OBO abbreviations for ontologies and the values are lists, where the first item is a string
        that contains the file path information to the downloaded ontology, the second item is a list of clinical
        identifiers that can be used for filtering the dbXrefs. An example of this input is shown below.

            {'CHEBI': ['resources/ontologies/chebi_without_imports.owl', ['DrugBank', 'ChEMBL', 'UniProt']]}

        Returns:
            None.
        """

        for ont in self.ont_dictionary.items():
            print('\nPROCESSING ONTOLOGY: {0}'.format(ont[0]))
            print('Loading RDF Graph ... Please be patient, this step can take several minutes for large files.')
            self.graph = Graph().parse(ont[1], format='xml')

            # get ontology information
            ont_dict = self.get_ontology_information(ont[0])
            ont_df = self.creates_pandas_dataframe(ont_dict, ont[0])
            self.ontology_entity_finder(ont_df, ont[0])

        return None
