#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
import logging
import os

from google.api_core import page_iterator
from google.cloud import storage

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


def download_data(folder: str, files: page_iterator.HTTPIterator) -> None:
    logging.info('File download Started... Wait for the job to complete.')

    # Create this folder locally if not exists
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Iterating through for loop one by one using API call
    for file in files:
        logging.info('Blobs: {}'.format(file.name))
        destination_uri = '{}/{}'.format(folder, file.name.split('/')[-1])
        file.download_to_filename(destination_uri)
        logging.info('Exported {} to {}'.format(file.name, destination_uri))

    return None


@click.command()
@click.option('--bucket_name', prompt='The name of the GCS bucket')
@click.option('--file_name', prompt='The name of the GCS directory to download files from')
@click.option('--auth_json', prompt='The filepath to service_account.json file')
@click.option('--folder', prompt='Local directory to save files to')
@click.option('--delimiter', prompt='file path delimiter', default='/')
def main(bucket_name: str, file_name: str, auth_json: str, folder: str, delimiter: str) -> None:

    # connect to GCS
    storage_client = storage.Client.from_service_account_json(auth_json)
    bucket = storage_client.get_bucket(bucket_name)
    files = bucket.list_blobs(prefix=file_name, delimiter=delimiter)

    # download data files
    download_data(folder, files)


if __name__ == '__main__':
    main()
