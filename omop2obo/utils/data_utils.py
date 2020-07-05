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
