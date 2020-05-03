#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
import logging
import os

from google.api_core import page_iterator
from google.cloud import storage

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


def download_data(files: page_iterator.HTTPIterator, folder: str) -> None:
    """Method takes a page_iterator containing files located within a Google Cloud Storage bucket and downloads them
    to the file location specified by the folder variable.

    Args:
        files: An iterator containing file names to download from a GCS bucket.
        folder: A string containing a local file path where the data will be downloaded to.

    Returns:
        None.
    """
    logging.info('File download Started... Wait for the job to complete.')

    # create folder locally if not exists
    if not os.path.exists(folder): os.makedirs(folder)

    for file in files:
        logging.info('GCS File: {}'.format(file.name))
        destination_uri = '{}/{}'.format(folder, file.name.split('/')[-1])
        file.download_to_filename(destination_uri if destination_uri.endswith('.csv') else destination_uri + '.csv')
        logging.info('Exported {} to {}'.format(file.name, destination_uri))

    return None


@click.command()
@click.option('--bucket_name', prompt='The name of the GCS bucket')
@click.option('--file_name', prompt='The name of the GCS bucket directory to download data from')
@click.option('--auth_json', prompt='The filepath to service_account.json file')
def main(bucket_name: str, file_name: str, auth_json: str) -> None:

    # connect to GCS bucket
    storage_client = storage.Client.from_service_account_json(auth_json)
    bucket = storage_client.get_bucket(bucket_name)
    files = bucket.list_blobs(prefix=file_name)  # hardcoded assumption for delimiter

    # download data files
    download_data(files, 'resources/clinical_data')


if __name__ == '__main__':
    main()
