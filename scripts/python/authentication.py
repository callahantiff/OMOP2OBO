##############################################################################################
# authentication.py
# original: https://github.com/HHS/uts-rest-api/blob/master/samples/python/Authentication.py
# version 1.0.0
# python 3.6.2
##############################################################################################

import requests

from lxml.html import fromstring


class Authentication(object):

    def __init__(self):
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
