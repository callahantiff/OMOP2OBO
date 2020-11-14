#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import glob  # type: ignore
import os
import pandas as pd  # type: ignore

from rdflib import URIRef  # type: ignore
from typing import Dict, List, Optional


class SemanticMappingTransformer(object):

    def __init__(self, ontology_list: List, omop2obo_data_file: str, ontology_directory: str = Optional[None],
                 map_type: str = 'multi', superclasses: Dict = Optional[None]) -> None:
        """This class is designed to facilitate the transformation of OMOP2OBO mappings into semantic
        representations. To do this, the class includes several methods that assist with processing different aspects
        of the mapping data. The class currently enables two types of mappings to be created: (1) Single. A single
        mapping processes each OMOP2OBO mapping by ontology, within that ontology; (2) Multi. A multi mapping first
        merges all relevant ontologies and then constructs new OMOP2OBO classes that span multiple ontologies.

        For additional information on this approach please see the dedicated project wiki page:
            https://github.com/callahantiff/OMOP2OBO/wiki/Semantic-Mapping-Representation

        Arg:
            ontologies: A list of ontology identifiers (i.e. ['HP', 'MONDO']).
            omop2obo_data: A Pandas DataFrame containing OMOP2OBO mapping data.
            ont_directory: A string pointing to a directory that contains OWL ontology files.
            construction_type: A string indicating whether to build single (i.e. 'single') or multi-ontology
                (i.e. 'multi') classes. The default type is "multi".
           superclass_dict: A dictionary where keys are clinical domains and values are either a dictionary or a URIRef
                object. For example:
                    {'condition': {'phenotype': URIRef('http://purl.obolibrary.org/obo/HP_0000118'),
                                                  'disease': URIRef('http://purl.obolibrary.org/obo/MONDO_0000001')},
                                    'drug': URIRef('http://purl.obolibrary.org/obo/CHEBI_24431'),
                                    'measurement': URIRef('http://purl.obolibrary.org/obo/HP_0000118')}
           multi_class_relations: A nested dictionary keyed by clinical domain that contains sub-dictionaries of
                edges and relation URIs.
                For example: {'conditions': {'relations':
                                {'MONDO-HP': rdflib.term.URIRef('http://purl.obolibrary.org/obo/RO_0002200')}},
                              'drugs': {'relations':
                                {'CHEBI-VO': rdflib.term.URIRef('http://purl.obolibrary.org/obo/RO_0002180'),
                                'CHEBI-PR': rdflib.term.URIRef('http://purl.obolibrary.org/obo/RO_0002180'),
                                'VO-NCBITAXON': rdflib.term.URIRef('http://purl.obolibrary.org/obo/RO_0002162')}},
                              'measurements': {'relations':
                                {'HP-UBERON': rdflib.term.URIRef('http://purl.obolibrary.org/obo/RO_0002479'),
                                'HP-CL': rdflib.term.URIRef('http://purl.obolibrary.org/obo/RO_0002180'),
                                'HP-CHEBI': rdflib.term.URIRef('http://purl.obolibrary.org/obo/RO_0002180')}}}

        Returns:
            None.
        """

        # check ontology list to be a list
        if not isinstance(ontology_list, List):
            raise TypeError('ontology_list must be type str')
        elif len(ontology_list) == 0:
            raise ValueError('ontology_list cannot be an empty list')
        else:
            self.ontologies = ontology_list

        # check mapping data input
        if not isinstance(omop2obo_data_file, str):
            raise TypeError('omop2obo_data_file must be type str.')
        elif not os.path.exists(omop2obo_data_file):
            raise OSError('The {} file does not exist!'.format(omop2obo_data_file))
        elif os.stat(omop2obo_data_file).st_size == 0:
            raise TypeError('Input file: {} is empty'.format(omop2obo_data_file))
        else:
            print('Loading Mapping Data')
            self.omop2obo_data = pd.read_excel(omop2obo_data_file, sheet_name='Aggregated_Mapping_Results',
                                               sep=',', header=0)
            self.omop2obo_data.fillna('', inplace=True)

        # check ontology directory
        onts = 'resources/ontologies' if ontology_directory is None else ontology_directory
        ont_data = glob.glob(onts + '/*.owl')
        ont_check = [x for x in self.ontologies if x.lower() in [y.split('/')[-1].split('_')[0] for y in ont_data]]

        # check for ontology data
        if not os.path.exists(onts):
            raise OSError("Can't find 'ontologies/' directory, this directory is a required input")
        elif len(ont_data) == 0:
            raise TypeError('The ontologies directory is empty')
        elif len(ont_check) == 0:
            raise ValueError('No ontology owl files match provided ontology list')
        else:
            self.ont_directory = onts

        # check mapping approach type
        if not isinstance(map_type, str):
            raise TypeError('map_type must be type string')
        else:
            self.construction_type = 'single' if map_type != 'multi' else map_type

        # check subclass dict input
        if superclasses is not None:
            if not isinstance(superclasses, Dict):
                self.superclass_dict = superclasses
            else:
                raise TypeError('superclasses must be type Dict')
        else:
            self.superclass_dict = {'condition': {'phenotype': URIRef('http://purl.obolibrary.org/obo/HP_0000118'),
                                                  'disease': URIRef('http://purl.obolibrary.org/obo/MONDO_0000001')},
                                    'drug': URIRef('http://purl.obolibrary.org/obo/CHEBI_24431'),
                                    'measurement': URIRef('http://purl.obolibrary.org/obo/HP_0000118')}

        # read in multi-ontology relations
        if self.construction_type == 'multi':
            rel_data_loc = 'resources/mapping_semantics/omop2obo_class_relations.txt'
            if not os.path.exists(rel_data_loc):
                raise OSError('The {} file does not exist!'.format(rel_data_loc))
            elif os.stat(rel_data_loc).st_size == 0:
                raise TypeError('Input file: {} is empty'.format(rel_data_loc))
            else:
                print('Loading Multi-Ontology Class Construction Relations')
                rel_data = glob.glob('resources/mapping_semantics/omop2obo_class_relations.txt')[0]
                self.multi_class_relations: Dict = {}
                with open(rel_data, 'r') as f:
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

        # check for existing version of omop2obo
        existing_mappings = glob.glob('resources/mapping_semantics/omop2obo*.owl')
        self.current_omop2obo = None if len(existing_mappings) == 0 else existing_mappings[0]
