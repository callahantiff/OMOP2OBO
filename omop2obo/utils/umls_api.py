#!/usr/bin/env python
# -*- coding: utf-8 -*-

# UMLS SOFTWARE: https://github.com/HHS/uts-rest-api/blob/master/samples/python/Authentication.py


# import needed libraries
import json
import requests

from lxml.html import fromstring  # type: ignore  # pylint: disable=import-error
from typing import Dict


class Authentication(object):

    def __init__(self) -> None:
        self.service: str = "http://umlsks.nlm.nih.gov"
        self.uri: str = "https://utslogin.nlm.nih.gov"
        self.auth_endpoint: str = "/cas/v1/api-key"
        self.api_key: str = open("resources/programming/umls_api.txt").read()

    def gettgt(self):
        params = {'apikey': self.api_key}
        h = {"Content-type": "application/x-www-form-urlencoded",
             "Accept": "text/plain",
             "User-Agent": "python"}

        r = requests.post(self.uri + self.auth_endpoint, data=params, headers=h)
        response = fromstring(r.text)
        tgt = response.xpath('//form/@action')[0]

        return tgt

    def getst(self, tgt):
        params = {'service': self.service}
        h = {"Content-type": "application/x-www-form-urlencoded",
             "Accept": "text/plain",
             "User-Agent": "python"}

        r = requests.post(tgt, data=params, headers=h)
        st = r.text

        return st


def cui_search(cui: str) -> Dict:
    """This function takes a string containing the UMLS REST API URI, a string containing a UMLS CUI, and a string
    specifying UMLS version to query (default is set to query the most up to date version). Using this information the
    REST API is queried. Function returns a dictionary containing the results for a single query.

    Additional information can be found: https://documentation.uts.nlm.nih.gov/rest/concept/index.html.

    Args:
        cui: A string containing a UMLS CUI.

    Returns:
        A dictionary containing the results for a single query.
    """

    auth_client = Authentication()
    tgt = auth_client.gettgt()
    content_endpoint = '/rest/content/' + 'current' + '/CUI/' + str(cui)
    query = {'ticket': auth_client.getst(tgt)}

    # ping API
    r = requests.get('https://uts-ws.nlm.nih.gov' + content_endpoint, params=query)  # type: ignore
    r.encoding = 'utf-8'

    #
    # tries, r = 0, ''
    # while r == '' and tries != 20:
    #     try:
    #         r = requests.get('https://uts-ws.nlm.nih.gov' + content_endpoint, params=query)  # type: ignore
    #         r.encoding = 'utf-8'  # type: ignore
    #     except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
    #         sleep(10)
    #         tries += 1
    #     except requests.exceptions.RequestException as e:
    #         print(e)
    #         sys.exit(1)

    return json.loads(r.text)['result']  # type: ignore
