#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data PreProcessing Utility Functions.

Pandas DataFrame Manipulations
* data_frame_subsetter
* data_frame_supersetter
* column_splitter
* data_frame_grouper
* normalizes_source_codes
* aggregates_column_values
* dataframe_difference
* recursively_update_dataframe
* merges_dataframes
* finds_umls_descendants

Dictionary Manipulations
* merge_dictionaries

Mapping Result Processing
* ohdsi_ananke
* normalizes_clinical_source_codes
* filters_mapping_content
* compiles_mapping_content
* formats_mapping_evidence
* assigns_mapping_category
* aggregates_mapping_results
* finds_ancestor_mappings

Reading and Writing Data Objects
* pickle_large_data_structure
* read_pickled_large_data_structure

"""

# import needed libraries
import itertools
import os
import pandas as pd  # type: ignore
import pickle
import sys

from functools import reduce
from more_itertools import unique_everseen
from tqdm import tqdm  # type: ignore
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union  # type: ignore

# ENVIRONMENT WARNINGS
# WARNING 1 - Pandas: disable chained assignment warning rationale:
# https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas
pd.options.mode.chained_assignment = None

# reset recursion limit to be a bit less conservative in order to handle terminologies with deep hierarchies
sys.setrecursionlimit(1500)


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
        subset.loc[:, 'CODE_COLUMN'] = [col] * len(subset)
        subset.columns = [primary_key, 'CODE', 'CODE_COLUMN']
        subset_data_frames.append(subset)

    # convert list to single concatenated Pandas DataFrame
    subset_data = pd.concat(subset_data_frames)

    return subset_data.drop_duplicates()


def data_frame_supersetter(data: pd.DataFrame, index: str, columns: str, values: str) -> pd.DataFrame:
    """Takes a stacked Pandas DataFrame and unstacks it according to row values specified in the index column.
    This is equivalent to converting a DataFrame in long format to wide format. An example of the input and
    generated output is shown below.

        INPUT:
              CONCEPT_ID                CODE          CODE_COLUMN
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


def column_splitter(data: pd.DataFrame, key: str, delimited_columns: List, delimiter: str) -> pd.DataFrame:
    """Takes a Pandas DataFrame and a list of strings specifying columns in the DataFrame that may contain a delimiter
    and expands the delimited strings within each column into separate rows. The expanded data are then merged with the
    original data.

    Args:
        data: A stacked Pandas DataFrame containing output from the umls_cui_annotator method.
        key: A string containing the column of a Pandas DataFrame to use as the primary key.
        delimited_columns: A list of the column names which contain delimited data.
        delimiter: A string specifying the delimiter type.

    Returns:
        merged_split_data: A Pandas DataFrame containing the expanded data.
    """

    delimited_data = []

    for col in delimited_columns:
        subset_data = data[[key, col]]

        # expand delimited column
        split_data = subset_data[col].str.split(delimiter).apply(pd.Series, 1).stack()
        split_data.index = split_data.index.droplevel(-1)
        split_data.name = col

        # drop original delimited column and merge expanded data
        subset_data.drop(columns=[col], inplace=True)
        merged_split_data = subset_data.join(split_data)

        # clean up leading and trailing white space
        merged_split_data[col] = merged_split_data[col].apply(lambda x: x.strip())
        delimited_data.append(merged_split_data.drop_duplicates())

    # merge delimited data
    merged_delimited_data = reduce(lambda x, y: pd.merge(x, y, on=key), delimited_data)

    return merged_delimited_data.drop_duplicates()


def aggregates_column_values(data: pd.DataFrame, primary_key: str, agg_cols: List, delimiter: str) -> pd.DataFrame:
    """Takes a Pandas DataFrame, a string containing a primary key, a list of columns to aggregate, and a string
    delimiter to use when aggregating the columns. The method then loops over each column in agg_cols and performs
    the aggregation. The method joins all aggregated columns and merges it into a single Pandas DataFrame.

    Args:
        data: A Pandas DataFrame.
        primary_key: A string containing a column name to be used as a primary key.
        agg_cols: A list of columns to aggregate.
        delimiter: A string containing a delimiter to aggregate results by.

    Returns:
        merged_combo: A Pandas DataFrame that includes the primary_key column and one
            delimiter-aggregated column for each column in the agg_cols list.
    """

    # create list of aggregated GroupBy DataFrames
    grouped_data = data.groupby([primary_key])
    combo = [grouped_data[col].apply(lambda x: delimiter.join(list(unique_everseen(x)))) for col in agg_cols]

    # merge data frames by primary key and reset index
    merged_combo = reduce(lambda x, y: pd.merge(x, y, on=primary_key, how='outer'), combo)
    merged_combo = merged_combo.reset_index(level=0, inplace=False)

    return merged_combo


def data_frame_grouper(data: pd.DataFrame, primary_key: str, type_column: str, col_agg: Callable) -> \
        pd.DataFrame:
    """Methods takes a Pandas DataFrame as input, a primary key, and a column to group the data by and
    creates a new DataFrame that merges the individual grouped DataFrames into a single DataFrame.
    Examples of the input and output data are shown below.

    INPUT_DATA:
                   CONCEPT_ID        CONCEPT_DBXREF_ONT_URI  CONCEPT_DBXREF_ONT_TYPE          CONCEPT_DBXREF_EVIDENCE
            0         442264        http://...MONDO_0100010                     MONDO   CONCEPT_DBXREF_sctid:68172002
            2        4029098        http://...MONDO_0045014                     MONDO   CONCEPT_DBXREF_sctid:237913008
            4        4141365        http://...HP_0000964                        HP      CONCEPT_DBXREF_sctid:426768001

    OUTPUT DATA:
    Columns: ['CONCEPT_ID', 'HP_CONCEPT_DBXREF_ONT_URI', 'HP_CONCEPT_DBXREF_ONT_LABEL', 'HP_CONCEPT_DBXREF_EVIDENCE',
              'MONDO_CONCEPT_DBXREF_ONT_URI', 'MONDO_CONCEPT_DBXREF_ONT_LABEL', 'MONDO_CONCEPT_DBXREF_EVIDENCE']

    Args:
        data: A Pandas DataFrame containing data with columns that can be grouped (see INPUT above for ex).
        primary_key: A string containing the name of the column in the input DataFrame to use as a
            primary key.
        type_column: A string containing the name of the column in the input DataFrame to use for
            grouping the data (see OUTPUT above for an example).
        col_agg: A func that aggregates data within a Pandas DataFrame column.

    Returns:
        grouped_data_full: A Pandas DataFrame containing a merged version of the grouped data.
    """

    # group data by ontology type
    grouped_data = data.groupby(type_column)
    grouped_data_frames = []

    for grp in grouped_data.groups:
        temp_df = grouped_data.get_group(grp)
        temp_df.drop(type_column, axis=1, inplace=True)
        # rename columns
        updated_names = [x.replace('ONT', grp) for x in list(temp_df.columns) if x != primary_key]
        temp_df.columns = [primary_key] + updated_names
        # aggregate data
        agg_cols = [col for col in temp_df.columns if col.split('_')[-1] in ['LABEL', 'EVIDENCE', 'URI']]
        temp_df_agg = col_agg(temp_df.copy(), primary_key, agg_cols, ' | ')

        grouped_data_frames.append(temp_df_agg.drop_duplicates())

    # merge DataFrames back together
    grouped_data_full = reduce(lambda x, y: pd.merge(x, y, how='outer', on=primary_key), grouped_data_frames)

    return grouped_data_full.drop_duplicates()


