##########################################################################################
# ontology_downloader.py
# version 1.0.0
# date: 03.30.2019
# Python 3.6.2
##########################################################################################

from datetime import *
import requests
import os
import os.path
import subprocess


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
<<<<<<< HEAD
        """Download each ontology from a list (including ontologies imported by each ontology."""
=======
        """Function takes a string representing a file path/name to a text file as an argument. The function assumes
        that each item in the input file list is an URL to an OWL ontology. For each URL, the referenced ontology is
        downloaded, and used as input to an OWLTools command line argument (
        https://github.com/owlcollab/owltools/wiki/Extract-Properties-Command) that facilitating the downloading of
        ontologies imported by the primary ontology. The function will save the downloaded ontology + imported
        ontologies. The function outputs a list of URLs. The function performs two verification steps, the first to
        ensure that the command line argument passed to OWLTools returned data and the second is that for each URL
        provided as input, a data file is returned.
        """
>>>>>>> parent of a4384c7... updated gittignore and added resources files

        print('\n')
        print('#' * 100)
        print('Downloading and processing ontologies')
        print('\n')

        for i in range(0, len(self.source_list)):

            source = self.source_list[i]
            file_prefix = source.split('/')[-1].split('.')[0]
            print('Downloading ' + str(file_prefix))

            # set command line argument
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

<<<<<<< HEAD
        if len(self.source_list) != len(self.data_files):
            raise Exception('ERROR: Not all URLs returned a data file')
=======
            # CHECK - all URLs returned an data file
            if len(self.source_list) != i + 1:
                raise Exception('ERROR: Not all URLs returned a data file')
>>>>>>> parent of a4384c7... updated gittignore and added resources files

    def get_data_files(self):
        """Data source paths."""

        return self.data_files

    def source_metadata(self):
<<<<<<< HEAD
        """Obtain metadata for each imported ontology."""
=======
        """Function generates metadata for the data sources that it imports. Metadata includes the date of download,
        date of last modification to the file, the difference in days between last date of modification and current
        download date, file size in bytes, path to file, and URL from which the file was downloaded for each data source

            :param
                data_file (list): each item in the list contains the full path and filename of an input data source

             :return:
                 metadata (list): nested list where first item is today's date and each remaining item is a list that
                 contains metadata information for each source that was downloaded
        """
>>>>>>> parent of a4384c7... updated gittignore and added resources files

        self.metadata.append(['#' + str(datetime.utcnow().strftime('%a %b %d %X UTC %Y')) + ' \n'])

        for i in range(0, len(self.data_files)):
            source = self.data_files[i]
            file_info = requests.head(self.source_list[i])
<<<<<<< HEAD
            mod_info = file_info.headers[[x for x in file_info.headers.keys() if 'Date' in x][0]]
            mod_date = datetime.strptime(mod_info, '%a, %d %b %Y %X GMT').strftime('%m/%d/%Y')
            diff_date = (datetime.now() - datetime.strptime(mod_date, '%m/%d/%Y')).days
=======
            # file_info = requests.head(source_list[i])
            diff_date = ''
            mod_date = ''

            if ".owl" in source:
                mod_date = "NONE"
                diff_date = "N/A"

            if ".owl" not in source:
                mod_info = file_info.headers[[x for x in file_info.headers.keys() if 'modified' in x.lower() or
                                              'Last-Modified' in x.lower()][0]]
                mod_date = datetime.strptime(mod_info, '%a, %d %b %Y %X GMT').strftime('%m/%d/%Y')

                # difference in days between download date and last modified date
                diff_date = (datetime.now() - datetime.strptime(mod_date, '%m/%d/%Y')).days
>>>>>>> parent of a4384c7... updated gittignore and added resources files

            source_metadata = ['DOWNLOAD_URL= %s' % str(self.source_list[i]),
                               'DOWNLOAD_DATE= %s' % str(datetime.now().strftime('%m/%d/%Y')),
                               'FILE_SIZE_IN_BYTES= %s' % str(os.stat(source).st_size),
                               'FILE_AGE_IN_DAYS= %s' % str(diff_date),
                               'DOWNLOADED_FILE= %s' % str(source),
                               'FILE_LAST_MOD_DATE= %s' % str(mod_date)]

            self.metadata.append(source_metadata)

    def get_source_metadata(self):
        """Data source metadata."""

        return self.metadata

    def write_source_metadata(self):
<<<<<<< HEAD
        """Store metadata for imported ontologies."""
=======
        """Function generates a text file that stores metadata for the data sources that it imports.

        :param
            metadata (list): nested list where first item is today's date and each remaining item is a list that
                 contains metadata information for each source that was downloaded

            data_type (str): the type of data files being processed

        :return:
            writes a text file storing metadata for the imported ontologies and names it

        """
>>>>>>> parent of a4384c7... updated gittignore and added resources files

        print('\n')
        print('#' * 100)
        print('Writing downloaded ontology metadata')
        print('\n')

        write_location = str('/'.join(self.data_files[0].split('/')[:-1]) + '/') + 'ontology_metadata.txt'
        outfile = open(write_location, 'w')
        outfile.write(self.metadata[0][0])

        for i in range(1, len(self.metadata)):
            source = self.metadata[i]

            # write file
            outfile.write(str(source[0]) + '\n')
            outfile.write(str(source[1]) + '\n')
            outfile.write(str(source[2]) + '\n')
            outfile.write(str(source[3]) + '\n')
            outfile.write(str(source[4]) + '\n')
            outfile.write('\n')

        outfile.close()
