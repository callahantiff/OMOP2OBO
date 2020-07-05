#!/usr/bin/env python
# -*- coding: utf-8 -*-


from .data_utils import *
from .kg_utils import *


__all__ = ['url_download', 'ftp_url_download', 'gzipped_ftp_url_download', 'zipped_url_download',
           'gzipped_url_download', 'data_downloader', 'gets_ontology_statistics', 'gets_ontology_classes',
           'gets_deprecated_ontology_classes']
