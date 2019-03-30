
from datetime import *
import requests
import os
import os.path
import subprocess


class Ontology(object):
    """Class creates an object that stores different aspects of data.

    The class takes as input a string that represents the file path/name of a text file that stores 1 to many
    different data sources. Each source is shown as a URL. The class is comprised of several methods that are all
    designed to perform a different function on the data sources. In the same directory that each type of data is
    downloaded to, a metadata file is created that stores important information on each of the files that is downloaded

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
        """Function verifies that the file contains data and then outputs the a list where each item is a line from the
        input text file. The function performs a check before processing any data to ensure that the data file is not
        empty. The function also verifies the URL for each ontology to ensure that they are OBO ontologies before
        processing any text
        """

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
        """Function returns the data sources parsed from input text file"""

        return self.source_list

    def url_download(self):
        """Function takes a string representing a file path/name to a text file as an argument. The function assumes
        that each item in the input file list is an URL to an OWL ontology. For each URL, the referenced ontology is
        downloaded, and used as input to an OWLTools command line argument (
        https://github.com/owlcollab/owltools/wiki/Extract-Properties-Command) that facilitating the downloading of
        ontologies imported by the primary ontology. The function will save the downloaded ontology + imported
        ontologies. The function outputs a list of URLs. The function performs two verification steps, the first to
        ensure that the command line argument passed to OWLTools returned data and the second is that for each URL
        provided as input, a data file is returned.
        """
        print('\n')
        print('#' * 100)
        print('Downloading and processing ontologies')
        print('\n')

        # for i in range(0, len(source_list)):
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

        # CHECK - all URLs returned an data file
        if len(self.source_list) != len(self.data_files):
            raise Exception('ERROR: Not all URLs returned a data file')

    def get_data_files(self):
        """Function returns the list of data sources with file path"""

        return self.data_files

    def source_metadata(self):
        """Function generates metadata for the data sources that it imports. Metadata includes the date of download,
        date of last modification to the file, the difference in days between last date of modification and current
        download date, file size in bytes, path to file, and URL from which the file was downloaded for each data source
        """

        self.metadata.append(['#' + str(datetime.utcnow().strftime('%a %b %d %X UTC %Y')) + ' \n'])

        for i in range(0, len(self.data_files)):
            source = self.data_files[i]
        # for i in range(0, len(data_files)):
        #     source = data_files[i]

            # get vars for metadata file
            file_info = requests.head(self.source_list[i])
            diff_date = ''

            if ".owl" in source:
                diff_date = "N/A"

            if ".owl" not in source:
                mod_info = file_info.headers[[x for x in file_info.headers.keys() if 'modified' in x.lower() or
                                              'Last-Modified' in x.lower()][0]]
                mod_date = datetime.strptime(mod_info, '%a, %d %b %Y %X GMT').strftime('%m/%d/%Y')

                # difference in days between download date and last modified date
                diff_date = (datetime.now() - datetime.strptime(mod_date, '%m/%d/%Y')).days

            # add metadata for each source as nested list
            source_metadata = ['DOWNLOAD_URL= %s' % str(self.source_list[i]),
                               'DOWNLOAD_DATE= %s' % str(datetime.now().strftime('%m/%d/%Y')),
                               'FILE_SIZE_IN_BYTES= %s' % str(os.stat(source).st_size),
                               'FILE_AGE_IN_DAYS= %s' % str(diff_date),
                               'DOWNLOADED_FILE= %s' % str(source)]

            self.metadata.append(source_metadata)

    def get_source_metadata(self):
        """Function returns the list of data source metadata"""

        return self.metadata

    def write_source_metadata(self):
        """Function generates a text file that stores metadata for the data sources that it imports.
        """

        # open file to write to and specify output location
        write_location = str('/'.join(self.data_files[0].split('/')[:-1]) + '/') + '_ontology_metadata.txt'
        outfile = open(write_location, 'w')

        outfile.write(self.metadata[0][0])
        print('Writing metadata \n')

        for i in range(1, len(self.metadata)):
            source = self.metadata[i]

            # write file
            outfile.write(str(source[0]) + '\n')
            outfile.write(str(source[1]) + '\n')
            outfile.write(str(source[2]) + '\n')
            outfile.write(str(source[3]) + '\n')
            outfile.write(str(source[4]) + '\n')
            outfile.write(str(source[5]) + '\n')
            outfile.write('\n')

        outfile.close()