# def normalizes_source_codes(data: pd.DataFrame, source_code_dict: Dict) -> pd.Series:
#     """Takes a Pandas DataFrame column containing source code values that need normalization and normalizes them
#     using values from a pre-built dictionary (resources/mappings/source_code_vocab_map.csv). The function is designed
#     to normalize identifier prefixes according to the specifications in the source_code_dict. It provides some light
#     regex support for the following scenarios:
#         - ICD10CM:C85.92 --> icd10:c85.92
#         - http://www.snomedbrowser.com/codes/details/12132356564 --> snomed_12132356564
#         - http://www.orpha.net/ordo/orphanet_1920 --> orphanet_1920
#
#     Assumption: assumes that the column to normalize is always the 0th index.
#
#     Args:
#         data: A column from a Pandas DataFrame containing unstacked identifiers that need normalization (e.g.
#             umls:c123456, http://www.snomedbrowser.com/codes/details/12132356564, rxnorm:12345).
#         source_code_dict: A dictionary keyed by input prefix with values reflecting the preferred prefixes in the
#             source_code_dict file. For example:
#                 {'snomed': 'snomed', 'snomed_ct': 'snomed', 'snomed_ct_us_2018_03_01': 'snomed'}
#
#     Returns:
#         A Pandas Series that has been normalized.
#     """
#
#     # split prefix from number in each identifier
#     prefix = data[data.columns[0]].apply(
#         lambda j: j.rstrip([x for x in re.split('[_:|/]', j) if x != ''][-1])[:-1] if 'http' in j and '_' in j else
#         j.rstrip([x for x in re.split('[:|/]', j) if x != ''][-1])[:-1]
#     )
#
#     id_num = data[data.columns[0]].apply(
#         lambda j: [x for x in re.split('[_:|/]', j) if x != ''][-1] if 'http' in j and '_' in j else
#         [x for x in re.split('[:|/]', j) if x != ''][-1]
#     ).str.lower()
#
#     # normalize prefix to dictionary and clean up urls
#     norm_prefix = prefix.apply(lambda j: source_code_dict[j] if j in source_code_dict.keys() else j)
#
#     # concat normalized identifier and number back together
#     updated_source_codes = norm_prefix + ':' + id_num
#
#     return updated_source_codes


def merge_dictionaries(dictionaries: Dict, key_type: str, reverse: bool = False) -> Dict:
    """Given any number of dictionaries, shallow copy and merge into a new dict, precedence goes to key value pairs
    in latter dictionaries.

    Function from StackOverFlow Post:
        https://stackoverflow.com/questions/38987/how-do-i-merge-two-dictionaries-in-a-single-expression-in-python

    Args:
        dictionaries: A nested dictionary.
        key_type: A string containing the key of one of the inner dictionaries.
        reverse: A bool indicating whether  the dictionaries should be reversed before merging (default=False).

    Returns:
        combined_dictionary: A dictionary object containing a merge set of items from each dictionary.
    """

    combined_dictionary: Dict = {}

    for dictionary in dictionaries.keys():
        if reverse: combined_dictionary.update({v: k for k, v in dictionaries[dictionary][key_type].items()})
        else: combined_dictionary.update(dictionaries[dictionary][key_type])

    return combined_dictionary


def ohdsi_ananke(primary_key: str, ont_keys: list, ont_data: pd.DataFrame, data1: pd.DataFrame, data2: pd.DataFrame) \
        -> pd.DataFrame:
    """Function applies logic from the OHDSIAnanake method to extend data1, which contains dbxref mappings to OMOP
    concept ids with mappings from UMLS cuis to relevant umls ontology mappings. The merged data set is returned.

    Method adapted from: https://github.com/thepanacealab/OHDSIananke

    Args:
        primary_key: A string containing the name of the primary key (i.e. CONCEPT_ID).
        ont_keys: A list of ontology type identifiers (i.e. ['hp', 'mondo']).
        ont_data: A Pandas DataFrame containing ontology dbxref information.
        data1: A stacked Pandas DataFrame containing source codes and umls cuis.
        data2: A Pandas DataFrame containing UMLS cuis and mappings to ontologies.

    Returns:
        dbxrefs: A Pandas DataFrame containing the data from data1 merged with new entries from the umls cui data (
            data2).
    """

    # convert ont_data into a format that can be merged

    col = [x for x in ont_data.columns if 'URI' in x][0]
    ont_data['CODE'] = ont_data[col].apply(lambda x: x.split('/')[-1].lower().replace('_', ':'))

    # filter umls cui data to only
    data2_filtered = data2[(data2['CODE'].apply(lambda x: x if x.split(':')[0] in ont_keys else 999) != 999)]

    # merge with filtered data with ontology data
    merged_data = data1.merge(data2_filtered, how='inner', left_on='CODE', right_on='CUI').drop_duplicates()

    # merge with ont labels
    merged_data_ont = merged_data.merge(ont_data, how='inner', left_on='CODE_y', right_on='CODE').drop_duplicates()

    # drop unneeded columns
    dbxref_col = [x for x in merged_data_ont.columns if 'DBXREF' in x][0]
    merged_data_ont = merged_data_ont[[primary_key, 'CUI', 'CODE_COLUMN', dbxref_col]]

    # update cuis column
    merged_data_ont['CUI'] = merged_data_ont['CUI'].apply(lambda x: 'umls:' + x)

    # rename columns
    merged_data_ont.columns = [primary_key, 'CODE', 'CODE_COLUMN', dbxref_col]

    return merged_data_ont


def normalizes_source_terminologies(dbxref_dict: Dict, source_df: pd.DataFrame, cols: List) -> pd.DataFrame:
    """Function takes a Pandas DataFrame, a source abbreviation alignment dictionary, and a list of columns containing
    strings of column names that need normalization. THe column normalizes columns of terminology concepts and returns
    them as new columns with '_TEMP' appended to the end.

    Args:
        dbxref_dict: A dictionary of ontology identifiers and their database cross-references.
        source_df: A Pandas DataFrame that contains code and source columns needing normalization.
        cols: A list of columns to normalize.

    An example of each input is shown below:
        dbxref_dict: {'snm', 'snomed': 'snomed', 'snomed_ct': 'snomed', 'snomed_ct_us_2018_03_01': 'snomed'}
        cols: [UMLS_SAB, 'OBO_DBXREF_SAB']
        source_df:
            UMLS_SAB               HPO
            OBO_DBXREF_SAB         icd-10

    Returns:
        normalized_df: A Pandas DataFrame containing normalizes terminology columns.

        An example output is shown below:
        source_df:
            UMLS_SAB               HPO
            UMLS_SAB_TEMP          hp
            OBO_DBXREF_SAB         icd-10
            OBO_DBXREF_SAB_TEMP    icd10
    """

    normalized_df = source_df.copy()
    valid_cols = set(cols).intersection(set(source_df.columns))

    for i in valid_cols:
        normalized_df[i + '_TEMP'] = normalized_df[i].apply(lambda x: dbxref_dict[x] if x in dbxref_dict.keys() else x)

    return normalized_df


