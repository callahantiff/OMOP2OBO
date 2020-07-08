#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data PreProcessing Utility Functions.

Downloads Data from a Url
* url_download
* ftp_url_download
* gzipped_ftp_url_download
* zipped_url_download
* gzipped_url_download
* data_downloader

Pandas DataFrame manipulations
* data_frame_subsetter
* data_frame_supersetter

Dictionary manipulations
* merge_dictionaries

"""

# import needed libraries
import ftplib
import gzip
import os
import pandas as pd  # type: ignore
import re
import requests
import shutil
import urllib3  # type: ignore

from contextlib import closing
from io import BytesIO
from typing import Dict, List, Tuple  # type: ignore
from urllib.request import urlopen
from zipfile import ZipFile

# ENVIRONMENT WARNINGS
# WARNING 1 - Pandas: disable chained assignment warning rationale:
# https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas
pd.options.mode.chained_assignment = None

# WARNING 2 - urllib3: disable insecure request warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def url_download(url: str, write_location: str, filename: str) -> None:
    """Downloads a file from a URL.

    Args:
        url: A string that points to the location of a temp mapping file that needs to be processed.
        write_location: A string that points to a file directory.
        filename: A string containing a filepath for where to write data to.

    Returns:
        None.

    Raises:
        HTTPError: If the response returns a status code other than 200.
    """

    print('Downloading Data from {}'.format(url))
    r = requests.get(url, allow_redirects=True, verify=False)

    if r.ok is False:
        raise requests.HTTPError('{status}: Could not downloaded data from {url}'.format(status=r.status_code, url=url))
    else:
        data = None
        if 'Content-Length' in r.headers:
            while r.ok and int(r.headers['Content-Length']) < 1000:
                r = requests.get(url, allow_redirects=True, verify=False)
            data = r.content
        else:
            if len(r.content) > 10:
                data = r.content

        # download and save data
        if data:
            with open(write_location + '{filename}'.format(filename=filename), 'wb') as outfile:
                outfile.write(data)
            outfile.close()

    return None


def ftp_url_download(url: str, write_location: str, filename: str) -> None:
    """Downloads a file from an ftp server.

    Args:
        url: A string that points to the location of a temp mapping file that needs to be processed.
        write_location: A string that points to a file directory.
        filename: A string containing a filepath for where to write data to.

    Returns:
        None.
    """

    print('Downloading Data from FTP Server: {}'.format(url))

    with closing(urlopen(url)) as downloaded_data:
        with open(write_location + '{filename}'.format(filename=filename), 'wb') as outfile:
            shutil.copyfileobj(downloaded_data, outfile)
        outfile.close()

    return None


def gzipped_ftp_url_download(url: str, write_location: str, filename: str) -> None:
    """Downloads a gzipped file from an ftp server.

    Args:
        url: A string that points to the location of a temp mapping file that needs to be processed.
        write_location: A string that points to a file directory.
        filename: A string containing a filepath for where to write data to.

    Returns:
        None.
    """

    # get ftp server info
    server = url.replace('ftp://', '').split('/')[0]
    directory = '/'.join(url.replace('ftp://', '').split('/')[1:-1])
    file = url.replace('ftp://', '').split('/')[-1]
    write_loc = write_location + '{filename}'.format(filename=file)

    # download ftp gzipped file
    print('Downloading Gzipped data from FTP Server: {}'.format(url))
    with closing(ftplib.FTP(server)) as ftp, open(write_loc, 'wb') as fid:
        ftp.login()
        ftp.cwd(directory)
        ftp.retrbinary('RETR {}'.format(file), fid.write)

    # read in gzipped file,uncompress, and write to directory
    print('Decompressing and Writing Gzipped Data to File')
    with gzip.open(write_loc, 'rb') as fid_in:
        with open(write_loc.replace('.gz', ''), 'wb') as file_loc:
            file_loc.write(fid_in.read())

    # change filename and remove gzipped and original files
    if filename != '':
        os.rename(re.sub('.gz|.zip', '', write_loc), write_location + filename)

    # remove compressed file
    os.remove(write_loc)

    return None


def zipped_url_download(url: str, write_location: str, filename: str = '') -> None:
    """Downloads a zipped file from a URL.

    Args:
        url: A string that points to the location of a temp mapping file that needs to be processed.
        write_location: A string that points to a file directory.
        filename: A string containing a filepath for where to write data to.

    Returns:
        None.

    Raises:
        HTTPError: If the response returns a status code other than 200.
    """

    print('Downloading Zipped Data from {}'.format(url))
    r = requests.get(url, allow_redirects=True)

    if r.ok is False:
        raise requests.HTTPError('{status}: Could not downloaded data from {url}'.format(status=r.status_code, url=url))
    else:
        with r as zip_data:
            with ZipFile(BytesIO(zip_data.content)) as zip_file:
                zip_file.extractall(write_location[:-1])
        zip_data.close()

        # change filename
        if filename != '':
            os.rename(write_location + re.sub('.gz|.zip', '', url.split('/')[-1]), write_location + filename)

    return None


def gzipped_url_download(url: str, write_location: str, filename: str) -> None:
    """Downloads a gzipped file from a URL.

    Args:
        url: A string that points to the location of a temp mapping file that needs to be processed.
        write_location: A string that points to a file directory.
        filename: A string containing a filepath for where to write data to.

    Returns:
        None.

    Raises:
        HTTPError: If the response returns a status code other than 200.
    """

    print('Downloading Gzipped Data from {}'.format(url))
    r = requests.get(url, allow_redirects=True, verify=False)

    if r.ok is False:
        raise requests.HTTPError('{status}: Could not downloaded data from {url}'.format(status=r.status_code, url=url))
    else:
        with open(write_location + '{filename}'.format(filename=filename), 'wb') as outfile:
            outfile.write(gzip.decompress(r.content))
        outfile.close()

    return None


def data_downloader(url: str, write_location: str, filename: str = '') -> None:
    """Downloads data from a URL and saves the file to the `/resources/processed_data/unprocessed_data' directory.

    Args:
        url: A string that points to the location of a temp mapping file that needs to be processed.
        write_location: A string that points to a file directory.
        filename: A string containing a filepath for where to write data to.

    Returns:
        None.
    """

    # get filename from url
    file = re.sub('.gz|.zip', '', filename) if filename != '' else re.sub('.gz|.zip', '', url.split('/')[-1])

    if '.zip' in url:
        zipped_url_download(url, write_location, file)
    elif '.gz' in url or '.gz' in filename:
        if 'ftp' in url:
            gzipped_ftp_url_download(url, write_location, file)
        else:
            gzipped_url_download(url, write_location, file)
    else:
        if 'ftp' in url:
            ftp_url_download(url, write_location, file)
        else:
            url_download(url, write_location, file)

    return None


def data_frame_subsetter(data: pd.DataFrame, primary_key: str, subset_columns: List) -> pd.DataFrame:
    """Takes a Pandas DataFrame and subsets it such that each subset represents an original column of codes, OMOP
    concept identifiers, and a string containing the code's column name in the original DataFrame. An example of
    the input and generated output is shown below.

        INPUT:
              CONCEPT_ID CONCEPT_SOURCE_CODE  UMLS_CUI   UMLS_CODE        UMLS_SEM_TYPE
            0    4331309            22653005  C0729608    22653005  Disease or Syndrome
            1    4331310            22653011  C4075981    22653005  Disease or Syndrome

        OUTPUT:
              CONCEPT_ID                CODE          CODE_COLUMN
            0    4331309            22653005  CONCEPT_SOURCE_CODE
            1    4331309            C0729608             UMLS_CUI
            2   37018594            22653005            UMLS_CODE

    Args:
        data: A Pandas DataFrame containing several columns of clinical codes (see INPUT for an example).
        primary_key: A string containing a column to be used as a primary key.
        subset_columns: A list of columns to subset Pandas DataFrame on.

    Returns:
        subset_data_frames: A Pandas DataFrame containing stacked subsets of the original DataFrame.
    """

    # subset data
    subset_data_frames = []

    for col in subset_columns:
        subset = data[[primary_key, col]]
        subset['CODE_COLUMN'] = [col] * len(subset)
        subset.columns = [primary_key, 'CODE', 'CODE_COLUMN']
        subset_data_frames.append(subset)

    # convert list to single concatenated Pandas DataFrame
    subset_data = pd.concat(subset_data_frames)

    return subset_data.drop_duplicates()


def data_frame_supersetter(data: pd.DataFrame, index: str, columns: Tuple, values: Tuple) -> pd.DataFrame:
    """Takes a stacked Pandas DataFrame and unstacks it according to row values specified in the index column.
    This is equivalent to converting a DataFrame in long format to wide format. An example of the input and
    generated output is shown below.

        INPUT:
              CONCEPT_ID                CODE          CODE_COLUMN       ONTOLOGY_ID     ONTOLOGY        EVIDENCE
            0    4331309            22653005  CONCEPT_SOURCE_CODE
            1    4331309            C0729608             UMLS_CUI
            2   37018594            22653005            UMLS_CODE

        OUTPUT:
                 CONCEPT_ID CONCEPT_SOURCE_CODE  UMLS_CUI   UMLS_CODE
            0    4331309            22653005  C0729608    22653005
            1    4331310            22653011  C4075981    22653005

    Args:
        data: A Pandas DataFrame containing several columns of clinical codes (see INPUT for an example).
        index: A string containing a column to be used as a primary key.
        columns: A list of columns to unstack from row values into columns.
        values: A list of columns whose values will be used to populate the unstacked DataFrame.

    Returns:
        superset_data_frame: An unstacked version of the input DataFrame (see OUTPUT above for an example).
    """

    # unstack the DataFrame
    superset_data_frame = data.drop_duplicates().pivot(index=index, columns=columns, values=values)

    # reset index
    superset_data_frame.reset_index(level=0, inplace=True)
    superset_data_frame.columns.name = None

    return superset_data_frame.drop_duplicates()


def merge_dictionaries(dictionaries: Dict, key_type: str) -> Dict:
    """Given any number of dictionaries, shallow copy and merge into a new dict, precedence goes to key value pairs
    in latter dictionaries.

    Function from StackOverFlow Post:
        https://stackoverflow.com/questions/38987/how-do-i-merge-two-dictionaries-in-a-single-expression-in-python

    Args:
        dictionaries: A nested dictionary.
        key_type: A string containing the key of one of the inner dictionaries.

    Returns:
        combined_dictionary: A dictionary object containing.
    """

    combined_dictionary: Dict = {}

    for dictionary in dictionaries.keys():
        combined_dictionary.update(dictionaries[dictionary][key_type])

    return combined_dictionary
