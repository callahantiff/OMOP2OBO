#!/usr/bin/env python
# -*- coding: utf-8 -*-

from validate_version_code import validate_version_code

from omop2obo.__version__ import __version__


def test_version():
    assert validate_version_code(__version__)