def normalizes_source_codes(dbxref_dict: Dict, source_df: pd.DataFrame, cols: List) -> pd.DataFrame:
    """Function takes a Pandas DataFrame, a source abbreviation alignment dictionary, and a nested list of columns and
    uses them to construct and replace the original columns with normalized identifiers (storing the original column
    values with '_ORG' appended to the end).

    Args:
        dbxref_dict: A dictionary of ontology identifiers and their database cross-references.
        source_df: A Pandas DataFrame that contains code and source columns needing normalization.
        cols: A nested list, where each inner list contains two items representing column names in the source_df. The
            first item references the name of the column that contains codes and the second item references the name
            of the column that contains the code's source abbreviations.

        An example of each input is shown below:
        dbxref_dict: {'snm', 'snomed': 'snomed', 'snomed_ct': 'snomed', 'snomed_ct_us_2018_03_01': 'snomed'}
        cols: [['CODE', 'OBO_SAB'], ['DBXREF', 'OBO_DBXREF_SAB']]
        source_df:
            OBO_ontology_id                http://purl.obolibrary.org/obo/HP_0012161
            CODE                                                          HP:0012161
            OBO_SAB                http://purl.obolibrary.org/obo/hp/releases/202...
            DBXREF                                                          C4023016
            OBO_SAB                http://purl.obolibrary.org/obo/hp/releases/202...

    Returns:
        normalized_df: An updated Pandas DataFrame that contains normalized identifiers for the column referenced in the
            first position of each inner list. An example row of the output is shown below:

            OBO_ontology_id                http://purl.obolibrary.org/obo/HP_0012161
            CODE_ORG                                                      HP:0012161
            CODE                                                          hp:0012161
            OBO_SAB                http://purl.obolibrary.org/obo/hp/releases/202...
            DBXREF_ORG                                                      C4023016
            DBXREF                                                     umls:C4023016
            OBO_SAB                http://purl.obolibrary.org/obo/hp/releases/202...

    """

    normalized_df = source_df.copy()

    for col1, col2 in cols:
        normalized_df[col1 + '_ORG'] = normalized_df[col1]
        if list(normalized_df[col2])[0].startswith('http://purl.obolibrary.org/obo/'):
            normalized_df[col1] = normalized_df[col1].str.lower()
        else:
            normalized_df['temp'] = normalized_df[col2] + '*' + normalized_df[col1]
            normalized_df[col1] = normalized_df['temp'].apply(
                lambda x: dbxref_dict[x.split('*')[1].split(':')[0]] + ':' + x.split('*')[1].split(':')[1]
                if (len(x.split('*')[1].split(':')) == 2 and x.split('*')[1].split(':')[0] in dbxref_dict.keys())
                else dbxref_dict[x.split('*')[0]] + ':' + x.split('*')[1] if x.split('*')[0] in dbxref_dict.keys()
                else x.split('*')[0].lower() + ':' + x.split('*')[1] if x != 'None*None'
                else 'None')
            normalized_df = normalized_df.drop(['temp'], axis=1)

    return normalized_df


def normalizes_clinical_source_codes(dbxref_dict: Dict, source_dict: Dict):
    """Function takes two dictionaries and uses them to create a new dictionary. The first dictionary, contains ontology
    database cross-references and the second contains content to normalize the identifiers contained in the first
    dictionary.
    Args:
        dbxref_dict: A dictionary of ontology identifiers and their database cross-references.
        source_dict: A dictionary containing information for normalizing the prefixes of the database cross-references.
        An example of each dictionary is shown below:
        - dbxref_dict = {'DbXref', 'umls:c4022862': 'DbXref', 'umls:c0008733': 'DbXref'}
        - source_dict = {'snm', 'snomed': 'snomed', 'snomed_ct': 'snomed', 'snomed_ct_us_2018_03_01': 'snomed'}
    Returns:
        normalized_prefixes: A dictionary where the keys are database cross-references and the values are strings
            containing the database cross-reference type and prefix from the key, separated by a star. For example:
            {'umls:c4022862': 'DbXref*umls', 'umls:c0008733': 'DbXref*umls'}
    """

    normalized_prefixes = {}

    # split prefix from number in each identifier
    for key, value in dbxref_dict.items():
        prefix, id_num = key.split(':')[0], key.split(':')[-1].lower()
        norm_prefix = source_dict[prefix] if prefix in source_dict.keys() else prefix
        normalized_prefixes[norm_prefix + ':' + id_num] = value + '*' + prefix

    return normalized_prefixes


def filters_mapping_content(exact_results: List, similarity_results: List, threshold: float) -> Tuple:
    """Parses compiled mapping results, when results exist, to determine a final aggregated mapping result.

    Args:
        exact_results: A nested list containing 3 sub-lists where sub-list[0] contains exact match uris, sub-list[1]
            contains exact match labels, and sub-list[2] contains exact match evidence.
        similarity_results: A nested list containing 3 sub-lists where sub-list[0] contains similarity uris,
            sub-list[1] contains similarity labels, and sub-list[2] contains similarity evidence.
        threshold: A float that specifies a cut-off for filtering cosine similarity results.

    Returns:
        A tuple of lists containing mapping results for a given row. The first tuple contains exact mapping results
            and the second contains similarity results. Both lists contain 3 items: uris, labels, and evidence.
    """

    exact_uri, exact_label, exact_evid = exact_results
    sim_uri, sim_label, sim_evid = similarity_results
    exact_result: Optional[List[Any]] = [None, None, None]
    sim_result: Optional[List[Any]] = [None, None, None]

    # format results
    if exact_uri:
        exact_result = [list(unique_everseen(exact_uri)),
                        list(unique_everseen(exact_label)),
                        ' | '.join(exact_evid)]
    if sim_uri:
        if any(x for x in sim_evid[0].split(' | ') if float(x.split('_')[-1]) == 1.0):
            evid_list = sim_evid[0].split(' | ')
            sim_keep = [evid_list.index(x) for x in evid_list if float(x.split('_')[-1]) == 1.0]
            uris, labels = [sim_uri[x] for x in sim_keep], [sim_label[x] for x in sim_keep]
            sim_result = [uris, labels, ' | '.join([evid_list[x] for x in sim_keep])]
        elif any(x for x in sim_evid[0].split(' | ') if float(x.split('_')[-1]) >= threshold):
            evid_list = sim_evid[0].split(' | ')
            sim_keep = [evid_list.index(x) for x in evid_list if float(x.split('_')[-1]) >= threshold]
            uris, labels = [sim_uri[x] for x in sim_keep], [sim_label[x] for x in sim_keep]
            sim_result = [uris, labels, ' | '.join([evid_list[x] for x in sim_keep])]
        else:
            sim_result = [sim_uri, sim_label, ' | '.join(sim_evid)]

    return exact_result, sim_result


