#############################
# ontology_explorer.py
#############################


import glob
import pickle
import re

from datetime import datetime
from progressbar import ProgressBar, FormatLabel, Percentage, Bar
from rdflib import Graph


class OntologyEx(object):
    """Class creates an RDF graph from an OWL file and then performs queries to return DbXRefs, synonyms, and labels.

    Args:
        graph_path: A string that contains a filepath to an ontology file. If no string is passed the class is
        initialized with an empty graph.
    """

    def __init__(self, graph_path: str = ''):
        """ ."""
        self.graph = graph_path

    def set_graph(self):
        self.graph = Graph().parse(self.graph, format='xml')

    def get_graph(self):
        return self.graph

    def ontology_dictionary(self, ont_id: str):
        """Queries an RDF graph for non-deprecated classes.

        Args:
            ont_id: A string containing part of an ontology ID.

        Returns:
            A dict mapping each classes label to a list containing the corresponding class ID and definition. For
            example:
            {'ankle joint effusion': ['http://purl.obolibrary.org/obo/HP_0032063',
                                      'abnormal accumulation of fluid in or around the ankle joint'],
             'macular hyperpigmentation': ['http://purl.obolibrary.org/obo/HP_0011509',
                                      'increased amount of pigmentation in the macula lutea.']}

        Raises:
            ValueError: If the query returned no results.
        """

        start = datetime.now()
        print('Started running query to identify all ontology classes: {}'.format(start))

        query = """SELECT DISTINCT ?c ?c_label ?defn
                    WHERE {?c rdf:type owl:Class .
                           ?c rdfs:label ?c_label .
                           optional {?c obo:IAO_0000115 ?defn}
                           minus {?c owl:deprecated true}""" + \
                'FILTER(STRSTARTS(STR(?c), "http://purl.obolibrary.org/obo/%s"))\n' % str(ont_id) + ' }\n'

        query_results = self.graph.query(query, initNs={'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                                                        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
                                                        'owl': 'http://www.w3.org/2002/07/owl#',
                                                        'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#',
                                                        'obo': 'http://purl.obolibrary.org/obo/'})

        # create progress bar
        widgets = [Percentage(), Bar(), FormatLabel('(elapsed: %(elapsed)s)')]
        pbar = ProgressBar(widgets=widgets, maxval=len(query_results))
        valid_res = {}

        for row in pbar(query_results):
            if row[2] is not None:
                label = row[1].encode('ascii', 'ignore').lower().decode('utf-8')
                defn = row[2].encode('ascii', 'ignore').lower().decode('utf-8')
                valid_res[label] = [str(row[0]), defn]
            else:
                valid_res[row[1].encode('ascii', 'ignore').lower().decode('utf-8')] = [str(row[0]), '']

        pbar.finish()
        finish = datetime.now()
        print("Finished processing query: {}".format(finish))

        if not len(valid_res) > 1:
            raise ValueError('Error - did not return any classes for graph: {0}'.format(valid_res))
        else:
            time_diff = round((finish - start).total_seconds() / 60, 2)
            print('Query returned: {0} classes in {1} minutes \n'.format(len(valid_res), time_diff))
            return valid_res

    def get_ontology_synonyms(self, ont_id: str):
        """Queries an RDF graph and returns exact, broad, narrow, and related synonyms.

        Args:
            ont_id: A string containing part of an ontology ID.

        Returns:
        A dict mapping each synonym to a list containing the corresponding class ID and label. For example:
            {'unexpanded lung': ['http://purl.obolibrary.org/obo/NCIT_C2888', 'atelectasis']}

        Raises:
            ValueError: If the query returned no results.
        """

        start = datetime.now()
        print('Started running query to identify all ontology class synonyms: {}'.format(start))
        syn = {}

        query = """SELECT DISTINCT ?syn ?c ?c_label ?p
                   WHERE { ?c rdf:type owl:Class .
                           ?c ?p ?syn .
                           ?c rdfs:label ?c_label .
                      FILTER(?p in (oboInOwl:hasSynonym, oboInOwl:hasExactSynonym, oboInOwl:hasBroadSynonym, 
                      oboInOwl:hasNarrowSynonym, oboInOwl:hasRelatedSynonym))
                      minus {?c owl:deprecated true}""" + \
                'FILTER(STRSTARTS(STR(?c), "http://purl.obolibrary.org/obo/%s"))\n' % str(ont_id) + ' }\n'

        query_results = self.graph.query(query, initNs={'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                                                        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
                                                        'owl': 'http://www.w3.org/2002/07/owl#',
                                                        'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#'})

        # create progress bar
        widgets = [Percentage(), Bar(), FormatLabel('(elapsed: %(elapsed)s)')]
        pbar = ProgressBar(widgets=widgets, maxval=len(query_results))

        for row in pbar(query_results):
            key = row[0].encode('ascii', 'ignore').lower().decode('utf-8')
            if key in syn.keys():
                defin = row[2].encode('ascii', 'ignore').lower().decode('utf-8')
                if str(row[1]) not in syn[key] and defin not in syn[key]:
                    syn[key] += [str(row[1]), row[2].encode('ascii', 'ignore').lower().decode('utf-8')]
            else:
                syn[key] = [str(row[1]), row[2].encode('ascii', errors='replace').lower().decode('utf-8')]

        pbar.finish()
        finish = datetime.now()
        print("Finished processing query: {}".format(finish))

        if not len(syn) > 1:
            raise ValueError('Error - did not return any synonyms for graph: {0}'.format(len(syn)))
        else:
            time_diff = round((finish - start).total_seconds() / 60, 2)
            print('Query returned: {0} synonyms in {1} minutes \n'.format(len(syn), time_diff))
            return syn

    def get_ontology_dbxrefs(self, codes: list, ont_id: str):
        """Function queries an RDF graph and returns DbXRefs.

        Args:
            codes: A list of strings that represent terminology names.
            ont_id: A string containing part of an ontology ID.

        Returns:
        A dict mapping each DbXRef to a list containing the corresponding class ID and label. For example:
            {'UMLS:C4022824': ['http://purl.obolibrary.org/obo/HP_0012604', 'Hyponatriuria'],
             'SNOMED:38599001': ['http://purl.obolibrary.org/obo/HP_0012231', 'Exudative retinal detachment']}

        Raises:
            ValueError: If the query returned no results.
        """

        start = datetime.now()
        print('Started running query to identify all ontology class DbXRefs: {}'.format(start))
        xref = {}

        query = """SELECT DISTINCT ?dbref ?c ?c_label 
               WHERE {?c rdf:type owl:Class .
                     ?c oboInOwl:hasDbXref ?dbref .
                     ?c rdfs:label ?c_label .
                     minus {?c owl:deprecated true}""" + \
                'FILTER(STRSTARTS(STR(?c), "http://purl.obolibrary.org/obo/%s"))\n' % str(ont_id) + ' }\n'

        query_results = self.graph.query(query, initNs={'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                                                        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
                                                        'owl': 'http://www.w3.org/2002/07/owl#',
                                                        'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#'})

        # create progress bar
        widgets = [Percentage(), Bar(), FormatLabel('(elapsed: %(elapsed)s)')]
        pbar = ProgressBar(widgets=widgets, maxval=len(query_results))

        for row in pbar(query_results):
            for code in codes:
                if code in str(row[0]):
                    key = str(code) + ':' + str(str(row[0]).split(':')[-1])
                    if key in xref.keys():
                        xref[key] += [str(row[1]), str(row[2])]
                    else:
                        xref[key] = [str(row[1]), str(row[2])]

        pbar.finish()
        finish = datetime.now()
        print("Finished processing query: {}".format(finish))

        if not len(xref) > 1:
            raise ValueError('Error - did not return any DbXRefs for graph: {0}'.format(len(xref)))
        else:
            time_diff = round((finish - start).total_seconds() / 60, 2)
            print('Query returned: {0} DbXRefs in {1} minutes \n'.format(len(xref), time_diff))
            return xref

    def ontology_info_getter(self, ont_info_dictionary: dict):
        """Using different information from the user, this function retrieves all class labels, definitions,
        synonyms, and database cross-references (dbXref). The function expects a dictionary as input where the keys are
        short nick-names or OBO abbreviations for ontologies and the values are lists, where the first item is a string
        that contains the file path information to the downloaded ontology, the second item is a list of clinical
        identifiers that can be used for filtering the dbXrefs. An example of this input is shown below.

            {'CHEBI': ['resources/ontologies/chebi_without_imports.owl', ['DrugBank', 'ChEMBL', 'UniProt']]}

        Args:
            ont_info_dictionary: A dictionary. Detail on this is provided in the function description.

        Returns:
            None.
        """

        for ont in ont_info_dictionary.items():
            print('Processing Ontology: {0} \n'.format(ont[0]))

            # create graph
            self.graph = Graph().parse(ont[1][0], format='xml')

            # get ontology classes
            ont_dict = self.ontology_dictionary(ont[0])
            with open(str(ont[1][0][:-4]) + '_classes.pickle', 'wb') as handle:
                pickle.dump(ont_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

            # get ontology synonyms
            syn = self.get_ontology_synonyms(ont[0])
            with open(str(ont[1][0][:-4]) + '_synonyms.pickle', 'wb') as handle:
                pickle.dump(syn, handle, protocol=pickle.HIGHEST_PROTOCOL)

            # get ontology dbXrefs
            if None not in ont[1][1]:
                dbxref = self.get_ontology_dbxrefs(ont[1][1], ont[0])
                with open(str(ont[1][0][:-4]) + '_DbXRef.pickle', 'wb') as handle:
                    pickle.dump(dbxref, handle, protocol=pickle.HIGHEST_PROTOCOL)

        return None

    @staticmethod
    def ontology_loader(ontology_name: list):
        """Function takes a list of file paths to pickled data, loads the data, and then saves each file as a dictionary
        entry.

        Args:
            ontology_name: A list of strings representing ontologies

        Returns:
            A dictionary where each key is a file name and each value is a dictionary.

        Raises:
            ValueError: If the provided ontology name does not match any downloaded ontology files.
            ValueError: If the number of dictionary entries does not equal the number of files in the files list.
        """

        # find files that match user input
        ont_files = [glob.glob('resources/ontologies/' + str(e.lower()) + '*.pickle') for e in ontology_name][0]

        if len(ont_files) > 0:
            # input files to dictionary
            ontology_data = {}

            for f in [x for y in ont_files for x in y]:
                with open(f, 'rb') as _file:
                    f_name = re.search(r'(\w+_.*.)[^pickle]', f).group(1)
                    ontology_data[f_name] = pickle.load(_file)

            if len(ont_files) != len(ontology_data):
                raise ValueError('Unable to load all of files referenced in the file path')
            else:
                return ontology_data
        else:
            raise ValueError('Unable to find files that include that ontology name')
