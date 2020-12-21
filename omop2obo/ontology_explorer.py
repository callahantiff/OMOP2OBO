#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import glob
import os
import pickle

from rdflib import Graph  # type: ignore
from tqdm import tqdm  # type: ignore
from typing import Dict

from omop2obo.utils import *


class OntologyInfoExtractor(object):
    """Class creates an RDF graph from an OWL file and then performs queries to return DbXRefs, synonyms, and labels.

    Attributes:
        graph: An RDFLib graph object.
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

        # check for ontology data
        if not os.path.exists(ontology_directory):
            raise OSError("Can't find 'ontologies/' directory, this directory is a required input")
        elif len(glob.glob(ontology_directory + '/*.owl')) == 0:
            raise TypeError('The ontologies directory is empty')
        else:
            self.ont_directory = ontology_directory

    def get_ontology_information(self, ont_id: str) -> Dict:
        """Function queries an RDF graph and returns labels, definitions, dbXRefs, and synonyms for all non-deprecated
        ontology classes.

        Args:
            ont_id: A string containing an ontology namespace.

        Returns: A dict mapping each DbXRef to a list containing the corresponding class ID and label. For example:
            {'HP': {
                'label': {'narrow naris': 'http://purl.obolibrary.org/obo/HP_0009933'},
                'definition': {'agenesis of lower primary incisor.': 'http://purl.obolibrary.org/obo/HP_0011047'},
                'dbxref': {'SNOMEDCT_US:88598008': 'http://purl.obolibrary.org/obo/HP_0000735'},
                'synonyms': { 'open bite': 'http://purl.obolibrary.org/obo/HP_0010807'}}
        """

        # get class information
        deprecated_classes = gets_deprecated_ontology_classes(self.graph, ont_id)
        filter_classes = set([x for x in gets_ontology_classes(self.graph, ont_id) if x not in deprecated_classes])

        # filter results and add to dictionary
        syns = gets_ontology_class_synonyms(self.graph, filter_classes)
        dbxrefs = gets_ontology_class_dbxrefs(self.graph, filter_classes)
        res: Dict = {
            'label': gets_ontology_class_labels(self.graph, filter_classes),
            'definition': gets_ontology_class_definitions(self.graph, filter_classes),
            'dbxref': dbxrefs[0], 'dbxref_type': dbxrefs[1],
            'synonym': syns[0], 'synonym_type': syns[1],
        }

        return res

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

            # check and make sure that we are not re-running a file we have already processed
            if ont[1].replace('.owl', '_class_information.pickle').split('/')[-1] in os.listdir(self.ont_directory):
                pass
            else:
                print('Loading RDF Graph ... Please be patient, this step can take several minutes for large files.')
                self.graph = Graph().parse(ont[1], format='xml')

                # get ontology information
                ont_dict = self.get_ontology_information(ont[0])

                with open(str(ont[1][:-4]) + '_class_information.pickle', 'wb') as handle:
                    pickle.dump(ont_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
                handle.close()

        return None

    def ontology_loader(self) -> None:
        """Function takes a list of file paths to pickled data, loads the data, and then saves each file as a dictionary
        entry.

        Returns:
            A dictionary where each key is a file name and each value is a dictionary.

        Raises:
            OSError: If there are no pickled data files in the directory specified by the ont_directory variable.
        """

        # find pickled data
        pickled_data = glob.glob(self.ont_directory + '/*_class_information.pickle')

        if len(pickled_data) == 0:
            raise OSError('There are no ontology pickled data files in: {}'.format(self.ont_directory))
        else:
            ontology_data = {}

            for ont_file in tqdm(pickled_data):
                if 'master' not in ont_file:  # ignore existing pickled master_ontology_dictionary files
                    with open(ont_file, 'rb') as _file:
                        ont_data = pickle.load(_file)
                        ont_id = list(ont_data['label'].values())[0].split('/')[-1].split('_')[0].lower()
                        ontology_data[ont_id] = ont_data
                    _file.close()

            # write out all ontologies into a single pickled file
            with open(self.ont_directory + '/master_ontology_dictionary.pickle', 'wb') as handle:
                pickle.dump(ontology_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
            handle.close()

            return None