def compiles_mapping_content(row: pd.Series, ont: str, threshold: float) -> Tuple:
    """Function takes a row of data from a Pandas DataFrame and processes it to return a single ontology mapping for
    the clinical concept represented by the row.

    Args:
        row: A row from a Pandas DataFrame cont
        ont: A string containing the name of an ontology (e.g. "HP", "MONDO").
        threshold: A float that specifies a cut-off for filtering cosine similarity results.

    Returns:
        A list containing mapping results for a given row. The list contains three items: uris, labels, evidence.
    """

    relevant_cols = [x for x in row.keys() if any(y for y in ['_DBXREF_' + ont, '_STR_' + ont, ont + '_SIM'] if y in x)]

    for level in ['CONCEPT', 'ANCESTOR']:
        exact_uri, exact_label, exact_evid, sim_uri, sim_label, sim_evid = ([] for _ in range(6))  # type: ignore
        for col in relevant_cols:
            if level in col and any(y for y in ['DBXREF', 'STR'] if y in col):
                if 'URI' in col and row[col] != '': exact_uri += [x.split('/')[-1] for x in row[col].split(' | ')]
                if 'LABEL' in col and row[col] != '': exact_label += [x for x in row[col].split(' | ')]
                if 'EVIDENCE' in col and row[col] != '': exact_evid += [row[col]]
            if 'SIM' in col:
                if 'URI' in col and row[col] != '': sim_uri += [x.split('/')[-1] for x in row[col].split(' | ')]
                if 'LABEL' in col and row[col] != '': sim_label += [x for x in row[col].split(' | ')]
                if 'EVIDENCE' in col and row[col] != '': sim_evid += [row[col]]
        if exact_uri: break

    # put together mapping
    if not exact_uri and not sim_uri:
        return [None] * 3, [None] * 3  # type: ignore
    else:
        return filters_mapping_content([exact_uri, exact_label, exact_evid], [sim_uri, sim_label, sim_evid], threshold)


def formats_mapping_evidence(ont_dict: dict, source_dict: Dict, result: Tuple, clin_data: Dict) -> Tuple:
    """Takes a nested dictionary of ontology attributes, a dictionary of source code prefix mapping information, a
    nested list containing aggregated mapping information, and a dictionary of clinical concept labels and synonyms.
    The function uses this information to aggregate the evidence supporting the mapping provided in the result object.

    Args:
        ont_dict: A nested dictionary containing ontology attributes.
        source_dict: A dictionary containing ontology prefixing information.
        result: A list containing mapping results for a given row. The list contains three items: uris, labels,
            evidence.
        clin_data: A dictionary keyed by column identifier with values containing data from the keyed column.

    Returns:
        A tuple. Where the first item contains evidence for exact matches and the second contains evidence for cosine
            similarity results. For example:
            ('OBO_LABEL-OMOP_CONCEPT_LABEL:abetalipoproteinemia', 'CONCEPT_SIMILARITY:HP_0008181_1.0')
    """

    dbx_evid, lab_evid, syn_evid, sim_evid = ([] for _ in range(4))  # type: ignore
    ont_label, ont_syns, ont_syntp = ont_dict['label'], ont_dict['synonym'], ont_dict['synonym_type']
    dbxref_type = normalizes_clinical_source_codes(ont_dict['dbxref_type'], source_dict)

    # sort clinical data
    if None not in result[0]:
        for x in result[0][2].split(' | '):
            lvl = x.split('_')[0]
            clin = {k: v for k, v in clin_data.items() if lvl in k}

            if 'dbxref' in x.lower():
                if x.split('_')[-1] in dbxref_type.keys():
                    prefix = dbxref_type[x.split('_')[-1]]
                else:
                    prefix = 'DbXref*' + x.split('_')[-1].split(':')[0]
                updated_prefix = 'OBO_' + prefix.split('*')[0] + '-OMOP_' + lvl + '_CODE'
                dbx_evid.append(updated_prefix + ':' + prefix.split('*')[-1] + '_' + x.split(':')[-1].replace(':', '_'))
            if 'label' in x.lower():
                lab_evid, clin_lab = [], ' | '.join([clin[x] for x in clin.keys() if 'label' in x.lower()])
                for lab in set(clin_lab.split(' | ')):
                    if lab.lower() in ont_label.keys() and ont_label[lab.lower()].split('/')[-1] in result[0][0]:
                        lab_evid.append('OBO_LABEL-OMOP_' + x.split('_')[0] + '_LABEL:' + x.split(':')[-1])
                    if lab.lower() in ont_syns.keys() and ont_syns[lab.lower()].split('/')[-1] in result[0][0]:
                        lab_evid.append('OBO_' + ont_syntp[lab.lower()] + '-OMOP_' + lvl + '_LABEL:' + x.split(':')[-1])
            if 'synonym' in x.lower():
                syn_evid, clin_syn = [], ' | '.join([clin[x] for x in clin.keys() if 'synonym' in x.lower()])
                for syn in set(clin_syn.split(' | ')):
                    if syn.lower() in ont_label.keys() and ont_label[syn.lower()].split('/')[-1] in result[0][0]:
                        syn_evid.append('OBO_LABEL-OMOP_' + x.split('_')[0] + '_SYNONYM:' + x.split(':')[-1])
                    if clin_syn.lower() in ont_syns.keys() and ont_syns[syn.lower()].split('/')[-1] in result[0][0]:
                        syn_lab = '-OMOP_' + lvl + '_SYNONYM:'
                        syn_evid.append('OBO_' + ont_syntp[syn.lower()] + syn_lab + x.split(':')[-1])
    if None not in result[1]: sim_evid = ['CONCEPT_SIMILARITY:' + x for x in result[1][-1].split(' | ')]

    # compile evidence
    compiled_exact = ' | '.join(list(filter(None, list(unique_everseen(dbx_evid + lab_evid + syn_evid)))))
    compiled_sim = ' | '.join(list(filter(None, list(unique_everseen(sim_evid)))))

    return compiled_exact, compiled_sim


def assigns_mapping_category(mapping_result: List, map_evidence: str) -> str:
    """Function takes a mapping result and evidence and uses it to determine the mapping category.

    Args:
        mapping_result: A list containing mapping results for a given row. The list contains three items: uris, labels,
            evidence.
        map_evidence: A string containing the compiled mapping evidence.

    Returns:
         mapping_category: A string containing the mapping category.
    """

    if 'CONCEPT_SIMILARITY:' in map_evidence:
        if len(map_evidence.split(' | ')) > 1:
            mapping_category = 'Automatic Constructor - Concept'
        else:
            mapping_category = 'Manual Exact - Concept Similarity'
    elif any(x for x in ['ANCESTOR_CODE', 'ANCESTOR_SYNONYM', 'ANCESTOR_LABEL'] if x not in map_evidence):
        if len(mapping_result[0]) > 1:
            mapping_category = 'Automatic Constructor - Concept'
        else:
            mapping_category = 'Automatic Exact - Concept'
    elif any(x for x in ['ANCESTOR_CODE', 'ANCESTOR_SYNONYM', 'ANCESTOR_LABEL'] if x in map_evidence):
        if len(mapping_result[0]) > 1:
            mapping_category = 'Automatic Constructor - Ancestor'
        else:
            mapping_category = 'Automatic Exact - Ancestor'
    else:
        mapping_category = ''

    return mapping_category


