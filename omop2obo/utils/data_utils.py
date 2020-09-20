#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data PreProcessing Utility Functions.

Pandas DataFrame manipulations
* data_frame_subsetter
* data_frame_supersetter
* column_splitter
* aggregates_column_values
* data_frame_grouper
* normalizes_source_codes

Dictionary manipulations
* merge_dictionaries

"""

# import needed libraries
import pandas as pd  # type: ignore
import re

from functools import reduce
from more_itertools import unique_everseen
from tqdm import tqdm  # type: ignore
from typing import Callable, Dict, List  # type: ignore

# ENVIRONMENT WARNINGS
# WARNING 1 - Pandas: disable chained assignment warning rationale:
# https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas
pd.options.mode.chained_assignment = None


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
    combo = [data.groupby([primary_key])[col].apply(lambda x: delimiter.join(list(unique_everseen(x))))
             for col in agg_cols]

    # merge data frames by primary key and reset index
    merged_combo = reduce(lambda x, y: pd.merge(x, y, on=primary_key, how='outer'), combo)
    merged_combo.reset_index(level=0, inplace=True)

    return merged_combo


def data_frame_grouper(data: pd.DataFrame, primary_key: str, type_column: str, col_agg: Callable) -> \
        pd.DataFrame:
    """Methods takes a Pandas DataFrame as input, a primary key, and a column to group the data by and
    creates a new DataFrame that merges the individual grouped DataFrames into a single DataFrame.
    Examples of the input and output data are shown below.

    INPUT_DATA:
                   CONCEPT_ID         CONCEPT_DBXREF_ONT_URI  CONCEPT_DBXREF_ONT_TYPE         CONCEPT_DBXREF_EVIDENCE
            0         442264        http://...MONDO_0100010                     MONDO   CONCEPT_DBXREF_sctid:68172002
            2        4029098        http://...MONDO_0045014                     MONDO  CONCEPT_DBXREF_sctid:237913008
            4        4141365           http://...HP_0000964                        HP  CONCEPT_DBXREF_sctid:426768001

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


def normalizes_source_codes(data: pd.DataFrame, source_code_dict: Dict) -> pd.Series:
    """Takes a Pandas DataFrame column containing source code values that need normalization and normalizes them
    using values from a pre-built dictionary (resources/mappings/source_code_vocab_map.csv). The function is designed
    to normalize identifier prefixes according to the specifications in the source_code_dict. It provides some light
    regex support for the following scenarios:
        - ICD10CM:C85.92 --> icd10:c85.92
        - http://www.snomedbrowser.com/codes/details/12132356564 --> snomed_12132356564
        - http://www.orpha.net/ordo/orphanet_1920 --> orphanet_1920

    Assumption: assumes that the column to normalize is always the 0th index.

    Args:
        data: A column from a Pandas DataFrame containing unstacked identifiers that need normalization (e.g.
            umls:c123456, http://www.snomedbrowser.com/codes/details/12132356564, rxnorm:12345).
        source_code_dict: A dictionary keyed by input prefix with values reflecting the preferred prefixes in the
            source_code_dict file. For example:
                {'snomed': 'snomed', 'snomed_ct': 'snomed', 'snomed_ct_us_2018_03_01': 'snomed'}

    Returns:
        A Pandas Series that has been normalized.
    """

    # split prefix from number in each identifier
    prefix = data[data.columns[0]].apply(lambda j: j.rstrip([x for x in re.split('[_:|/]', j) if x != ''][-1])[:-1]
                                         if 'http' in j and '_' in j else
                                         j.rstrip([x for x in re.split('[:|/]', j) if x != ''][-1])[:-1])
    id_num = data[data.columns[0]].apply(lambda j: [x for x in re.split('[_:|/]', j) if x != ''][-1]
                                         if 'http' in j and '_' in j else
                                         [x for x in re.split('[:|/]', j) if x != ''][-1]).str.lower()

    # normalize prefix to dictionary and clean up urls
    norm_prefix = prefix.apply(lambda j: source_code_dict[j] if j in source_code_dict.keys() else j)

    # concat normalized identifier and number back together
    updated_source_codes = norm_prefix + ':' + id_num

    return updated_source_codes


