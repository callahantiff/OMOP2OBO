from progressbar import ProgressBar, FormatLabel, Percentage, Bar
from rdflib import Graph


class RDFGraph(object):
    """Classes creates an RDF graph from an OWL file and then performs queries to return DbXRefs, synonyms, and labels.

    Attributes:
        graph: A string that contains a filepath to an OWL file.
    """

    def __init__(self, graph):
        """ ."""
        self.graph = Graph().parse(graph, format='xml')

    def ont_dictionary(self):
        """Function queries an RDF graph for non-deprecated classes.

        Raises:
            ValueError: An error occurred when the query returned no results.
        """

        print('Running Query to Identify all Ontology Classes \n')

        query_results = self.graph.query(
            """SELECT DISTINCT ?c ?c_label ?defn
               WHERE {
                  ?c rdf:type owl:Class .
                  ?c rdfs:label ?c_label .
                  optional {?c obo:IAO_0000115 ?defn}
                  minus {?c owl:deprecated true}
                  }
               """, initNs={'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
                            'owl': 'http://www.w3.org/2002/07/owl#',
                            'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#',
                            'obo': 'http://purl.obolibrary.org/obo/'})

        # create progress bar
        widgets = [Percentage(), Bar(), FormatLabel('(elapsed: %(elapsed)s)')]
        pbar = ProgressBar(widgets=widgets, maxval=len(query_results))

        # create variable to store results
        valid_res = {}

        print('Processing Query Results \n')

        for row in pbar(query_results):
            if row[2] is not None:
                valid_res[str(row[1].decode('ascii', 'ignore')).lower()] = [str(row[0]),
                                                                            str(row[2].encode('ascii',
                                                                                              'ignore')).lower()]
            else:
                valid_res[str(row[1].decode('ascii', 'ignore')).lower()] = [str(row[0]), '']

        # close progress bar
        pbar.finish()

        # verify we have results
        if not len(valid_res) > 1:
            raise ValueError('Error - did not return any classes for graph: {0}'.format(len(valid_res)))
        else:
            return valid_res

    def dbxref(self, codes):
        """Function queries an RDF graph and returns DbXRefs.

        Args:
            codes: A list of strings that represent terminology names.

        Raises:
            ValueError: An error occurred when the query returned no results.
        """

        print('Running Query to Identify all DbXRefs \n')

        xref = {}

        query_results = self.graph.query(
            """SELECT DISTINCT ?dbref ?c ?c_label 
               WHERE {
                  ?c rdf:type owl:Class .
                  ?c oboInOwl:hasDbXref ?dbref .
                  ?c rdfs:label ?c_label .
                  minus {?c owl:deprecated true}
                  }
               """, initNs={'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
                            'owl': 'http://www.w3.org/2002/07/owl#',
                            'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#'})

        # create progress bar
        widgets = [Percentage(), Bar(), FormatLabel('(elapsed: %(elapsed)s)')]
        pbar = ProgressBar(widgets=widgets, maxval=len(query_results))

        print('Processing Query Results \n')

        for row in pbar(query_results):
            # create dictionary of DbXRefs
            for code in codes:
                if code in str(row[0]):
                    key = str(code) + ':' + str(str(row[0]).split(':')[-1])

                    if key in xref.keys():
                        xref[key] += [str(row[1]), str(row[2])]
                    else:
                        xref[key] = [str(row[1]), str(row[2])]

        pbar.finish()

        # verify we have results
        if not len(xref) > 1:
            raise ValueError('Error - did not return any DbXRefs for graph: {0}'.format(len(xref)))
        else:
            return xref

    def synonym(self):
        """Function queries an RDF graph and returns exact, broad, narrow, and related synonyms.

        Raises:
            ValueError: An error occurred when the query returned no results.
        """

        print('Running Query to Identify all synonyms \n')

        # create variable to store results
        syn = {}

        query_results = self.graph.query(
            """SELECT DISTINCT ?syn ?c ?c_label ?p
               WHERE {
                  ?c rdf:type owl:Class .
                  ?c ?p ?syn .
                  ?c rdfs:label ?c_label .

                  FILTER(?p in (oboInOwl:hasExactSynonym, oboInOwl:hasBroadSynonym, oboInOwl:hasNarrowSynonym,
                  oboInOwl:hasRelatedSynonym))

                  minus {?c owl:deprecated true}
                  }
               """, initNs={'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
                            'owl': 'http://www.w3.org/2002/07/owl#',
                            'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#'})

        # create progress bar
        widgets = [Percentage(), Bar(), FormatLabel('(elapsed: %(elapsed)s)')]
        pbar = ProgressBar(widgets=widgets, maxval=len(query_results))

        print('Processing Query Results \n')

        for row in pbar(query_results):
            key = str(row[0].encode('ascii', errors='replace')).lower()

            if key in syn.keys():
                if str(row[1]) not in syn[key] and str(row[2].encode('ascii',
                                                                     errors='replace').lower()) not in syn[key]:
                    syn[key] += [str(row[1]), str(row[2].encode('ascii', errors='replace').lower())]
            else:
                syn[key] = [str(row[1]), str(row[2].encode('ascii', errors='replace').lower())]

        pbar.finish()

        if not len(syn) > 1:
            raise ValueError('Error - did not return any DbXRefs for graph: {0}'.format(len(syn)))
        else:
            return syn
