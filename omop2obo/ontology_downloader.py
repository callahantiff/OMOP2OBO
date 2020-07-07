#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import glob
import os
import os.path
import re
import subprocess

from datetime import *
from tqdm import tqdm  # type: ignore
from typing import Dict, List

from omop2obo.utils import data_downloader, gets_ontology_statistics


class OntologyDownloader(object):
    """Download a list of ontologies listed in a text file.

    Attributes:
            data_path: a string containing a file path/name to a txt file storing URLs of sources to download.
            source_list: a list of URLs representing the data sources to download/process.
            data_files: the full file path and name of each downloaded data source.
            metadata: a list containing metadata information for each downloaded ontology.

    Raises:
        TypeError: If the file pointed to by data_path is not type str.
        IOError: If the file pointed to by data_path does not exist.
        TypeError: If the file pointed to by data_path is empty.
    """

    def __init__(self, data_path: str) -> None:

        # read in data source file
        if not isinstance(data_path, str):
            raise TypeError('data_path must be type str.')
        elif not os.path.exists(data_path):
            raise OSError('The {} file does not exist!'.format(data_path))
        elif os.stat(data_path).st_size == 0:
            raise TypeError('Input file: {} is empty'.format(data_path))
        else:
            self.data_path: str = data_path

        self.source_list: Dict[str, str] = {}
        self.data_files: Dict[str, str] = {}
        self.metadata: List[List[str]] = []

    def parses_resource_file(self) -> None:
        """Parses data from a file and outputs a list where each item is a line from the input text file.

        Returns:
            source_list: A dictionary, where the key is the type of data and the value is the file path or url. See
                example below: {'chemical-gomf', 'http://ctdbase.org/reports/CTD_chem_go_enriched.tsv.gz',
                                'phenotype': 'http://purl.obolibrary.org/obo/hp.owl'
                                }

        """

        with open(self.data_path, 'r') as file_name:
            try:
                self.source_list = {row.strip().split(',')[0]: row.strip().split(',')[1].strip()
                                    for row in file_name.read().splitlines()}
            except IndexError:
                raise Exception('ERROR: input file: {} has incorrectly formatted data'.format(self.data_path))
        file_name.close()

        return None

    def downloads_data_from_url(self, owltools_location: str = './omop2obo/libs/owltools') -> None:
        """Takes a string representing a file path/name to a text file as an argument. The function assumes
        that each item in the input file list is an URL to an OWL/OBO ontology.

        For each URL, the referenced ontology is downloaded, and used as input to an OWLTools command line argument (
        https://github.com/owlcollab/owltools/wiki/Extract-Properties-Command), which facilitates the downloading of
        ontologies that are imported by the primary ontology. The function will save the downloaded ontology + imported
        ontologies.

        Args:
            owltools_location: A string pointing to the location of the owl tools library.

        Returns:
            data_files: A dictionary mapping each source identifier to the local location where it was downloaded.
                For example: {'chemical-gomf', 'resources/edge_data/chemical-gomf_CTD_chem_go_enriched.tsv',
                              'phenotype': 'resources/ontologies/hp_with_imports.owl'
                              }
        """

        # check data before download
        self.parses_resource_file()

        # set location where to write data
        file_loc = '/'.join(self.data_path.split('/')[:-1]) + '/ontologies/'
        print('\n ***Downloading Data: to "{0}" ***\n'.format(file_loc))

        # process data
        for i in tqdm(self.source_list.keys()):
            source = self.source_list[i]
            file_prefix = source.split('/')[-1].split('.')[0]
            write_loc = file_loc + file_prefix

            print('\nDownloading: {}'.format(str(file_prefix)))

            # don't re-download ontologies
            if any(x for x in os.listdir(file_loc) if re.sub('_without.*.owl', '', x) == file_prefix):
                self.data_files[i] = glob.glob(file_loc + '*' + file_prefix + '*.owl')[0]
            else:
                if 'purl' in source:
                    try:
                        subprocess.check_call([os.path.abspath(owltools_location),
                                               str(source),
                                               '-o',
                                               str(write_loc) + '_without_imports.owl'])

                        self.data_files[i] = str(write_loc) + '_without_imports.owl'
                    except subprocess.CalledProcessError as error:
                        print(error.output)
                else:
                    data_downloader(source, file_loc, str(file_prefix) + '_without_imports.owl')
                    self.data_files[i] = file_loc + str(file_prefix) + '_without_imports.owl'

            # print stats
            gets_ontology_statistics(file_loc + str(file_prefix) + '_without_imports.owl',
                                     os.path.abspath(owltools_location))

        # generate metadata
        self.generates_source_metadata()

        return None

    def generates_source_metadata(self):
        """Obtain metadata for each imported ontology."""

        print('\n*** Generating Metadata ***\n')
        self.metadata.append(['#' + str(datetime.utcnow().strftime('%a %b %d %X UTC %Y')) + ' \n'])

        for i in tqdm(self.data_files.keys()):
            source = self.data_files[i]
            source_metadata = ['DOWNLOAD_URL= %s' % str(self.source_list[i].split(', ')[-1]),
                               'DOWNLOAD_DATE= %s' % str(datetime.now().strftime('%m/%d/%Y')),
                               'FILE_SIZE_IN_BYTES= %s' % str(os.stat(source).st_size),
                               'DOWNLOADED_FILE_LOCATION= %s' % str(source)]

            self.metadata.append(source_metadata)

        # write metadata
        self._writes_source_metadata()

        return None

    def _writes_source_metadata(self):
        """Store metadata for imported ontologies."""

        print('\n*** Writing Metadata ***\n')

        # open file to write to and specify output location
        write_loc_part = str('/'.join(list(self.data_files.values())[0].split('/')[:-1]) + '/')
        outfile = open(write_loc_part + 'ontology_source_metadata.txt', 'w')
        outfile.write('=' * 35 + '\n{}'.format(self.metadata[0][0]) + '=' * 35 + '\n\n')

        for i in tqdm(range(1, len(self.data_files.keys()) + 1)):
            outfile.write(str(self.metadata[i][0]) + '\n')
            outfile.write(str(self.metadata[i][1]) + '\n')
            outfile.write(str(self.metadata[i][2]) + '\n')
            outfile.write(str(self.metadata[i][3]) + '\n')
            outfile.write('\n')

        outfile.close()

        return None