def merge_dictionaries(dictionaries: Dict, key_type: str, reverse: bool = False) -> Dict:
    """Given any number of dictionaries, shallow copy and merge into a new dict, precedence goes to key value pairs
    in latter dictionaries.

    Function from StackOverFlow Post:
        https://stackoverflow.com/questions/38987/how-do-i-merge-two-dictionaries-in-a-single-expression-in-python

    Args:
        dictionaries: A nested dictionary.
        key_type: A string containing the key of one of the inner dictionaries.
        reverse: A bool indicating whether or not the dictionaries should be reversed before merging (default=False).

    Returns:
        combined_dictionary: A dictionary object containing.
    """

    combined_dictionary: Dict = {}

    for dictionary in dictionaries.keys():
        if reverse:
            combined_dictionary.update({v: k for k, v in dictionaries[dictionary][key_type].items()})
        else:
            combined_dictionary.update(dictionaries[dictionary][key_type])

    return combined_dictionary


def ohdsi_ananke(ont_keys: list, ont_data: pd.DataFrame, data1: pd.DataFrame, data2: pd.DataFrame) -> pd.DataFrame:
    """Function applies logic from the OHDSIAnanake method to extend data1, which contains dbxref mappings to OMOP
    concept ids with mappings from UMLS cuis to relevant umls ontology mappings. The merged data set is returned.

    Method adapted from: https://github.com/thepanacealab/OHDSIananke

    Args:
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
    merged_data_ont = merged_data_ont[['CONCEPT_ID', 'CUI', 'CODE_COLUMN', dbxref_col]]

    # update cuis column
    merged_data_ont['CUI'] = merged_data_ont['CUI'].apply(lambda x: 'umls:' + x)

    # rename columns
    merged_data_ont.columns = ['CONCEPT_ID', 'CODE', 'CODE_COLUMN', dbxref_col]

    return merged_data_ont


def normalizes_clinical_source_codes(dbxref_dict: Dict, source_dict: Dict):
    """Function takes two dictionaries and uses them to create a new dictionary. The first dictionary, contains ontology
    database cross references and the second contains content to normalize the identifiers contained in the first
    dictionary.

    Args:
        dbxref_dict: A dictionary of ontology identifiers and their database cross references.
        source_dict: A dictionary containing information for normalizing the prefixes of the database cross references.

        An example of each dictionary is shown below:
        - dbxref_dict = {'DbXref', 'umls:c4022862': 'DbXref', 'umls:c0008733': 'DbXref'}
        - source_dict = {'snm', 'snomed': 'snomed', 'snomed_ct': 'snomed', 'snomed_ct_us_2018_03_01': 'snomed'}

    Returns:
        normalized_prefixes: A dictionary where the keys are database cross references and the values are strings
            containing the database cross reference type and prefix from the key, separated by a star. For example:
            {'umls:c4022862': 'DbXref*umls', 'umls:c0008733': 'DbXref*umls'}
    """

    normalized_prefixes = {}

    # split prefix from number in each identifier
    for key, value in dbxref_dict.items():
        prefix, id_num = key.split(':')[0], key.split(':')[-1].lower()
        norm_prefix = source_dict[prefix] if prefix in source_dict.keys() else prefix
        normalized_prefixes[norm_prefix + ':' + id_num] = value + '*' + prefix

    return normalized_prefixes


def compiles_mapping_content(data_row: pd.Series, ont: str) -> List:
    """Function takes a row of data from a Pandas DataFrame and processes it to return a single ontology mapping for
    the clinical concept represented by the row.

    Args:
        data_row: A row from a Pandas DataFrame cont
        ont: A string containing the name of an ontology (e.g. "HP", "MONDO").

    Returns:
        mapping_result: A list containing mapping results for a given row. The list contains three items: uris,
        labels, evidence.
    """

    for level in ['CONCEPT', 'ANCESTOR']:
        dx_id, dx_lab, dx_ev, str_id, str_lab, str_ev, sim_id, sim_lab, sim_ev = ([] for _ in range(9))  # type: ignore

        # dbxrefs
        dx_id += [data_row[x].split(' | ') for x in data_row.keys() if level + '_DBXREF_' + ont + '_URI' in x]
        dx_lab += [data_row[x].split(' | ') for x in data_row.keys() if level + '_DBXREF_' + ont + '_LABEL' in x]
        dx_ev += [data_row[x] for x in data_row.keys() if level + '_DBXREF_' + ont + '_EVIDENCE' in x]
        # strings
        str_id += [data_row[x].split(' | ') for x in data_row.keys() if level + '_STR_' + ont + '_URI' in x]
        str_lab += [data_row[x].split(' | ') for x in data_row.keys() if level + '_STR_' + ont + '_LABEL' in x]
        str_ev += [data_row[x] for x in data_row.keys() if level + '_STR_' + ont + '_EVIDENCE' in x]
        # concept similarity
        sim_id += [data_row[x].split(' | ') for x in data_row.keys() if ont + '_SIM_ONT_URI' in x]
        sim_lab += [data_row[x].split(' | ') for x in data_row.keys() if ont + '_SIM_ONT_LABEL' in x]
        sim_ev += [data_row[x] for x in data_row.keys() if ont + '_SIM_ONT_EVIDENCE' in x]

        if (dx_id != [] or str_id != []) and (dx_id[0] != [''] or str_id[0] != ['']): break

    # put together mapping
    if (dx_id == [] or str_id == []) or (dx_id[0] == [''] or str_id[0] == ['']):
        mapping_result = [None] * 3  # type: ignore
    else:
        if dx_id[0][0] != '' or str_id[0][0] != '':
            uris = list(unique_everseen([x.split('/')[-1] for x in dx_id[0]] + [x.split('/')[-1] for x in str_id[0]]))
            labels = list(unique_everseen([x for x in dx_lab[0]] + [x for x in str_lab[0]]))
            evidence = list(unique_everseen(dx_ev + str_ev))
            # determine if similarity should be added and add the overlapping uri's evidence
            evidence += [sim_ev[0].split(' | ')[x] for x in [sim_id[0].index(x) for x in sim_id[0] if x in uris]]
            mapping_result = [uris, labels, ' | '.join(evidence)]  # type: ignore
        else:
            mapping_result = [sim_id, sim_lab, ' | '.join(sim_ev)]  # type: ignore

    return mapping_result


def formats_mapping_evidence(ont_dict: dict, source_dict: Dict, result: List, clin_data: Dict) -> str:
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
        compiled_evid: A string containing the compiled mapping evidence. For example:
            'OBO_LABEL-OMOP_CONCEPT_LABEL:abetalipoproteinemia | CONCEPT_SIMILARITY:HP_0008181_1.0'.
    """

    dbx_evid, label_evid, syn_evid, sim_evid = ([] for _ in range(4))  # type: ignore
    ont_label, ont_syns, ont_syntyp = ont_dict['label'], ont_dict['synonym'], ont_dict['synonym_type']
    dbxref_type = normalizes_clinical_source_codes(ont_dict['dbxref_type'], source_dict)

    # sort clinical data
    for x in result[2].split(' | '):
        level = [x.split('_')[0] if ':' in x else 'CONCEPT_SIMILARITY'][0]
        clin_update = {k: v for k, v in clin_data.items() if level in k}

        if 'dbxref' in x.lower():
            if x.split('_')[-1] in dbxref_type.keys(): prefix = dbxref_type[x.split('_')[-1]]
            else: prefix = 'DbXref*' + x.split('_')[-1].split(':')[0]
            updated_prefix = 'OBO_' + prefix.split('*')[0] + '-OMOP_' + level + '_CODE'
            dbx_evid.append(updated_prefix + ':' + prefix.split('*')[-1] + '_' + x.split(':')[-1].replace(':', '_'))
        if 'label' in x.lower():
            label_evid, clin_lab = [], ' | '.join([clin_update[x] for x in clin_update.keys() if 'label' in x.lower()])
            for lab in set(clin_lab.split(' | ')):
                if lab.lower() in ont_label.keys() and ont_label[lab.lower()].split('/')[-1] in result[0]:
                    label_evid.append('OBO_LABEL-OMOP_' + x.split('_')[0] + '_LABEL:' + x.split(':')[-1])
                if lab.lower() in ont_syns.keys() and ont_syns[lab.lower()].split('/')[-1] in result[0]:
                    label_evid.append('OBO_' + ont_syntyp[lab.lower()] + '-OMOP_CONCEPT_LABEL:' + x.split(':')[-1])
        if 'synonym' in x.lower():
            syn_evid, clin_syn = [], ' | '.join([clin_update[x] for x in clin_update.keys() if 'synonym' in x.lower()])
            for syn in set(clin_syn.split(' | ')):
                if syn.lower() in ont_label.keys() and ont_label[syn.lower()].split('/')[-1] in result[0]:
                    syn_evid.append('OBO_LABEL-OMOP_' + x.split('_')[0] + '_SYNONYM:' + x.split(':')[-1])
                if clin_syn.lower() in ont_syns.keys() and ont_syns[syn.lower()].split('/')[-1] in result[0]:
                    syn_lab = '-OMOP_' + level + '_SYNONYM:'
                    syn_evid.append('OBO_' + ont_syntyp[syn.lower()] + syn_lab + x.split(':')[-1])
        if level == 'CONCEPT_SIMILARITY':
            sim_evid.append('CONCEPT_SIMILARITY:' + x)

    # compile evidence
    compiled_evid = ' | '.join(list(filter(None, list(unique_everseen(dbx_evid + label_evid + syn_evid + sim_evid)))))

    return compiled_evid


