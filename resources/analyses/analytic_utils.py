#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Analytic Utility Functions.

Clinical Data Manipulation
* reconfigures_dataframe
* splits_concept_levels

Ontology Data Manipulation
* outputs_ontology_metadata

Statistical Testing
* get_asterisks_for_pvalues
* chisq_and_posthoc_corrected

"""

# import needed libraries
import numpy as np  # type: ignore
import pandas as pd  # type: ignore
import statistics

from collections import Counter
from itertools import combinations  # type: ignore
from scipy.stats import chi2_contingency  # type: ignore
from sklearn.preprocessing import MinMaxScaler
from statsmodels.sandbox.stats.multicomp import multipletests  # type: ignore
from tqdm import tqdm
from typing import Dict, List, Optional, Set


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

    # make sure that all blank variables are converted to NaN
    data_frame = data_frame.replace(r'^\s*$', np.nan, regex=True)

    # identify which columns belong to each of the input ontologies
    category_split_data = []
    for x in split_list:
        # get category-specific columns
        cat_columns = [i for i in data_frame.columns if x.lower() in i.lower()]
        # subset original data to include non-category and specific single category data
        cat_data = data_frame[non_category_columns + cat_columns].drop_duplicates()
        # drop rows where all category columns are NaN and blank string
        cat_data = cat_data.dropna(subset=cat_columns, how='all')
        cat_data.columns = non_category_columns + [col.upper().replace(x.upper(), 'CATEGORY') for col in cat_columns]
        # add category specific column
        cat_data['CATEGORY'] = [x] * len(cat_data)
        category_split_data.append(cat_data)

    # concatenate stacked data into single DataFrame
    reconfigured_data = pd.concat(category_split_data)

    return reconfigured_data.fillna('').drop_duplicates()


def splits_concept_levels(data: pd.DataFrame, type_col: Optional[str], concept_strings: List) -> List:
    """Takes a Pandas DataFrame and a string containing a keyword and with the keyword, splits the input DataFrame
    into concept and ancestor-level data. The keyword is used to obtain relevant columns where the data differs for
    concepts and ancestors.

    Args:
        data: A Pandas DataFrame containing stacked mapping results.
        type_col: A string containing the data type to parse (e.g. "DBXREF" or "STR").
        concept_strings: A list of strings where the first string is a concept-level identifier and the second item
            is an ancestor-level identifier.

    Returns:
        A list of tuples, each tuple contains a Pandas DataFrame and a list, the first contains a subset of the
            original data to a specific set of columns and the list contains all ontology concepts that were
            annotated to the OMOP concepts contained in the Pandas DataFrame. The first tuple contains data at the
            concept level and the second tuple contains data at the ancestor level.
    """

    con_string, anc_string = concept_strings
    data = data.copy().replace(r'^\s*$', np.nan, regex=True)

    # extract relevant columns
    if type_col is not None:
        all_cols = [x for x in data.columns if type_col not in x]
        conc_type = [x for x in data.columns if con_string.upper() in x.upper() and type_col.upper() in x.upper()]
        anc_type = [x for x in data.columns if anc_string.upper() in x.upper() and type_col.upper() in x.upper()]
        if len(anc_type) > 0 and len(conc_type) > 0:
            conc_type_uri = [x for x in conc_type if x.upper().endswith('URI')][0]
            anc_type_uri = [x for x in anc_type if x.upper().endswith('URI')][0]
            # extract concept codes from ancestor codes
            concept = data[all_cols + conc_type].dropna(subset=conc_type, how='all').drop_duplicates()
            ancestor = data[all_cols + anc_type].dropna(subset=anc_type, how='all').drop_duplicates()
            # get counts of ontology concepts at each concept level
            concept_ont_codes = [i for j in [x.split(' | ') for x in list(concept[conc_type_uri])] for i in j]
            ancestor_ont_codes = [i for j in [x.split(' | ') for x in list(ancestor[anc_type_uri])] for i in j]

            return [(concept, concept_ont_codes), (ancestor, ancestor_ont_codes)]
        elif len(conc_type) == 0 and len(anc_type) > 0:
            anc_type_uri = [x for x in anc_type if x.upper().endswith('URI')][0]
            # extract concept codes
            ancestor = data[all_cols + anc_type].dropna(subset=anc_type, how='all').drop_duplicates()
            # get counts of ontology concepts at each concept level
            ancestor_ont_codes = [i for j in [x.split(' | ') for x in list(ancestor[anc_type_uri])] for i in j]

            return [(None, None), (ancestor, ancestor_ont_codes)]
        else:
            conc_type_uri = [x for x in conc_type if x.upper().endswith('URI')][0]
            # extract concept codes from ancestor codes
            concept = data[all_cols + conc_type].dropna(subset=conc_type, how='all').drop_duplicates()
            # get counts of ontology concepts at each concept level
            concept_ont_codes = [i for j in [x.split(' | ') for x in list(concept[conc_type_uri])] for i in j]

            return [(concept, concept_ont_codes), (None, None)]
    else:
        concept = data[[x for x in data.columns if x.startswith(con_string)]].dropna(how='all').drop_duplicates()
        ancestor = data[[x for x in data.columns if x.startswith(anc_string)]].dropna(how='all').drop_duplicates()
        concept_ont_codes, ancestor_ont_codes = [], []

        return [(concept, concept_ont_codes), (ancestor, ancestor_ont_codes)]


def outputs_ontology_metadata(ontology_data: Dict, ontology_list: List, metadata: List) -> Dict:
    """Method takes a nested dictionary of ontology

    Args:
        ontology_data: A nested dictionary containing metadata for each ontology. The outer keys are strings
            representing ontology prefixes (e.g. 'hp', 'mondo').
        ontology_list: A list of ontologies to use when filtering the ontology dictionary (e.g. ['HP', 'MONDO']).
        metadata: A list of string specifying what ontology metadata to retrieve for each ontology.

    Returns:
        ontology_subset: A nested dictionary keyed by lower-cased ontology prefix string (e.g. 'hp, 'mondo') with
            inner dictionaries keyed by items in metadata and having numeric or string values. An example is shown
            below:
                {{'hp': {'label': 15247,
                         'dbxref': 19569,
                         'synonym': 19860,
                         'synonym_type': 'hasNarrowSynonym, hasExactSynonym, hasRelatedSynonym, hasBroadSynonym'}
                }}
    """

    # lowercase all ontologies in list
    updated_ontology_list = list(map(lambda x: x.lower(), ontology_list))

    # reduce ont dictionary to relevant ontologies
    ontology_subset_dictionary = {k: v for k, v in ontology_data.items() if k in updated_ontology_list}

    # obtain specific ontology metadata
    ontology_subset = {}
    for ont in updated_ontology_list:
        ont_sub = ontology_subset_dictionary[ont]
        ontology_subset[ont] = {x: len(ont_sub[x]) for x in metadata if x != 'synonym_type'}
        ontology_subset[ont]['synonym_type'] = ', '.join(set(ont_sub['synonym_type'].values()))  # type: ignore

    return ontology_subset


def get_asterisks_for_pvalues(p_value: float) -> str:
    """Receives the p-value and returns asterisks string.

    Args:
        p_value: A float that represents a p-value.

    Returns:
        p_text: A string containing an asterisk representation of the p-value significance.
    """
    if p_value > 0.05:
        p_text = 'ns'  # above threshold => not significant
    elif p_value < 1e-4:
        p_text = '****'
    elif p_value < 1e-3:
        p_text = '***'
    elif p_value < 1e-2:
        p_text = '**'
    else:
        p_text = '*'

    return p_text


def chisq_and_posthoc_corrected(df: pd.DataFrame, correction: str = 'bonferroni') -> pd.DataFrame:
    """Receives a dataframe and performs chi2 test and then post hoc. Prints the p-values and corrected p-values (
    after FDR correction). This method is modified from: https://neuhofmo.github.io/chi-square-and-post-hoc-in-python/.

    Args:
        df: A Pandas DataFrame containing cross-tabulated results.
        correction: A string containing a multiple testing correction method. The full list of correction methods can
            be found here: https://www.statsmodels.org/dev/_modules/statsmodels/stats/multitest.html#multipletests

    Returns:
        post_hoc_results: A Pandas DataFrame containing the results from performing post-hoc testing. An example of
            the output is shown below.

            OUTPUT:
                                      comparison  original_pvalue  corrected_pvalue  reject_h0
                0           CHEBI-CL    5.488896e-284     5.911118e-284       True
                1           CHEBI-HP     0.000000e+00      0.000000e+00       True
                2        CHEBI-MONDO     0.000000e+00      0.000000e+00       True
                3    CHEBI-NCBITaxon     0.000000e+00      0.000000e+00       True
                4           CHEBI-PR     0.000000e+00      0.000000e+00       True
                5       CHEBI-UBERON     0.000000e+00      0.000000e+00       True
    """

    # perform chi-square omnibus test on full data
    chi2, p, dof, ex = chi2_contingency(df, correction=True)
    print('Chi-Square Omnibus Test Results: Test statistic: {}, df: {}, p-value: {}'.format(chi2, dof, p))

    # post-hoc analysis
    print('Performing post hoc testing using: {} p-value correction method'.format(correction))
    p_values, all_combinations = [], list(combinations(df.index, 2))  # gathering all combinations for post-hoc chi2

    for comb in all_combinations:
        new_df = df[(df.index == comb[0]) | (df.index == comb[1])]
        chi2, p, dof, ex = chi2_contingency(new_df, correction=True)
        p_values.append(p)

    # checking significance and application of correction for multiple testing
    reject_list, corrected_p_vals = multipletests(p_values, method=correction)[:2]

    # save results to a pandas df
    post_hoc_results = pd.DataFrame({'comparison': ['-'.join(x) for x in all_combinations],
                                     'original_pvalue': p_values,
                                     'corrected_pvalue': list(corrected_p_vals),
                                     'reject_h0': list(reject_list)})

    return post_hoc_results


def process_clinical_data(data: pd.DataFrame, grp_var: str) -> Dict:
    """Method takes a Pandas data frame assumed to have data that will be used for mapping and a string representing
    a column in that DataFrame that can be used to group the data. The function then groups the data and outputs

    Args:
        data: A Pandas DataFrame that contains OMOP data.
        grp_var: A string representing a column to group by.

    Returns:
        results: A dictionary of results where keys are categories of the grp_var and values are lists of concept and
            ancestor-level data.
    """

    # split results by concept type (i.e. concepts used in practice, standard concepts)
    grouped_data = data.groupby(grp_var)

    # obtain results for groups
    results = {}
    for grp in grouped_data.groups.keys():
        results[grp] = {}
        print('Processing Group: {}'.format(grp))

        # get group data
        grp_data = grouped_data.get_group(grp).drop_duplicates()
        results[grp]['grp_full_data'] = grp_data
        # get concept data
        results[grp]['concept_src_code'] = [x for y in grp_data['CONCEPT_SOURCE_CODE'] for x in y.split(' | ')]
        results[grp]['concept_src_label'] = [x for y in grp_data['CONCEPT_LABEL'] for x in y.split(' | ')]
        results[grp]['concept_synonym'] = [x for y in grp_data['CONCEPT_SYNONYM'] for x in y.split(' | ')]
        results[grp]['concept_vocab'] = ', '.join(set([x for y in grp_data['CONCEPT_VOCAB'] for x in y.split(' | ')]))
        # get ancestor data
        results[grp]['anc_concept_id'] = [x for y in grp_data['ANCESTOR_CONCEPT_ID'] for x in y.split(' | ')]
        results[grp]['anc_src_code'] = [x for y in grp_data['ANCESTOR_SOURCE_CODE'] for x in y.split(' | ')]
        results[grp]['anc_label'] = [x for y in grp_data['ANCESTOR_LABEL'] for x in y.split(' | ')]
        results[grp]['anc_vocab'] = ', '.join(set([x for y in grp_data['ANCESTOR_VOCAB'] for x in y.split(' | ')]))

    return results


def gets_data_by_concept_type(grouped_data: pd.DataFrame, data_type: str) -> Dict:
    """Takes a Pandas DataFrame containing grouped data and processes data for each of the groups. Specifically,
    the data for each group is processed in order to obtain data at the concept and ancestor level. The function
    returns a nested list of processed data for each group.

    Args:
        grouped_data: A grouped Pandas DataFrame containing data that needs to be processed.
        data_type: String containing the type of data to search for (e.g. "DBXREF").

    Returns:
        group_data: A dictionary keyed by group in grouped_data with values as a list of lists where the first sub-list
            contains concept-level data and the second sub-list contains ancestor-level data. Within each specific
            sub-list is a list. The first item is a Pandas DataFrame and the second list is a list of all identifiers.
    """

    group_data = {}

    # get groups to process
    groups = list(grouped_data.groups.keys())

    # split stacked data by concept type
    for grp in groups:
        concept_grp = grouped_data.get_group(grp).drop_duplicates()

        # concepts used in practice
        group_data[grp] = {}
        group_data[grp]['data'] = concept_grp
        group_data[grp]['level data'] = splits_concept_levels(concept_grp, data_type, ['concept', 'ancestor'])

    return group_data


def process_mapping_results(data: pd.DataFrame, ont_list: List, grp_var: str, data_type: str = None) -> Dict:
    """Function takes a Pandas DataFrame, a list of ontologies, a grouping variable, and a data type. using this
    information, the function first groups the data by each ontology type. Then, the function further groups the data
    by the grp_var to obtain the data stored in the columns noted by data_type. Finally, the data is grouped one last
    time at the concept and ancestor level. The function returns a nested dictionary keyed by ontology,
    with the inner dictionary keyed by each level of the grp_var and with values being a third dictionary that is
    keyed by data level (i.e. "concept" or "ancestor") with values that contain 2 lists. The first item int he list
    is a Pandas DataFrame and the second item is a list of all identifiers.

    Args:
        data: A Pandas DataFrame containing mapping data that needs to be processed.
        ont_list: A list of strings representing ontologies to process (e.g. ["HP", "MONDO"]).
        grp_var: String containing the type of data to group by (e.g. "CONCEPT-TYPE").
        data_type: String containing the type of data to search for (e.g. "DBXREF").

    Returns:
        A dictionary keyed by ontology that contains processed results for the input data_type for each group in the
            grp_var and further within each group at the concept and ancestor level.
    """

    # make data long-form with ontologies stacked as a type of category
    data_stacked = reconfigures_dataframe(ont_list, data)

    # group by ontology
    data_stacked_category_grp = data_stacked.groupby('CATEGORY')

    # process results by ontology
    ontology_results = {}
    for ont in ont_list:
        if ont in '_'.join(list(data.columns)):
            print('Processing Ontology: {}'.format(ont))

            # get individual ontology results
            ontology_results[ont] = {}
            data_stacked_ont = data_stacked_category_grp.get_group(ont).drop_duplicates().drop('CATEGORY', 1)
            ontology_results[ont]['ont_data'] = data_stacked_ont

            # group ont data by concept type (i.e. concepts used in practice, standard concepts)
            data_stacked_ont_grp = data_stacked_ont.groupby(grp_var)

            # get concept type group information
            group_results = gets_data_by_concept_type(data_stacked_ont_grp, data_type)

            # process and organize grouped results
            for res in group_results.keys():
                ontology_results[ont][res] = {}
                ontology_results[ont][res]['data'] = group_results[res]['data']
                ontology_results[ont][res]['concepts'] = group_results[res]['level data'][0]
                ontology_results[ont][res]['ancestors'] = group_results[res]['level data'][1]

    return ontology_results


def process_mapping_evidence(evidence_data: List):
    """Function takes a list of pipe-delimited values and parses the list to extract the different evidence types.

    Args:
        evidence_data: A list of evidence, where each entry is a pipe-delimited string of evidence.

    Returns:
        evidence_data: A dictionary containing the mapping evidence, keyed by evidence type.
    """

    # create evidence dictionary
    all_results = [j for k in [x.split(':') for y in evidence_data for x in y.split(' | ')] for j in k]
    dbxref_results = [x.split(':')[1] for y in evidence_data for x in y.split(' | ') if 'dbxref' in x.lower()]
    synonym_results = [x.split(':')[0] for y in evidence_data for x in y.split(' | ') if 'synonym' in x.lower()]
    syn_type = Counter([y.split('_')[1] for y in [x.split('-')[0] for x in synonym_results] if 'synonym' in y.lower()])
    label_results = [x.split(':')[0] for y in evidence_data for x in y.split(' | ') if 'label' in x.lower()]
    similarity_results = [float(x.split('_')[-1]) for y in evidence_data for x in y.split(' | ')
                          if 'similarity' in x.lower()]

    # aggregate evidence
    evidence = {'all': all_results, 'dbxref': dbxref_results, 'synonym': synonym_results,
                'synonym_type': syn_type, 'label': label_results, 'similarity': similarity_results}

    return evidence


def min_max_scaler(score_lists: List) -> List:
    """Method takes a list of lists, where each list contains a list of ints or floats and performs min-max
    normalization.

    Args:
        score_lists: A list of lists of ints or floats, where each float represents a score.

    Returns:
        normalized_scores: A single list of min/max normalized scores.
    """

    normalized_scores = []

    # instantiate sklearn scaler
    scaler = MinMaxScaler(feature_range=(0, 1))

    for scores in score_lists:
        scaled_scores = scaler.fit_transform(np.asarray(scores).reshape(-1, 1))
        scaled_scores_list = np.concatenate(scaled_scores, axis=0).tolist()
        normalized_scores += scaled_scores_list

    return normalized_scores


def output_coverage_set_counts(prim_data: pd.DataFrame, sec_data: pd.DataFrame, coverage_sets: List) -> Dict:
    """Function takes a primary Pandas DataFrame (assumed to contain concept prevalence data) and a secondary Pandas
    DataFrame assumed to contain (omop2obo data) and a list of coverage sets. Using this information the concept
    frequency values are extracted and returned as a dictionary.

    Args:
        prim_data: A Pandas DataFrame containing concept prevalence data.
        sec_data: A Pandas DataFrame containing OMOP2OBO concept data.
        coverage_sets: A list of concept sets in the following order: overlap, cp only, omop2obo only.

    Returns:
         coverage: A dictionary keyed by set type with values representing lists of processed concept data and counts.
    """

    # coverage sets
    overlap_concepts, cp_concepts_only, omop2obo_concepts_only = coverage_sets

    coverage = {}

    # get overlap set info
    overlap = prim_data[prim_data.CONCEPT_ID.isin(list(overlap_concepts))].fillna(0.0)
    overlap_only = overlap.groupby('CONCEPT_ID')['RECORD_COUNT'].mean().reset_index(name='MEAN_CONCEPT_COUNT')

    # get cp only info
    cp_df = prim_data[prim_data.CONCEPT_ID.isin(list(cp_concepts_only))][['CONCEPT_ID', 'CONCEPT_NAME', 'RECORD_COUNT']]
    cp_only = cp_df.drop_duplicates()
    cp_only = cp_only.groupby('CONCEPT_ID')['RECORD_COUNT'].mean().reset_index(name='MEAN_CONCEPT_COUNT')

    # get omop2obo only info
    omop2obo = sec_data[sec_data.CONCEPT_ID.isin(list(omop2obo_concepts_only))].fillna('')
    omop2obo_only = omop2obo[omop2obo['CONCEPT_COUNT_ADJUSTED'] != '']

    # get counts - converting NaN for concepts not used in practice to 0.0
    coverage['overlap'] = {'data': overlap_only, 'counts': list(np.log10(overlap_only['MEAN_CONCEPT_COUNT']))}
    coverage['cp_only'] = {'data': cp_only, 'counts': list(np.log10(cp_only['MEAN_CONCEPT_COUNT']))}
    coverage['omop2obo_only'] = {'data': omop2obo_only,
                                 'counts': list(np.log10(omop2obo_only['CONCEPT_COUNT_ADJUSTED'].values.astype(float)))}

    return coverage


def gets_group_stats(prim_data: pd.DataFrame, sec_data: pd.DataFrame, grp_col: str, concept_col: str) -> dict:
    """Function takes two Pandas Dataframes, one assumed to contain OMOP2OBO data and the other assumed to contain
    Concept Prevalence data. These data sets are processed in order to obtain the the concepts that overlap and don't
    overlap for each database.

    Args:
        prim_data: A Pandas DataFrame containing OMOP vocabulary concepts from external databases.
        sec_data: A Pandas DataFrame containing OMOP2OBO OMOP vocabulary concepts.
        grp_col: A string representing a column in the prim_data and sec_data sources that stores the OMOP vocabulary
            concepts.
        concept_col: A string representing a column that stores grouping variables

    Returns:
        db_compared_data: A nested dictionary containing keys for each external database being compared and for each
            of these keys there is a dictionary containing three additional keys, a dictionary of overlapping
            concepts between the specific secondary data source and the primary data source, a dictionary of concepts
            that only occurred in the primary data source, and a dictionary of concepts that only occurred in the
            secondary data source.
    """

    # preprocess secondary data
    sec_data.fillna(0, inplace=True)
    sec_count_col = [x for x in sec_data.columns if 'count_adjusted' in x.lower()][0]
    sec_concepts = set(sec_data[concept_col])
    sec_dict = {x[0]: int(x[1]) for x in list(zip(list(sec_data[concept_col]), list(sec_data[sec_count_col])))}
    # preprocess primary data
    prim_count_col = [x for x in prim_data.columns if 'count' in x.lower()][0]
    prim_data_grps = prim_data.groupby(grp_col)
    print('Processing {} Database groups\n'.format(len(prim_data_grps.groups.keys())))

    # loop over each database and compare against secondary data
    db_compared_data = {}
    for grp in tqdm(prim_data_grps.groups.keys()):
        db_compared_data[grp] = {}
        # print('Processing Database: {}'.format(grp))

        # get group data
        db_df = prim_data_grps.get_group(grp)

        # create dictionary out of concepts and counts
        prim_dict = {x[0]: x[1] for x in list(zip(list(db_df[concept_col]), list(db_df[prim_count_col])))}

        # get coverage data
        overlap = set(prim_dict.keys()).intersection(sec_concepts)
        prim_only = set(prim_dict.keys()).difference(sec_concepts)
        sec_only = sec_concepts.difference(set(prim_dict.keys()))

        # save output to dict
        db_compared_data[grp]['overlap'] = {x: prim_dict[x] for x in overlap}
        db_compared_data[grp]['primary_only'] = {x: prim_dict[x] for x in prim_only}
        db_compared_data[grp]['secondary_only'] = {x: sec_dict[x] for x in sec_only}

    return db_compared_data


def process_error_analysis_data(error_data: pd.DataFrame, missing_concepts: Set, data1: pd.DataFrame,
                                data2: pd.DataFrame, data3: pd.DataFrame) -> List:
    """
    Function takes several Pandas DataFrames and a set of concepts that were found to be missing from the OMOP2OBO
    mapping set. The function proceeds to create several Pandas DataFrames which provide a different explanation for
    the set of missing concepts.

    Args:
        error_data: A Pandas DataFrame containing OMOP data intended for use in the error analysis.
        missing_concepts: A set of concepts that were not found in the OMOP2OBO mappings.
        data1: A Pandas DataFrame containing ineligible OMOP2OBO mapping data.
        data2: A Pandas DataFrame containing eligible OMOP2OBO mapping data.
        data3: A Pandas DataFrame containing concept prevalence data.

    Return:
        A list of 3 Pandas DataFrames, where the first df contains missing concepts found in the error analysis data,
            the second df contains missing concepts that were contained in the ineligible conditions data, and the
            third df contains missing concepts that are truly missing.
    """

    # find not covered concepts in error analysis data
    error_analysis_concepts = set(error_data['TARGET_CONCEPT_ID']).intersection(missing_concepts)
    error_analysis_concepts_data = error_data[error_data.TARGET_CONCEPT_ID.isin(error_analysis_concepts)]

    # find not covered concepts in excluded clinical mapping data
    filtered_cond_maps = set(data1['CONCEPT_ID']).difference(set(data2['CONCEPT_ID']))
    filtered_cond_maps_not_ea = filtered_cond_maps.difference(error_analysis_concepts)
    filtered_concepts = filtered_cond_maps_not_ea.intersection(missing_concepts)
    filtered_concepts_data = data1[data1.CONCEPT_ID.isin(filtered_concepts)]

    # remaining not covered concepts (n=74)
    true_not_covered = missing_concepts.difference(set(list(error_analysis_concepts) + list(filtered_concepts)))
    true_not_covered_concepts_data = data3[data3.CONCEPT_ID.isin(true_not_covered)]

    return [error_analysis_concepts_data, filtered_concepts_data, true_not_covered_concepts_data]


def classifies_missing_concepts(data: pd.DataFrame, ont_list: List, key: str, db_type: str, dbs: List) -> Dict:
    """
    Function takes Pandas DataFrames missing OMOP2OBO data and converts them into a nested dictionary where keys
    contain different types of information on each missing concept. An example is shown below.

    Args:
        data: A Pandas DataFrame containing concept data.
        ont_list: A list of ontology prefixes (e.g. ['HP', 'MONDO']).
        key: A string containing the name of the primary concept id column.
        db_type: A string specifying the type of data in the data var.
        dbs: A list of Panda DataFrames. It is assumed that the first df contains concept prevalence data, the second
            df contains

    Return:
        error_analysis_org: A nested dictionary keyed by concept with a sub-dictionary containing information on each
            concept. For example:
                {35622917: {'dbs': 1, 'avg_count': 246, 'error_analysis_info': 'Newly Added Concept',
                            'evidence': ['HP:Manual Constructor', 'MONDO:Automatic Exact - Ancestor']},
                36716551: {'dbs': 13, 'avg_count': 195.30769230769232, 'error_analysis_info': 'Newly Added Concept',
                           'evidence': ['HP:INJURY', 'MONDO:INJURY']}

    """

    main_data, excluded_data, mapping_data = dbs
    concept_ids = set((data[key]))
    error_analysis_org = {db_type: {}}

    for concept in tqdm(concept_ids):
        src_ids = []
        error_analysis_org[db_type][concept] = {}

        # get concept count info from concept prevalence data
        concept_data = main_data.query('CONCEPT_ID == {}'.format(concept))
        error_analysis_org[db_type][concept]['dbs'] = len(concept_data)
        error_analysis_org[db_type][concept]['avg_count'] = statistics.mean(list(concept_data['RECORD_COUNT']))

        if db_type == 'error':
            relations_type = data.query('TARGET_CONCEPT_ID == {}'.format(concept))
            if 'Replaced Concept' in list(relations_type['SCENARIO_TYPE']): rel_type = 'Replaced Concept'
            else: rel_type = 'Newly Added Concept'
            src_ids = set(relations_type['SOURCE_CONCEPT_ID'])
            error_analysis_org[db_type][concept]['error_analysis_info'] = rel_type
        if db_type == 'excluded': src_ids = [concept]
        # get evidence
        if len(src_ids) > 0:
            evidence = []
            for src in src_ids:
                if src in list(mapping_data['CONCEPT_ID']):
                    row_data = mapping_data.query('CONCEPT_ID == {}'.format(src))
                else:
                    row_data = excluded_data.query('CONCEPT_ID == {}'.format(src))
                for ont in ont_list:
                    ev = row_data[ont + '_MAPPING'].values.tolist()[0]\
                        if row_data[ont + '_MAPPING'].values.tolist()[0] != 'Unmapped'\
                        else row_data[ont + '_URI'].values.tolist()[0]
                    evidence += [ont + ':' + ev]
        else:
            evidence = main_data.query('CONCEPT_ID == {}'.format(concept))['CONCEPT_NAME'].values.tolist()[0]
        error_analysis_org[db_type][concept]['evidence'] = evidence

    return error_analysis_org
