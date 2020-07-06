#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import glob
import os
import pickle

from datetime import datetime
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL
from tqdm import tqdm
from typing import Dict, List

# define global namespace
obo = Namespace('http://purl.obolibrary.org/obo/')
oboinowl = Namespace('http://www.geneontology.org/formats/oboInOwl#')


class OntologyInfoExtractor(object):
    """Class creates an RDF graph from an OWL file and then performs queries to return DbXRefs, synonyms, and labels.

    Attributes:
        graph: An rdflib graph object.
        ont_dictionary: A dictionary, where keys are a string aliasing an ontology and values are a string pointing
            the local location where the ontology was downloaded.
        ont_directory: A string containing the filepath to the ontology data directory.
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

    def get_ontology_information(self, ont_id: str, codes: List = None) -> Dict:
        """Function queries an RDF graph and returns labels, definitions, dbXRefs, and synonyms for all
        non-deprecated ontology classes.

        Args:
            ont_id: A string containing an ontology namespace.
            codes: A list of strings that represent terminology names.

        Returns: A dict mapping each DbXRef to a list containing the corresponding class ID and label. For example:
            {'HP': {
                'label': {'narrow naris': 'http://purl.obolibrary.org/obo/HP_0009933'},
                'definition': {'agenesis of lower primary incisor.': 'http://purl.obolibrary.org/obo/HP_0011047'},
                'dbxref': {'SNOMEDCT_US:88598008': 'http://purl.obolibrary.org/obo/HP_0000735'},
                'synonyms': { 'open bite': 'http://purl.obolibrary.org/obo/HP_0010807'}}
        """

        start = datetime.now()
        print('Identifying ontology information: {}'.format(start))
        res = {'label': {}, 'definition': {}, 'dbxref': {}, 'synonyms': {}}

        # get ontology classes
        class_ids = [x for x in self.graph.subjects(RDF.type, OWL.Class) if isinstance(x, URIRef)]
        class_dep = list(self.graph.subjects(OWL.deprecated,
                                             Literal('true',
                                                     datatype=URIRef('http://www.w3.org/2001/XMLSchema#boolean'))))

        # filter classes to only include those that are in the ont_id namespace and are not deprecated
        filtered_classes = [x for x in list(set(class_ids) - set(class_dep)) if ont_id.lower() in str(x).lower()]

        for cls in tqdm(filtered_classes):
            # labels
            for x in list(self.graph.objects(cls, RDFS.label)):
                res['label'][str(x).encode('ascii', 'ignore').lower().decode('utf-8')] = str(cls)

            # definitions
            for x in list(self.graph.objects(cls, URIRef(obo + 'IAO_0000115'))):
                res['definition'][str(x).encode('ascii', 'ignore').lower().decode('utf-8')] = str(cls)

            # dbxref
            for x in list(self.graph.objects(cls, URIRef(oboinowl + 'hasDbXref'))):
                if codes:
                    if any(i for i in codes if i in str(x)):
                        res['dbxref'][str(x)] = str(cls)
                else:
                    res['dbxref'][str(x)] = str(cls)

            # synonyms
            syns = [str(x).encode('ascii', 'ignore').lower().decode('utf-8')
                    for x in list(self.graph.objects(cls, URIRef(oboinowl + 'hasSynonym')))]
            syns += [str(x).encode('ascii', 'ignore').lower().decode('utf-8')
                     for x in list(self.graph.objects(cls, URIRef(oboinowl + 'hasExactSynonym')))]
            syns += [str(x).encode('ascii', 'ignore').lower().decode('utf-8')
                     for x in list(self.graph.objects(cls, URIRef(oboinowl + '#hasBroadSynonym')))]
            syns += [str(x).encode('ascii', 'ignore').lower().decode('utf-8')
                     for x in list(self.graph.objects(cls, URIRef(oboinowl + 'hasNarrowSynonym')))]
            syns += [str(x).encode('ascii', 'ignore').lower().decode('utf-8')
                     for x in list(self.graph.objects(cls, URIRef(oboinowl + 'hasRelatedSynonym')))]

            for x in syns:
                res['synonyms'][x] = str(cls)

        finish = datetime.now()
        print("Finished processing query: {}".format(finish))

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
            print('\n****** Processing Ontology: {0}'.format(ont[0]))

            # check and make sure that we are not re-running a file we have already processed
            if ont[1].replace('.owl', '_class_information.pickle').split('/')[-1] in os.listdir(self.ont_directory):
                pass
            else:
                print('Loading RDF Graph')
                self.graph = Graph().parse(ont[1], format='xml')

                # get ontology information
                ont_dict = self.get_ontology_information(ont[0])

                with open(str(ont[1][:-4]) + '_class_information.pickle', 'wb') as handle:
                    pickle.dump(ont_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
                handle.close()

        return None

    def ontology_loader(self) -> Dict:
        """Function takes a list of file paths to pickled data, loads the data, and then saves each file as a dictionary
        entry.

        Returns:
            A dictionary where each key is a file name and each value is a dictionary.

        Raises:
            ValueError: If the provided ontology name does not match any downloaded ontology files.
            ValueError: If the number of dictionary entries does not equal the number of files in the files list.
        """

        # find files that match user input
        ont_files = []
        for key, val in self.ont_dictionary.items():
            prefix = val.split('/')[-1].replace('_without_imports.owl', '')
            pickle_file = glob.glob(self.ont_directory + '/' + str(prefix.lower()) + '*.pickle')
            if len(pickle_file) != 0:
                ont_files.append((key, pickle_file[0]))

        if len(ont_files) == 0:
            raise ValueError('Unable to find files that include that ontology name')
        else:
            ontology_data = {}
            for ont, f in tqdm(ont_files):
                with open(f, 'rb') as _file:
                    ontology_data[ont] = pickle.load(_file)
            _file.close()

            if len(ont_files) != len(ontology_data):
                raise ValueError('Unable to load all of files referenced in the file path')
            else:
                return ontology_data
