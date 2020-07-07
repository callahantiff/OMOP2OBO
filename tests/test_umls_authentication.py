#!/usr/bin/env python
# -*- coding: utf-8 -*-


import responses

from mock import patch
from unittest import TestCase, mock

from omop2obo.utils import cui_search
from omop2obo.utils.umls_api import Authentication


class TestAuthentication(TestCase):
    """Class to test the UMLS Authentication."""

    def setUp(self):
        # set-up some mocking attributes
        self.service = "http://umlsks.nlm.nih.gov"
        self.uri = "https://utslogin.nlm.nih.gov"
        self.auth_endpoint = "/cas/v1/api-key"
        self.params1 = {'apikey': 'f12f22r8-y0122-5ui9-p2y2-ef608jk666e'}
        self.params2 = {'service': self.service}

        self.header = {"Content-type": "application/x-www-form-urlencoded",
                       "Accept": "text/plain", "User-Agent": "python"}

        return None

    @responses.activate
    def test_authentication_gettgt_method(self):
        """Tests the authentication gettgt method."""

        def request_callback(request):
            payload = '<!DOCTYPE HTML PUBLIC \\"-//IETF//DTD HTML 2.0//EN\\"><html><head><title>201 ' \
                      'Created</title></head><body><h1>TGT Created</h1><form ' \
                      'action="https://utslogin.nlm.nih.gov/cas/v1/api-key/TGT-410796' \
                      '-fakekey-cas" method="POST">Service:<input type="text" ' \
                      'name="service" value=""><br><input type="submit" value="Submit"></form></body></html>'
            resp_body = payload
            headers = self.header
            return 201, headers, resp_body

        # fake file connection
        responses.add_callback(
            responses.POST,
            self.uri + self.auth_endpoint,
            callback=request_callback,
            content_type='application/x-www-form-urlencoded')

        # test mocked download
        mock_open = mock.mock_open(read_data='TGT-410796-fakekey-cas')

        with patch('builtins.open', mock_open):
            auth = Authentication()
            tgt = auth.gettgt()
            self.assertEqual(tgt, 'https://utslogin.nlm.nih.gov/cas/v1/api-key/TGT-410796-fakekey-cas')

        return None

    @responses.activate
    def test_authentication_getst_method(self):
        """Tests the authentication getst method."""

        tgt = 'https://utslogin.nlm.nih.gov/cas/v1/api-key/TGT-410796-fakekey-cas'

        def request_callback(request):
            payload = 'ST-1234567-abcdefghijklmnopqrstuvwxyz-cas'
            resp_body = payload
            headers = self.header
            return 201, headers, resp_body

        # fake file connection
        responses.add_callback(
            responses.POST,
            tgt,
            callback=request_callback,
            content_type='application/x-www-form-urlencoded')

        # test mocked download
        mock_open = mock.mock_open(read_data='TGT-410796-fakekey-cas')

        with patch('builtins.open', mock_open):
            auth = Authentication()

            sgt = auth.getst(tgt)
            self.assertEqual(sgt, 'ST-1234567-abcdefghijklmnopqrstuvwxyz-cas')

        return None

    @responses.activate
    @patch('omop2obo.utils.umls_api.Authentication')
    def test_cui_search(self, mock_auth):
        """Tests the cui_search method."""

        mock_auth.return_value.gettgt.return_value = 'https://utslogin.nlm.nih.gov/cas/v1/api-key/TGT-fakekey-cas'
        mock_auth.return_value.getst.return_value = 'ST-1234567-abcdefghijklmnopqrstuvwxyz-cas'

        # creating expect response body
        body = '{"result": "fake results"}'

        # fake file connection
        responses.add(
            responses.GET,
            'https://uts-ws.nlm.nih.gov/rest/content/current/CUI/C0003635',
            status=200,
            content_type='application/json',
            body=body)

        data = cui_search('C0003635')

        # check result
        expected_result = 'fake results'
        self.assertEqual(expected_result, data)