def assigns_mapping_category(mapping_result: List, mapping_evidence: str) -> str:
    """Function takes a mapping result and evidence and uses it to determine the mapping category.

    Args:
        mapping_result: A list containing mapping results for a given row. The list contains three items: uris, labels,
            evidence.
        mapping_evidence: A string containing the compiled mapping evidence.

    Returns:
         mapping_category: A string containing the mapping category.
    """

    # determine if mapping is exact or constructor
    if len(mapping_result[0]) == 1:
        if 'CONCEPT_SIMILARITY:' in mapping_evidence and len(mapping_evidence.split(' | ')) == 1:
            mapping_category = 'Manual Exact - Concept Similarity'
        else:
            mapping_category = 'Automatic Exact - '
    elif len(mapping_result[0]) > 1:
        mapping_category = 'Automatic Constructor - '
    else:
        mapping_category = ''

    # determine mapping level (i.e. concept or ancestor)
    if any(x for x in ['CONCEPT_CODE', 'CONCEPT_SYNONYM', 'CONCEPT_LABEL'] if x in mapping_evidence):
        mapping_category = mapping_category + 'Concept'
    elif any(x for x in ['ANCESTOR_CODE', 'ANCESTOR_SYNONYM', 'ANCESTOR_LABEL'] if x in mapping_evidence):
        mapping_category = mapping_category + 'Ancestor'
    else:
        mapping_category = mapping_category

    return mapping_category