def aggregates_mapping_results(data: pd.DataFrame, onts: List, ont_data: Dict, source_codes: Dict,
                               threshold: float = 0.25) -> pd.DataFrame:
    """Function takes a Pandas Dataframe containing the results from running the OMOP2OBO exact and similarity
    mapping functions. This function takes those results and aggregates them such that a single column set of
    evidence is returned for each ontology (i.e. uris, labels, mapping category, and mapping evidence).

    #TODO: this function could (should) be parallelized

    Args:
        data: A Pandas DataFrame of mapping results from running the OMOP2OBO exact mapping and concept similarity
            pipeline.
        onts: A list of strings representing ontologies (e.g. ["hp", "mondo"]).
        ont_data: A nested dictionary of ontology data including mappings between ontology class URIs, labels,
            synonyms, definitions, and dbxrefs.
        source_codes: A dictionary containing dbxref mappings between dbxref prefixes that is designed to normalize
            prefixes to a single type.
        threshold: A float that specifies a cut-off for filtering cosine similarity results (default = 0.25).

    Return:
        A Pandas DataFrame containing the original columns with 8 additional columns per ontology, where the first
            set of 4 columns contain the exact match results and the second set of 4 columns contains the concept
            similarity results.
    """

    print('\n#### AGGREGATING AND COMPILING MAPPING RESULTS ####')
    print('Note. Until parallelized this step can up to several hours to complete for large concept sets...\n')

    # set input variables
    cols = [x.lower() for x in data.columns]
    clin_cols = [x for x in cols if (x.endswith('label') or x.endswith('nym')) and not any(y for y in onts if y in x)]

    for ont in [x.upper() for x in onts]:
        print('Processing {} Mappings'.format(ont))
        exact_mappings: List[Any] = []
        sim_mappings: List[Any] = []
        for idx, row in tqdm(data.iterrows(), total=data.shape[0]):
            ont_list = ['DBXREF_' + ont, 'STR_' + ont, ont + '_SIM']
            res = [x for x in row.keys() if row[x] != '' and any(y for y in ont_list if y in x)]
            if len(res) != 0:
                map_info = compiles_mapping_content(row, ont, threshold)
                clin_data = {x.upper(): row[x.upper()] for x in clin_cols if x.upper() in row.keys()}
                ext_evid, sim_evid = formats_mapping_evidence(ont_data[ont.lower()], source_codes, map_info, clin_data)
                # get exact mapping information
                if ext_evid != '':
                    exact_mappings.append([' | '.join(map_info[0][0]), ' | '.join(map_info[0][1]),
                                           assigns_mapping_category(map_info[0], ext_evid), ext_evid])
                else: exact_mappings.append([None] * 4)
                # get similarity information
                if sim_evid != '':
                    sim_mappings.append([' | '.join(map_info[1][0]), ' | '.join(map_info[1][1]),
                                         assigns_mapping_category(map_info[1], sim_evid), sim_evid])
                else: sim_mappings.append([None] * 4)
            else:
                exact_mappings.append([None] * 4)
                sim_mappings.append([None] * 4)

        # add aggregated mapping results back to data frame
        data['AGGREGATED_' + ont + '_URI'] = [x[0] for x in exact_mappings]
        data['AGGREGATED_' + ont + '_LABEL'] = [x[1] for x in exact_mappings]
        data['AGGREGATED_' + ont + '_MAPPING'] = [x[2] for x in exact_mappings]
        data['AGGREGATED_' + ont + '_EVIDENCE'] = [x[3] for x in exact_mappings]
        data['SIMILARITY_' + ont + '_URI'] = [x[0] for x in sim_mappings]
        data['SIMILARITY_' + ont + '_LABEL'] = [x[1] for x in sim_mappings]
        data['SIMILARITY_' + ont + '_MAPPING'] = [x[2] for x in sim_mappings]
        data['SIMILARITY_' + ont + '_EVIDENCE'] = [x[3] for x in sim_mappings]

    # shortens long text fields in original output data (otherwise Excel expands columns into additional rows)
    size_limit = 32500  # current size limit for an Excel column
    for x in data.columns:
        data[x] = data[x].apply(lambda i: i[0:size_limit] if not isinstance(i, int) and i is not None else i)

    return data


