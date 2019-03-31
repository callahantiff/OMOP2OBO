##########################################################################################
# ontology_downloader.py
# version 1.0.0
# python 3.6.2
##########################################################################################


import os
import os.path
import requests
import subprocess

from datetime import *


class Ontology(object):
    """Download a list of ontologies listed in a text file.

    Attributes:
            data_path: A string containing a file path/name to a txt file storing URLs of sources to download.
            source_list (list): a list of URLs representing the data sources to download/process
            data_files (list): the full file path and name of each downloaded data source
    """

    def __init__(self, data_path):
        self.data_path = data_path
        self.source_list = []
        self.data_files = []
        self.metadata = []

    def file_parser(self):
        """Gather and verify sources to download."""

        # CHECK - file has data
        if os.stat(self.data_path).st_size == 0:
            raise Exception('ERROR: input file: {} is empty'.format(self.data_path))
        else:
            source_list = list(filter(None, [row.strip() for row in open(self.data_path).read().split('\n')]))
            good_sources = [url for url in source_list if 'purl.obolibrary.org/obo' in url]

            if len(source_list) == len(good_sources):
                self.source_list = source_list
            else:
                raise Exception('ERROR: Not all URLs were formatted properly')

    def get_source_list(self):
        """Data sources parsed from input text file."""

        return self.source_list

    def url_download(self):
        """Download each ontology from a list (including ontologies imported by each ontology."""

        print('\n')
        print('#' * 100)
        print('Downloading and processing ontologies')
        print('\n')

        for i in range(0, len(self.source_list)):
            source = self.source_list[i]
            file_prefix = source.split('/')[-1].split('.')[0]

            # check if ontology has already been downloaded
            if os.path.exists('./resources/ontologies/' + str(file_prefix) + '_with_imports.owl'):
                pass
            else:
                print('Downloading ' + str(file_prefix))

                try:
                    subprocess.check_call(['./resources/lib/owltools',
                                           str(source),
                                           '--merge-import-closure',
                                           '-o',
                                           './resources/ontologies/'
                                           + str(file_prefix) + '_with_imports.owl'])
                except subprocess.CalledProcessError as error:
                    print(error.output)

            self.data_files.append('./resources/ontologies/' + str(file_prefix) + '_with_imports.owl')

        if len(self.source_list) != len(self.data_files):
            raise Exception('ERROR: Not all URLs returned a data file')

    def get_data_files(self):
        """Data source paths."""

        return self.data_files

    def source_metadata(self):
        """Obtain metadata for each imported ontology."""

        self.metadata.append(['#' + str(datetime.utcnow().strftime('%a %b %d %X UTC %Y')) + ' \n'])

        for i in range(0, len(self.data_files)):
            source = self.data_files[i]
            file_info = requests.head(self.source_list[i])
            mod_info = file_info.headers[[x for x in file_info.headers.keys() if 'Date' in x][0]]
            mod_date = datetime.strptime(mod_info, '%a, %d %b %Y %X GMT').strftime('%m/%d/%Y')
            diff_date = (datetime.now() - datetime.strptime(mod_date, '%m/%d/%Y')).days

            source_metadata = ['DOWNLOAD_URL= %s' % str(self.source_list[i]),
                               'DOWNLOAD_DATE= %s' % str(datetime.now().strftime('%m/%d/%Y')),
                               'FILE_SIZE_IN_BYTES= %s' % str(os.stat(source).st_size),
                               'FILE_AGE_IN_DAYS= %s' % str(diff_date),
                               'DOWNLOADED_FILE= %s' % str(source)]

            self.metadata.append(source_metadata)

    def get_source_metadata(self):
        """Data source metadata."""

        return self.metadata

    def write_source_metadata(self):
        """Store metadata for imported ontologies."""

        print('\n')
        print('#' * 100)
        print('Writing downloaded ontology metadata')
        print('\n')

        write_location = str('/'.join(self.data_files[0].split('/')[:-1]) + '/') + 'ontology_metadata.txt'
        outfile = open(write_location, 'w')
        outfile.write(self.metadata[0][0])

        for i in range(1, len(self.metadata)):
            outfile.write(str(self.metadata[i][0]) + '\n')
            outfile.write(str(self.metadata[i][1]) + '\n')
            outfile.write(str(self.metadata[i][2]) + '\n')
            outfile.write(str(self.metadata[i][3]) + '\n')
            outfile.write(str(self.metadata[i][4]) + '\n')
            outfile.write('\n')

        outfile.close()
