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

from omop2obo.utils import gets_ontology_statistics


class OntologyDownloader(object):
    """Class downloads a list of ontologies listed in a text file and extract and write metadata about each downloaded
    ontology to local repository (resources/ontologies).

    For additional detail see README: https://github.com/callahantiff/OMOP2OBO/blob/enabling_bidirectional_mapping/resources/ontologies/README.md

    Attributes:
            data_path: a string containing a file path/name to a txt file storing URLs of sources to download.
            source_list: a list of URLs representing the data sources to download/process.
            data_files: the full file path and name of each downloaded data source.
            metadata: a list containing metadata information for each downloaded ontology.

    Raises:
        TypeError: If the file pointed to by data_path is not type str.
        IOError: If the file pointed to by data_path does not exist.
        IndexError: If the file pointed to by data_path is empty.
    """

    def __init__(self, data_path: str, stats_flag: bool = False) -> None:

        if not isinstance(data_path, str): raise TypeError('data_path must be type str.')
        elif not os.path.exists(data_path): raise OSError('The {} file does not exist!'.format(data_path))
        elif os.stat(data_path).st_size == 0: raise IndexError('Input file: {} is empty'.format(data_path))
        else: self.data_path: str = data_path
        self.source_list: Dict[str, str] = {}
        self.data_files: Dict[str, str] = {}
        self.metadata: List[List[str]] = []
        self.stats: bool = stats_flag

    def parses_resource_file(self) -> None:
        """Parses data from a file and outputs a list where each item is a line from the input text file.

        Returns:
            source_list: A dictionary, where the key is the type of data and the value is the file path or url. See
                example: {'hp': 'http://purl.obolibrary.org/obo/hp.owl'}.

        Raises:
            ValueError: If the data within the data_path file is not formatted correctly (comma-delimited) and is not of
                the right type (.owl or .obo).
        """

        with open(self.data_path, 'r') as file_name:
            for row in file_name.read().splitlines():
                if ',' in row and ('.owl' in row or '.obo' in row):
                    self.source_list[row.strip().split(',')[0]] = row.strip().split(',')[1].strip()
                else: raise ValueError('ERROR: file: {} has incorrectly formatted data'.format(self.data_path))
        file_name.close()

        return None

    def _writes_source_metadata(self) -> None:
        """Writes metadata for all downloaded ontologies to resources/ontologies/ontology_source_metadata.txt."""

        # open file to write to and specify output location
        write_loc_part = str('/'.join(list(self.data_files.values())[0].split('/')[:-1]) + '/')
        loc = write_loc_part + 'ontology_source_metadata.txt'
        print('\t- Writing Metadata for Downloaded Ontologies to: {}'.format(loc))
        outfile = open(loc, 'w')
        outfile.write('=' * 35 + '\n{}'.format(self.metadata[0][0]) + '=' * 35 + '\n\n')
        for i in tqdm(range(1, len(self.data_files.keys()) + 1)):
            outfile.write(str(self.metadata[i][0]) + '\n')
            outfile.write(str(self.metadata[i][1]) + '\n')
            outfile.write(str(self.metadata[i][2]) + '\n')
            outfile.write(str(self.metadata[i][3]) + '\n')
            outfile.write('\n')

        outfile.close()

        return None

    def generates_source_metadata(self) -> None:
        """Obtains metadata for each downloaded ontology."""

        self.metadata.append(['#' + str(datetime.utcnow().strftime('%a %b %d %X UTC %Y')) + ' \n'])
        for i in tqdm(self.data_files.keys()):
            source = self.data_files[i]
            source_metadata = ['DOWNLOAD_URL= %s' % str(self.source_list[i].split(', ')[-1]),
                               'DOWNLOAD_DATE= %s' % str(datetime.now().strftime('%m/%d/%Y')),
                               'FILE_SIZE_IN_BYTES= %s' % str(os.stat(source).st_size),
                               'DOWNLOADED_FILE_LOCATION= %s' % str(source)]
            self.metadata.append(source_metadata)
        self._writes_source_metadata()

        return None

    def downloads_data_from_url(self, owltools: str = './omop2obo/libs/owltools') -> None:
        """Takes a string representing a file path/name to a text file as an argument. The function assumes
        that each item in the input file list is a URL to an OWL/OBO ontology.

        For each URL, the referenced ontology is downloaded, and used as input to an OWLTools command line argument
        (https://github.com/owlcollab/owltools/wiki/Extract-Properties-Command), which facilitates the downloading of
        ontologies that are imported by the primary ontology. The function will save the downloaded ontology + imported
        ontologies.

        Args:
            owltools: A string pointing to the location of the OWLTools library.

        Returns:
            data_files: A dictionary mapping each source identifier to the local location where it was downloaded.
                For example: {'hp': 'resources/ontologies/hp.owl'}
        """

        # check data before download and set location where to write data
        self.parses_resource_file()
        file_loc = '/'.join(self.data_path.split('/')[:-1]) + '/ontologies/'

        # process data
        print('\n' + '===' * 15 + '\nDOWNLOADING OBO FOUNDRY ONTOLOGIES\n' + '===' * 15)

        for i in tqdm(self.source_list.keys()):
            source = self.source_list[i]; file_prefix = source.split('/')[-1].split('.')[0]
            write_loc = file_loc + file_prefix
            print('--> Downloading Ontology: {} to {}'.format(str(file_prefix), file_loc))
            # only download each ontology if it's not in local directory
            if any(x for x in os.listdir(file_loc) if re.sub('.owl', '', x) == file_prefix):
                self.data_files[i] = glob.glob(file_loc + '*' + file_prefix + '*.owl')[0]
                if self.stats:
                    print('\t- Obtain Ontology Statistics')
                    stats = gets_ontology_statistics(file_loc + str(file_prefix) + '.owl', os.path.abspath(owltools))
                    print(stats)
            else:
                try:
                    # subprocess.check_call([os.path.abspath(owltools), str(source), '-o', str(write_loc) + '.owl'])
                    os.system('wget -O {} {}'.format(write_loc + '.owl', source))
                    self.data_files[i] = str(write_loc) + '.owl'
                except subprocess.CalledProcessError as error: print(error.output)
                print('\t- Obtain Ontology Statistics')
                stats = gets_ontology_statistics(file_loc + str(file_prefix) + '.owl', os.path.abspath(owltools))
                print(stats)
        print('--> Generate and Write Metadata for all Ontologies to Local Directory')
        self.generates_source_metadata()

        return None
