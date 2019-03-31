#############################################################################
# umls_api.py
# resource: https://github.com/HHS/uts-rest-api/tree/master/samples/python
# version 1.0.0
# python 3.6.2
#############################################################################


import json
import sys

from time import sleep

from scripts.python.authentication import *


def term_search(term):
    """This function queries the UMLS API and returns a list of dictionaries containing the results of the query.
    Additional input/output arguments for query can be found:
    https://documentation.uts.nlm.nih.gov/rest/search/index.html.

    Args:
        term: a string containing a term

    Returns:
        list of dictionaries containing the results of the query
    """

    auth_client = Authentication()
    content_endpoint = '/rest/search/' + 'current'
    page_number = 0
    umls_results = []
    result = ''

    while result != 'NO RESULTS':
        tries = 0
        r = ''

        while r == '' and tries != 20:
            try:
                ticket = auth_client.getst(auth_client.gettgt())
                page_number += 1
                query = {'string': term, 'ticket': ticket, 'pageNumber': page_number, 'sabs': 'SNOMEDCT_US'}
                r = requests.get('https://uts-ws.nlm.nih.gov' + content_endpoint, params=query)
                r.encoding = 'utf-8'
            except requests.exceptions.Timeout:
                sleep(10)
                tries += 1
            except requests.exceptions.ConnectionError:
                sleep(10)
                tries += 1
            except requests.exceptions.RequestException as e:
                print(e)
                sys.exit(1)

        # load results
        items = json.loads(r.text)
        json_data = items['result']

        # test if results were found
        if json_data['results'][0]['name'] == 'NO RESULTS':
            result = json_data['results'][0]['name']
        else:
            umls_results.append(json_data['results'][0])

    out_message = 'UMLS API returned: %d' % len(umls_results) + ' result(s) for ' + str(term)

    # print('\n')
    # print('=' * len(out_message))
    # print(out_message)
    # print('=' * len(out_message))
    # print('\n')

    return umls_results


def code_search(code):
    """
    This function takes a string containing the UMLS REST API URI, a string containing a source concept code, and a
    string specifying UMLS version to query (default is set to query the most up to date version). Using this
    information the REST API is queried. Function returns a list of dictionaries containing the results of the query.
    Additional input/output arguments for query can be found:
    https://documentation.uts.nlm.nih.gov/rest/search/index.html.

    Args:
        code: a string containing a source concept code

    Returns:
        list of dictionaries containing the results of the  query
    """

    # get session ticket
    auth_client = Authentication()
    content_endpoint = '/rest/search/' + 'current'
    page_number = 0
    umls_results = []
    result = ''

    while result != 'NO RESULTS':
        tries = 0
        r = ''
        while r == '' and tries != 20:
            try:
                # generate a new service ticket for each page if needed
                ticket = auth_client.getst(auth_client.gettgt())
                page_number += 1
                query = {'string': code, 'ticket': ticket, 'pageNumber': page_number, 'inputType': 'sourceUi',
                         'searchType': 'exact', 'includeObsolete': 'true', 'includeSuppressible': 'true'}

                r = requests.get('https://uts-ws.nlm.nih.gov' + content_endpoint, params=query)
                r.encoding = 'utf-8'

            except requests.exceptions.Timeout as e:
                print('Timeout ' + str(e))
                print('\n')

                # sleep and then try again
                sleep(10)
                tries += 1

                # generate a new service ticket for each page if needed
                ticket = auth_client.getst(auth_client.gettgt())
                page_number += 1
                query = {'string': code, 'ticket': ticket, 'pageNumber': page_number, 'inputType': 'sourceUi',
                         'searchType': 'exact', 'includeObsolete': 'true', 'includeSuppressible': 'true'}

                r = requests.get('https://uts-ws.nlm.nih.gov' + content_endpoint, params=query)
                r.encoding = 'utf-8'

            except requests.exceptions.ConnectionError as e:
                print('ConnectionError ' + str(e))
                print('\n')

                # sleep and then try again
                sleep(10)
                tries += 1

                # generate a new service ticket for each page if needed
                ticket = auth_client.getst(auth_client.gettgt())
                page_number += 1
                query = {'string': code, 'ticket': ticket, 'pageNumber': page_number, 'inputType': 'sourceUi',
                         'searchType': 'exact', 'includeObsolete': 'true', 'includeSuppressible': 'true'}
                r = requests.get('https://uts-ws.nlm.nih.gov' + content_endpoint, params=query)
                r.encoding = 'utf-8'

            except requests.exceptions.RequestException as e:
                print(e)
                print('\n')
                sys.exit(1)

        # load results
        items = json.loads(r.text)
        json_data = items['result']

        # test if results were found
        if json_data['results'][0]['name'] == 'NO RESULTS':
            result = json_data['results'][0]['name']
        else:
            umls_results.append(json_data['results'][0]['ui'])

    out_message = 'UMLS API returned: %d' % len(umls_results) + ' result(s) for ' + str(code)

    # print('\n')
    # print('=' * len(out_message))
    # print(out_message)
    # print('=' * len(out_message))
    # print('\n')

    return umls_results


def cui_search(cui):
    """This function takes a string containing the UMLS REST API URI, a string containing a UMLS CUI, and a string
    specifying UMLS version to query (default is set to query the most up to date version). Using this information the
    REST API is queried. Function returns a dictionary containing the results for a single query. Additional input
    and output information can be found: https://documentation.uts.nlm.nih.gov/rest/concept/index.html.

    Args:
        cui: a string containing a UMLS CUI

    Returns:
        dictionary containing the results for a single query
    """

    # get session ticket
    auth_client = Authentication()
    tgt = auth_client.gettgt()
    content_endpoint = '/rest/content/' + 'current' + '/CUI/' + str(cui)
    query = {'ticket': auth_client.getst(tgt)}

    # request results and track certain exceptions
    tries = 0
    r = ''
    while r == '' and tries != 20:

        try:
            r = requests.get('https://uts-ws.nlm.nih.gov' + content_endpoint, params=query)
            r.encoding = 'utf-8'

        except requests.exceptions.Timeout:
            sleep(10)
            tries += 1

        except requests.exceptions.ConnectionError:
            sleep(10)
            tries += 1

        except requests.exceptions.RequestException as e:
            # catastrophic error. bail.
            print(e)
            sys.exit(1)

    # retrieve results
    items = json.loads(r.text)
    json_data = items['result']

    return json_data
