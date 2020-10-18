#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Analytic Utility Functions.

Data Manipulation
* reconfigures_dataframe

"""

# import needed libraries
import pandas as pd  # type: ignore

from tqdm import tqdm
from typing import List


def reconfigures_dataframe(split_list: List, data_frame: pd.DataFrame) -> pd.DataFrame:
    """Takes a Pandas DataFrame and a list of strings representing important categories and reconfigures the DataFrame
    such that all it's stacked by category-specific data and a new column is added to represent which rows belong to
    each category. An example of the expected input and output data are shown below.

    INPUT DATA:
       CONCEPT_ID              CONCEPT_LABEL      HP_URI      MONDO_URI
            22288  Hereditary elliptocytosis  HP_0004445  MONDO_0008165

    OUTPUT DATA:
           CONCEPT_ID          CONCEPT_LABEL      CATEGORY  CATEGORY_URI
            22288  Hereditary elliptocytosis           HP     HP_0004445
            22288  Hereditary elliptocytosis        MONDO  MONDO_0008165

    Args:
        split_list: A list of string, where each string represents an ontology (e.g. ['HP, 'MONDO']).
        data_frame: A pandas data frame containing data. It is assumed that there will be columns in the data frame
            that correspond to at least one of the categories in split_list.

    Returns:
        reconfigured_data: A Pandas DataFrame that has been reconfigured such that the data are stacked by
            category-specific data and a new column is added to represent which rows belong to each category.
    """

    # get non-ontology columns
    non_category_columns = [x for x in data_frame.columns if not any(i for i in split_list if i.lower() in x.lower())]

    # identify which columns belong to each of the input ontologies
    category_split_data = []
    for x in split_list:
        # get category-specific columns
        cat_columns = [i for i in data_frame.columns if x.lower() in i.lower()]
        # subset original data to include non-category and specific single category data
        cat_data = data_frame[non_category_columns + cat_columns]
        # drop rows where all category columns are NaN
        cat_data = cat_data.dropna(subset=cat_columns)
        # rename data
        cat_data.columns = non_category_columns + [col.upper().replace(x.upper(), 'CATEGORY') for col in cat_columns]
        # add category specific column
        cat_data['CATEGORY'] = [x] * len(cat_data)
        category_split_data.append(cat_data)

    # concatenate stacked data into single DataFrame
    reconfigured_data = pd.concat(category_split_data)

    return reconfigured_data


# def splits_data_frame(onts: List, data_frame: pd.DataFrame) -> List:
#     """
#
#     Args:
#         onts: A list of string, where each string represents an ontology (e.g. ['HP, 'MONDO']).
#         data_frame: A pandas data frame containing data. It is assumed that there will be columns in the data frame
#             that correspond to at least one of the ontologies in onts.
#
#     Returns:
#         XX: A list of Pandas
#     """
#
#     # re-configure data
#     hp_dbxref = data_frame.groupby('Arb_Person_ID')
#
#     return