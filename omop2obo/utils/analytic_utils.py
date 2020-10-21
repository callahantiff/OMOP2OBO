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

from itertools import combinations  # type: ignore
from scipy.stats import chi2_contingency  # type: ignore
from statsmodels.sandbox.stats.multicomp import multipletests  # type: ignore
from typing import Dict, List


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

    return reconfigured_data


def splits_concept_levels(data: pd.DataFrame, type_col: str) -> List:
    """Takes a Pandas DataFrame and a string containing a keyword and with the keyword, splits the input DataFrame
    into concept and ancestor-level data. The keyword is used to obtain relevant columns where the data differs for
    concepts and ancestors.

    Args:
        data: A Pandas DataFrame containing stacked mapping results.
        type_col: A string containing the data type to parse (e.g. "DBXREF" or "STRING").

    Returns:
        A list of tuples, each tuple contains a Pandas DataFrame and a list, the first contains a subset of the
            original data to a specific set of columns and the list contains all ontology concepts that were
            annotated to the OMOP concepts contained in the Pandas DataFrame. The first tuple contains data at the
            concept level and the second tuple contains data at the ancestor level.
    """

    # extract relevant columns
    all_cols = [x for x in data.columns if type_col not in x]
    conc_type = [x for x in data.columns if 'CONCEPT' in x.upper() and type_col.upper() in x.upper()]
    conc_type_uri = [x for x in conc_type if x.upper().endswith('URI')][0]
    anc_type = [x for x in data.columns if 'ANCESTOR' in x.upper() and type_col.upper() in x.upper()]
    anc_type_uri = [x for x in anc_type if x.upper().endswith('URI')][0]

    # extract concept codes from ancestor codes
    concept = data[all_cols + conc_type].dropna(subset=conc_type, how='all').drop_duplicates()
    ancestor = data[all_cols + anc_type].dropna(subset=anc_type, how='all').drop_duplicates()

    # get counts of ontology concepts at each concept level
    concept_ont_codes = [i for j in [x.split(' | ') for x in list(concept[conc_type_uri])] for i in j]
    ancestor_ont_codes = [i for j in [x.split(' | ') for x in list(ancestor[anc_type_uri])] for i in j]

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