def dataframe_difference(df1: pd.DataFrame, df2: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Function finds rows which are different between two DataFrames. If there is new data the rows that are unique
    (i.e., new rows) are returned, otherwise None is returned.

    Args:
        df1: A Pandas DataFrame.
        df2: A Pandas DataFrame.

    Returns:
        diff_df: A Pandas DataFrame that contains data that is unique
    """

    if not df1.equals(df2): diff_df = pd.concat([df1, df2]).drop_duplicates(keep=False)
    else: diff_df = None

    return diff_df


def adds_merge_metadata(meta: List, df_obj: Union[pd.Series, pd.DataFrame]) -> \
        Union[Tuple[Optional[str], pd.Series], pd.Series]:
    """Function generates row-level metadata to explain a mapping.

    Args:
        meta: A nested list containing information needed to create metadata for mappings.
        df_obj: A pd.DataFrame or a pd.Series.

    Returns:
        A tuple where the first item is either a string or None type object and the second item is a pd.Series.
    """
    match_type, df1, df2 = meta; df1_name, df1_col_type = df1; df2_name, df2_col_type = df2
    match_str = '{} ({}) mapped to {} ({}) on "{}"' if df1_col_type is not None else '{} ({}) mapped to {} ({}) on {}'

    if isinstance(df_obj, pd.Series):
        hit = df_obj[match_type]
        if df1_col_type is not None:
            match = match_str.format(df1_name, df_obj[df1_col_type], df2_name, df_obj[df2_col_type], hit)
        else:
            match = match_str.format(df1_name, match_type, df2_name, match_type, hit)
        return match.replace(' (None)', ''), df_obj
    else:
        df_obj['MATCH_TYPE'] = df_obj.apply(
            lambda x: [match_str.format(df1_name, match_type, df2_name, match_type,
                                        x[match_type]).replace(' (None)', '')
                       if x[match_type] is not None else None][0]
            if df1_col_type is None
            else [match_str.format(df1_name, x[df1_col_type], df2_name, x[df2_col_type], x[match_type]
                  if x[match_type] is not None else None)][0].replace(' (None)', ''),
            axis=1)

        return df_obj['MATCH_TYPE']


def recursively_updates_dataframe(meta: List, df1: pd.DataFrame, cols: List, df2: pd.DataFrame = None) -> pd.DataFrame:
    """Function searches all column values provided in the cols list in an input Pandas DataFrame object and ensures
    that all possible matches for these variables, when merged against itself, are identified.

    Explained another way, for each row in df1, two types of values are returned:
        (i) test1: get all col2 identifier rows in df1 and return col1 identifiers from these rows. Then, return all
        rows from df2[col1] containing these identifiers.
        (i) test2: get all col1 identifier rows in df1 and return col2 identifiers from these rows. Then, return all
        rows from df2[col2] containing these identifiers.

    Args:
        meta: A nested list containing information needed to create metadata for mappings.
        df1: A Pandas DataFrame object.
        cols: A list of columns to recurse over.
        df2: A Pandas DataFrame object.

    Returns:
        df: A Pandas DataFrame that contains all possible objects in the col list for the input df1 object.
    """

    df_core, df2 = df1.copy(), df2 if df2 is not None else df1; master_ids = set()
    df_list: List = []; d1, d2 = meta[1][0], meta[2][0]

    for idx, row in tqdm(df1.iterrows(), total=df1.shape[0]):
        df1_keys = [x for x in df1.columns if x not in set(df2.columns) and 'MATCH' not in x]
        match, row = adds_merge_metadata(meta, row); df_core.at[idx, 'MATCH_TYPE'] = match
        for col1, col2 in itertools.combinations(cols, 2):
            for c1, c2 in [[col1, col2], [col2, col1]]:
                if (row[c1] != 'None' and row[c2] != 'None') and row[c1] + '-' + row[c2] not in master_ids:
                    master_ids |= {row[c1] + '-' + row[c2]}; d1c2 = row[c2]
                    d1c1_ids = df1[df1[c2] == d1c2][c1]; d1c1 = '|'.join(c1 + ':' + x for x in set(d1c1_ids))
                    df_t = dataframe_difference(df_core, df2[df2[c1].isin(d1c1_ids)])
                    df_t = df_t[pd.isna(df_t['MATCH_TYPE'])]
                    if df_t is not None and len(df_t) > 0:
                        for c in df1_keys: df_t[c] = df_t[c].apply(lambda x: row[c] if x == 'None' or pd.isna(x) else x)
                        df_t['MATCH'] = row['MATCH'] + ' - ' + 'Recursive Row Search Enhancement'
                        mt_str1 = row['MATCH'] + ':' + match
                        mt_str2 = '\n\nRecursive Row Search Enhancement: {}+{} Merge ({}:{}) Rows - {} ({}) Rows'
                        df_t['MATCH_TYPE'] = mt_str1 + mt_str2.format(d1, d2, c2, d1c2, d2, d1c1); df_list += [df_t]
    if len(df_list) > 0: df_core = pd.concat([df_core] + df_list).drop_duplicates()

    return df_core


def merges_dataframes(merge_type: str, df1: pd.DataFrame, df1_col: List, df2: pd.DataFrame, df2_col: List,
                      metadata_cols: List, recurse: bool = True) -> Optional[pd.DataFrame]:
    """Function takes two Pandas DataFrames and comprehensively integrates them, which is a process that includes the
    subsetting of columns in df1, the merging of df1 and df2, and the recursively updating of the merged data set
    using data from certain columns in df2.

    Args:
        merge_type: A string specifying the type of merge to perform (i.e., 'CODE', 'DBXREF', and 'STRING').
        df1: A Pandas DataFrame Object.
        df1_col: A list of columns to use when subsetting df1.
        df2: A Pandas DataFrame Object.
        df2_col: A list of columns to use from df2 when recursively integrating df1 and df2.
        metadata_cols: A nested list containing information needed to create metadata for mappings.
        recurse: A boolean value used to specify if the data should only be merged or be merged and recursed.

    Returns:
        merged_df: A comprehensively merged Pandas DataFrame Object.
    """

    print('Verifying Input Data')
    df1 = df1[df1_col].drop_duplicates(); mt = metadata_cols[0]
    merge_cols = list(set(df1.columns).intersection(set(df2.columns)))
    df1 = df1[df1[merge_type.replace('EXACT ', '')] != 'None'].drop_duplicates()
    if set(df1[merge_cols]) == {'None'} or len(df1) == 0: return None
    else:
        print('Merging Input Datasets')
        if mt == 'DBXREF': merged_df = df1.merge(df2, on=merge_cols, how='left').fillna('None').drop_duplicates()
        else: merged_df = df1.merge(df2, on=merge_cols, how='inner').fillna('None').drop_duplicates()
        if len(merged_df) == 0: return merged_df
        else:
            merged_df['MATCH_TYPE'] = adds_merge_metadata(metadata_cols, merged_df); merged_df['MATCH'] = merge_type
            merged_df['MATCH_TYPE'] = merged_df.apply(
                lambda x: 'OBO Provided {}'.format(x[metadata_cols[1][1]])
                if x[df2_col[0]] == 'None' else x['MATCH_TYPE'], axis=1)
            if recurse:
                print('Recursively Processing Merged Input Datasets')
                merged_update = recursively_updates_dataframe(metadata_cols, merged_df.copy(), df2_col, df2.copy())
            else: merged_update = merged_df.copy()
            merged_update = merged_update.fillna('None').drop_duplicates()
            # merged_update = merged_update.drop([i for i in merged_update
            # if set(merged_update[i]) == {'None'}], axis=0)

            return merged_update


# def finds_umls_descendants(df: pd.DataFrame, paths: Set, desc_set: Set, kids: Optional[Set] = None) -> Set:
#     """Function recursively searches for all descendant concepts of an input node regardless of context.
#
#     Args:
#         df: A Pandas DataFrame containing data from the UMLS MRHIER table.
#         paths: A list of strings, where each string represents a period-delimited list of ancestors.
#         desc_set: A set of all AUIs that are known to have at least one descendant concept.
#         kids: A list of strings, where each string represents a period-delimited list of descendants.
#
#     Returns:
#         kids: A list of strings, where each string represents a period-delimited list of descendants.
#     """
#
#     kids = set() if kids is None else kids
#
#     if len(paths) == 0: return kids
#     else:
#         results = df[df['PTR'] == paths.pop()]
#         # results = df[(df['PTR'] == path) & (df['AUI'].isin(desc_set))]
#         if len(results) > 0:
#             for idx, row in results.iterrows():
#                 # if row['AUI'] in desc_set:
#                 desc_seed_path = row['PTR'] + '.' + row['AUI']
#                 kids |= {desc_seed_path}
#                 if row['AUI'] in desc_set: paths |= {desc_seed_path}
#         return finds_umls_descendants(df, paths, desc_set, kids)

def finds_umls_descendants(df: pd.DataFrame, paths: List, desc_set: Set, kids: Optional[List] = None) -> List:
    """Function recursively searches for all descendant concepts of an input node regardless of context.

    Args:
        df: A Pandas DataFrame containing data from the UMLS MRHIER table.
        paths: A nested list of strings, where each string is an AUI.
        desc_set: A set of all AUIs that are known to have at least one descendant concept.
        kids: An ordered nested list, where each list contains AUIs.

    Returns:
        kids: An ordered nested list, where each list contains AUIs.
    """

    kids = list() if kids is None else kids

    if len(paths) == 1 and len(paths[0]) == 0: return kids
    else:
        res = set(df[df['PAUI'].isin(paths.pop())]['AUI'])
        paths += [[x for x in res if x in desc_set]]
        kids += [list(res)]
        return finds_umls_descendants(df, paths, desc_set, kids)


def processes_input_concept_mappings(filter_list: List, idx_list: Union[List, Set], df: pd.DataFrame,
                                     keys: List[str]) -> Tuple:
    """Function processes the results of mapping an input set of data to the UMLS or other relevant sources that are
    listed in the filter_list input and returns two Pandas DataFrames where the first DataFrame contains the concepts
    that were mapped to the UMLS or any relevant sources listed in the filter_list input.

    Args:
        filter_list: A list of strings representing normalized sources that a valid mapping would contain (e.g.,
            ['snomed', 'icd10', 'hp', 'icd10cm', 'icd9cm', 'icd9']).
        idx_list: A list of all input concepts that need mapping (e.g., ['HP:0033807']).
        df: A Pandas DataFrame that contains mapping results.
        keys: A list of strings, where each string refers to a column in a Pandas DataFrame. The first string is a
            primary key to be used for finding missing concepts (i.e., primary_key), the second string is a column to
            searched for matches in the provided Pandas DataFrames (i.e., search_column), and the remaining strings (
            i.e., df_col1-df_col4) contain relevant CODE and DBXref columns in the input sources that are merged for
            mappings (e.g., 'UMLS_SAB_TEMP', 'UMLS_DBXREF_SAB_TEMP', 'OBO_SAB_TEMP', 'OBO_DBXREF_SAB_TEMP']).

    Returns:
        A tuple of Pandas DataFrames where the first DataFrame contains concepts that had no mapping and the second
        contains all concepts with at least one mapping.
    """

    prim_key, sec_key, dfc1, dfc2, dfc3, dfc4 = keys
    no_match, matches, match_nodes, full_id_list = [], [], set(), set(df[prim_key])

    for i in tqdm(idx_list):
        if not i.startswith('http'):
            ids = 'http://purl.obolibrary.org/obo/' + i.replace(':', '_').upper() if 'obo' in prim_key.lower() else i
        else: ids = i
        primary_subset = df[(df[prim_key] == ids) & (df[sec_key] != 'None')]
        dbxref_subset = df[(df[prim_key] == ids) & (df['DBXREF'] != 'None')]
        code_subset = df[(df[prim_key] == ids) & (df['CODE'] != 'None')]
        df_list = [x for x in [primary_subset, dbxref_subset, code_subset] if len(x) > 0]
        for df_sub in df_list:
            for idx, row in df_sub.iterrows():
                k = row.keys()
                if row[sec_key] != 'None':
                    if dfc1 in k and row[dfc1] in filter_list: matches.append(idx); match_nodes |= {row[prim_key]}
                    elif dfc2 in k and row[dfc2] in filter_list: matches.append(idx); match_nodes |= {row[prim_key]}
                    elif dfc3 in k and row[dfc3] in filter_list: matches.append(idx); match_nodes |= {row[prim_key]}
                    elif dfc4 in k and row[dfc4] in filter_list: matches.append(idx); match_nodes |= {row[prim_key]}
                    if row['DBXREF'] not in ['None', i.lower()] or row['CODE'] != i.lower():
                        if dfc1 in k and row[dfc1] in filter_list: matches.append(idx); match_nodes |= {row[prim_key]}
                        elif dfc2 in k and row[dfc2] in filter_list: matches.append(idx); match_nodes |= {row[prim_key]}
                        elif dfc3 in k and row[dfc3] in filter_list: matches.append(idx); match_nodes |= {row[prim_key]}
                        elif dfc4 in k and row[dfc4] in filter_list: matches.append(idx); match_nodes |= {row[prim_key]}
                        else: continue
                elif row['DBXREF'] not in ['None', i.lower()] or row['CODE'] != i.lower():
                    if row[dfc3] in filter_list: matches.append(idx); match_nodes |= {row[prim_key]}
                    elif row[dfc4] in filter_list: matches.append(idx); match_nodes |= {row[prim_key]}
                    else: continue
                else: continue

    match_df = df[df.index.isin(matches)].drop_duplicates()
    no_match_df = df[df[prim_key].isin(list(full_id_list - match_nodes))].drop_duplicates()

    return no_match_df, match_df


def adds_relevant_missing_data(subset: pd.DataFrame, entity_df: pd.DataFrame, node: str, primary_key: str) -> \
        pd.DataFrame:
    """Function adds information from a primary entity DataFrame (e.g., the original Pandas DataFrame storing
    information on ontology concepts) to a matching result subset.

    Args:
        subset: A Pandas DataFrame containing a subset of mapping results.
        entity_df: A primary Pandas DataFrame, used to supplement the subset DataFrame.
        node: A string containing a node identifier.
        primary_key: A string containing a column name for the primary key needed to add data from the entity_df
            Pandas DataFrame to the subset Pandas DataFrame.

    Returns:
        subset_update: A Pandas DataFrame containing updated match information.
    """

    if primary_key not in subset.columns:
        # get original data on matched concept
        missing_data = entity_df[entity_df[primary_key].isin([node])]
        missing_data[primary_key] = node
        merge_cols = list(set(missing_data.columns).intersection(set(subset.columns)))
        subset_update = subset.merge(missing_data, on=merge_cols, how='left')
    else: subset_update = subset

    return subset_update


def finds_entity_mappings(search_type: str, concept_dict: Dict, keys: List, dfs: List, sab_list: List) -> Tuple:
    """Function takes a dictionary of concept ancestor or children information and three Pandas DataFrames,
    where the first DataFrame contains data on concepts that were unable to be mapped at the concept-level. The
    remaining DataFrames contain identifiers and associated information. Using these inputs, the function searches
    each concept in df0 in order to identify mappings to its ancestor or children concepts using df1 and df2.

    Args:
        search_type: A string containing the type of search (i.e., 'Ancestor' or 'Child').
        concept_dict: A dictionary of concepts and concept ancestors or children, where the concept keys are concept
            identifiers and the concept value is a dictionary keyed by node level (e.g., '0', '1') with values for each
            key containing an identifier.
        keys: A list of strings, where each string refers to a column in a Pandas DataFrame. The first string is a
            primary key to be used for finding missing concepts (i.e., primary_key), the second string is a column to
            searched for matches in the provided Pandas DataFrames (i.e., search_column), and the final string is a
            primary key to be used for finding matched concepts in one of the secondary Pandas DataFrames (i.e.,
            secondary_key).
        dfs: A Pandas DataFrame containing data for concepts without a mapping and the second two DataFrames contain
            identifiers and associated information to be used for mapping.
        sab_list: A list of source terminologies to further filter on results on.


    Returns:
        A tuple that contains a Pandas DataFrame where all rows with an ancestor or child match are removed and the
        second item is a dictionary where the keys are concept_ids and the values are DataFrames that contain the
        ancestor or children mappings.
    """

    sab_list = sab_list if isinstance(sab_list, List) else [sab_list]
    primary_key, search_column, secondary_key, col1_sab, col2_sab = keys
    df0, df1, df2, entity_df = dfs
    entity_dict = concept_dict; match_dict = dict()
    search_str = 'OBO {}: {} - {} level(s) above {} on {}' if 'Anc' in search_type \
                 else 'OBO {}: {} - {} level(s) below {} on {}'

    for i in tqdm(set(df0[primary_key])):
        entities = entity_dict[i]
        if entities is not None:
            entity_list = sorted(entities.keys()); match_hits = None; matched_df_list = []
            while len(entity_list) != 0 and match_hits is None:
                node_level = entity_list.pop(0); nodes = entities[node_level]; level = int(node_level) + 1
                relevant_rows = df1[(df1[primary_key].isin(nodes)) & (df1[search_column].isin(sab_list))]
                if len(relevant_rows) > 0:
                    if set(relevant_rows[search_column]) != {'umls'}:
                        node_ids = relevant_rows.groupby([primary_key]); node_list_dfs = []
                        for node in node_ids.groups.keys():
                            df = node_ids.get_group(node)
                            df_match_f = df[search_column].apply(lambda x: True if x != 'umls' else False)
                            match_hits = df[df_match_f].drop_duplicates(); match_hits['MATCH'] = 'DBXREF'
                            match_hits['MATCH_TYPE'] = match_hits.apply(
                                lambda x: search_str.format(search_type, node, level, i, x['DBXREF']), axis=1)
                            node_list_dfs.append(adds_relevant_missing_data(match_hits, entity_df, i, primary_key))
                        matched_df_list.append(pd.concat(node_list_dfs).drop_duplicates())
                    else:
                        relevant_row_ids = [x.split(':')[-1] for x in set(relevant_rows['DBXREF'])]
                        df_match1 = df2[(df2[secondary_key].isin(relevant_row_ids)) & (df2[col1_sab].isin(sab_list))]
                        df_match2 = df2[(df2[secondary_key].isin(relevant_row_ids)) & (df2[col2_sab].isin(sab_list))]
                        if len(df_match1) > 0:
                            node_ids = df_match1.groupby([secondary_key]); node_list_dfs = []
                            for node in node_ids.groups.keys():
                                match_hits = node_ids.get_group(node); match_hits['MATCH'] = 'DBXREF'
                                match_hits['MATCH_TYPE'] = match_hits.apply(
                                    lambda x: search_str.format(search_type, node, level, i, x['DBXREF']), axis=1)
                                node_list_dfs.append(adds_relevant_missing_data(match_hits, entity_df, i, primary_key))
                            matched_df_list.append(pd.concat(node_list_dfs).drop_duplicates())
                        elif len(df_match2) > 0:
                            node_ids = df_match2.groupby([secondary_key]); node_list_dfs = []
                            for node in node_ids.groups.keys():
                                match_hits = node_ids.get_group(node); match_hits['MATCH'] = 'DBXREF'
                                match_hits['MATCH_TYPE'] = match_hits.apply(
                                    lambda x: search_str.format(search_type, node, level, i, x['DBXREF']), axis=1)
                                node_list_dfs.append(adds_relevant_missing_data(match_hits, entity_df, i, primary_key))
                            matched_df_list.append(pd.concat(node_list_dfs).drop_duplicates())
                        else: continue
            if match_hits is not None: match_dict[i] = pd.concat(matched_df_list).fillna('None').drop_duplicates()

    # process and return updated output
    if len(match_dict) > 0: return df0[~df0[primary_key].isin(list(match_dict.keys()))], match_dict
    else: return df0, None


def finds_entity_fuzzy_matches(df_type: str, dfs: List, keys: List, sab_list: List, df_version: List) -> Optional[Dict]:
    """Function takes a list of Pandas DataFrames and a list of columns and uses that information to search for
    strings from the second DataFrame that containing specific substrings from the first DataFrame.

    Args:
        df_type: A string containing an identifier for df2.
        dfs: A list of Pandas DataFrames where the first DataFrame contains the mapping results and the second DataFrame
            contains a Pandas DataFrame of UMLS data.
        keys: A list of strings, where each string points to a specific column in the second DataFrame in the list.
        keys: A list of strings, where each string points to a specific column in the second DataFrame in the list.
        sab_list: A list of source terminologies to further filter on results on.
        df_version: A list, where the first item is the name of column to create and the second id a string containing
            the version the current df.

    Returns:
        substring_match_dict: A dictionary keyed by ontology_id where values are Pandas DataFrames containing the
            results of the fuzzy string matches.
    """

    main_key, primary_key, secondary_key, df2_col1, df2_col2 = keys
    df1, df2 = dfs; sab_list = [sab_list] if not isinstance(sab_list, List) else sab_list
    filtered_data = df1[df1[secondary_key] != 'None'].drop_duplicates()
    string_groups = filtered_data.groupby(['STRING']); string_match_dict = {}
    str_match = 'FUZZY STRING'
    str_match_type = '{} Strings Containing the Substring: "{}" on rows from MATCH: {} and MATCH_TYPE:{}'
    df_version_col, df_version = df_version

    for search_string in tqdm(string_groups.groups.keys()):
        str_df_subset = string_groups.get_group(search_string)
        matches = df2[df2['STRING'].str.contains(search_string, regex=False)]
        matches = matches[~matches['STRING'].isin([search_string])].reset_index()
        if len(matches) > 0:
            match1 = matches[matches[df2_col1].isin(sab_list)].drop_duplicates()
            match2 = matches[matches[df2_col2].isin(sab_list)].drop_duplicates()
        else: match1, match2 = None, None
        if match1 is not None and len(match1) > 0:
            match1['MATCH'] = str_match; match1[df_version_col] = df_version
            for idx, row in str_df_subset.iterrows():
                match1['MATCH_TYPE'] = str_match_type.format(df_type, search_string, row['MATCH'], row['MATCH_TYPE'])
                if row[main_key] in string_match_dict.keys(): string_match_dict[row[main_key]].append(match1)
                else: string_match_dict[row[main_key]] = [match1]
        elif match2 is not None and len(match2) > 0:
            match2['MATCH'] = str_match; match2[df_version_col] = df_version
            for idx, row in str_df_subset.iterrows():
                match2['MATCH_TYPE'] = str_match_type.format(df_type, search_string, row['MATCH'], row['MATCH_TYPE'])
                if row[main_key] in string_match_dict.keys(): string_match_dict[row[main_key]].append(match2)
                else: string_match_dict[row[main_key]] = [match2]
        else: continue

    if len(string_match_dict) > 0: return {k: pd.concat(v).drop_duplicates() for k, v in string_match_dict.items()}
    else: return None


def pickle_large_data_structure(data: Union[dict, pd.DataFrame], filepath: str) -> None:
    """Function writes a data object (i.e., dictionary or Pandas DataFrame) to disc employing a defensive way to write
    data, in order to allow for very large files on all platforms.

    Args:
        data: A python dictionary or Pandas DataFrame containing a very large amount of data.
        filepath: A string containing a valid file path and file name.

    Returns:
        None.
    """

    max_bytes, bytes_out = 2 ** 31 - 1, pickle.dumps(data)
    n_bytes = sys.getsizeof(bytes_out)
    with open(filepath, 'wb') as f_out:
        for idx in range(0, n_bytes, max_bytes):
            f_out.write(bytes_out[idx:idx + max_bytes])


def read_pickled_large_data_structure(filepath: str) -> Union[dict, pd.DataFrame]:
    """Function reads a pickled data object (i.e., dictionary or Pandas DataFrame) from disc employing a defensive way
    to read data, in order to allow for very large files on all platforms.

    Args:
        filepath: A string containing a valid file path and file name.

    Returns:
        None.
    """

    max_bytes = 2 ** 31 - 1
    input_size = os.path.getsize(filepath)
    bytes_in = bytearray(0)
    with open(filepath, 'rb') as f_in:
        for _ in range(0, input_size, max_bytes):
            bytes_in += f_in.read(max_bytes)
    data = pickle.loads(bytes_in)

    return data