def aggregates_mapping_results(data: pd.DataFrame, onts: List, ont_data: Dict, source_codes: Dict) -> pd.DataFrame:
    """Function takes a Pandas Dataframe containing the results from running the OMOP2OBO exact and similarity
    mapping functions. This function takes those results and aggregates them such that a single column set of
    evidence is returned for each ontology (i.e. uris, labels, mapping category, and mapping evidence).

    #TODO: this function could be parallelized

    Args:
        data: A Pandas DataFrame of mapping results from running the OMOP2OBO exact mapping and concept similarity
            pipeline.
        onts: A list of strings representing ontologies (e.g. ["hp", "mondo"]).
        ont_data: A nested dictionary of ontology data including mappings between ontology class URIs, labels,
            synonyms, definitions, and dbxrefs.
        source_codes: A dictionary containing dbxref mappings between dbxref prefixes that is designed to normalize
            prefixes to a single type.

    Return:
        A Pandas DataFrame
    """

    print('\n*** Aggregating and Compiling Mapping Results')

    # set input variables
    cols = [x.lower() for x in data.columns]
    clin_cols = [x for x in cols if (x.endswith('label') or x.endswith('nym')) and not any(y for y in onts if y in x)]

    for ont in [x.upper() for x in onts]:
        print('Processing {} Mappings'.format(ont))
        mappings = []
        for idx, row in tqdm(data.iterrows(), total=data.shape[0]):
            ont_list = ['DBXREF_' + ont, 'STR_' + ont, ont + '_SIM']
            res = [x for x in row.keys() if row[x] != '' and any(y for y in ont_list if y in x)]
            if len(res) != 0:
                # aggregate mapping info
                map_info = compiles_mapping_content(row, ont)
                # format aggregated mapping evidence
                clin_data = {x.upper(): row[x.upper()] for x in clin_cols if x.upper() in row.keys()}
                ont_dict = ont_data[ont.lower() if ont != 'uberon' else 'ext']
                map_evidence = formats_mapping_evidence(ont_dict, source_codes, map_info, clin_data)
                # assign mapping type to aggregated map
                map_category = assigns_mapping_category(map_info, map_evidence)
                # update mapping results dict
                mappings.append([' | '.join(map_info[0]), ' | '.join(map_info[1]), map_category, map_evidence])
            else:
                mappings.append([None, None, None, None])  # type: ignore

        # add aggregated mapping results back to data frame
        data['AGGREGATED_' + ont + '_URI'] = [x[0] for x in mappings]
        data['AGGREGATED_' + ont + '_LABEL'] = [x[1] for x in mappings]
        data['AGGREGATED_' + ont + '_MAPPING'] = [x[2] for x in mappings]
        data['AGGREGATED_' + ont + '_EVIDENCE'] = [x[3] for x in mappings]

    return data
