#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Analytic Utility Functions.

Clinical Data Manipulation and Result Formatting
* reconfigures_dataframe
* process_clinical_data
* process_results
* output_coverage_set_counts
* process_error_analysis_data

Ontology Data Manipulation and Result Formatting
* outputs_ontology_metadata

Process Mapping Results
* process_mapping_evidence
* splits_concept_levels

Statistical Testing
* get_asterisks_for_pvalues
* chisq_and_posthoc_corrected
* min_max_scaler
* gets_group_stats

Plotting Functions
* change_width

"""

# import needed libraries
import numpy as np  # type: ignore
import pandas as pd  # type: ignore

from itertools import combinations  # type: ignore
from scipy.stats import chi2_contingency  # type: ignore
from sklearn import preprocessing
from statsmodels.sandbox.stats.multicomp import multipletests  # type: ignore
from typing import Dict, List, Optional



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
        if len(conc_type) > 0:
            conc_type_uri = [x for x in conc_type if x.upper().endswith('URI')][0]
            concept = data[all_cols + conc_type].dropna(subset=conc_type, how='all').drop_duplicates()
            concept_ont_codes = [i for j in [x.split(' | ') for x in list(concept[conc_type_uri])] for i in j]
        else:
            concept, concept_ont_codes = None, None

        anc_type = [x for x in data.columns if anc_string.upper() in x.upper() and type_col.upper() in x.upper()]
        if len(anc_type) > 0:
            anc_type_uri = [x for x in anc_type if x.upper().endswith('URI')][0]
            ancestor = data[all_cols + anc_type].dropna(subset=anc_type, how='all').drop_duplicates()
            ancestor_ont_codes = [i for j in [x.split(' | ') for x in list(ancestor[anc_type_uri])] for i in j]
        else: ancestor, ancestor_ont_codes = None, None
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
    """Method takes a Pandas data frame assumed to have data that will be sued for mapping and a string representing
    a column in that DataFrame that can be used to group the data. The function then groups the data and outputs

    Args:
        data: A Pandas DataFrame that contains OMOP data.
        grp_var: A string representing a column to group by.

    Return:
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
        results[grp]['concept_src_code'] = [x for y in grp_data['CONCEPT_SOURCE_CODE'].astype(str) for x in y.split(' | ')]
        if 'CONCEPT_SOURCE_LABEL' in grp_data.columns:
            results[grp]['concept_src_label'] = [x for y in grp_data['CONCEPT_SOURCE_LABEL'].astype(str) for x in y.split(' | ')]
        else: results[grp]['concept_src_label'] = [x for y in grp_data['CONCEPT_LABEL'].astype(str) for x in y.split(' | ')]
        results[grp]['concept_synonym'] = [x for y in grp_data['CONCEPT_SYNONYM'].astype(str) for x in y.split(' | ')]
        results[grp]['concept_vocab'] = ', '.join(set([x for y in grp_data['CONCEPT_VOCAB'].astype(str) for x in y.split(' | ')]))
        # get ancestor data
        results[grp]['anc_concept_id'] = [x for y in grp_data['ANCESTOR_CONCEPT_ID'].astype(str) for x in y.split(' | ')]
        results[grp]['anc_src_code'] = [x for y in grp_data['ANCESTOR_SOURCE_CODE'].astype(str) for x in y.split(' | ')]
        results[grp]['anc_label'] = [x for y in grp_data['ANCESTOR_LABEL'].astype(str) for x in y.split(' | ')]
        results[grp]['anc_vocab'] = ', '.join(set([x for y in grp_data['ANCESTOR_VOCAB'].astype(str) for x in y.split(' | ')]))

    return results


def min_max_scaler(scores):
    scaled_scores = []
    for i in scores:
        x = np.asarray(i).reshape(-1, 1)
        scaler = preprocessing.MinMaxScaler()
        x_scaled = scaler.fit_transform(x)
        scaled_list = x_scaled.flatten().tolist()
        scaled_scores += [scaled_list]

    return scaled_scores


def process_results(df, col_type, col_list):
    if 'Concept Used In Practice' in set(df['CONCEPT_TYPE']):
        df_grp = df.groupby('CONCEPT_TYPE')
        df_grp_prac = df_grp.get_group('Concept Used In Practice').drop_duplicates()
        df_grp_stnd = df_grp.get_group('Standard Concept Not Used In Practice').drop_duplicates()
    else:
        df_grp = df.groupby('CONCEPT_TYPE')
        df_grp_prac = df_grp.get_group('CHCO Concept Used In Practice').drop_duplicates()
        df_grp_stnd = df_grp.get_group('LOINC2HPO Concept').drop_duplicates()

    # concepts used in practice
    df_prac_concept_data, df_prac_ancestor_data = splits_concept_levels(df_grp_prac, col_type, col_list)

    # standard concepts
    df_stnd_concept_data, df_stnd_ancestor_data = splits_concept_levels(df_grp_stnd, col_type, col_list)

    results = [df_prac_concept_data, df_prac_ancestor_data, df_stnd_concept_data, df_stnd_ancestor_data]

    return df_grp_prac, df_grp_stnd, results


def process_mapping_evidence(evidence_list):
    evidence_dict = {'all': [], 'dbxref': [], 'synonym': [], 'label': [], 'similarity': []}

    for x in evidence_list:
        for i in x.split(' | '):
            if 'synonym' in i.lower():
                evidence_dict['synonym'] += [i.split(':')[-1]]
                evidence_dict['all'] += [i.split(':')[-1]]
            if 'dbxref' in i.lower():
                evidence_dict['dbxref'] += [i.split(':')[-1]]
                evidence_dict['all'] += [i.split(':')[-1]]
            if 'label' in i.lower():
                evidence_dict['label'] += [i.split(':')[-1]]
                evidence_dict['all'] += [i.split(':')[-1]]
            if 'similarity' in i.lower():
                evidence_dict['similarity'] += [float(i.split(':')[-1].split('_')[-1])]
                evidence_dict['all'] += [i.split(':')[0] + ':' + '_'.join(i.split(':')[-1].split('_')[:-1])]

    return evidence_dict


def output_coverage_set_counts(cp_data, chco_data, sets):
    set_counts = {'overlap': None, 'cp_only': None, 'omop2obo_only': None}
    overlap, cp_only, o2o_only = sets

    # overlap
    #     set_counts['overlap'] = chco_data[chco_data['CONCEPT_ID'].isin(overlap)][[
    #     'CONCEPT_COUNT_ADJUSTED']].dropna().values.flatten().tolist()
    set_counts['overlap'] = cp_data[cp_data['CONCEPT_ID'].isin(overlap)][['RECORD_COUNT']].values.flatten().tolist()

    # cp only
    set_counts['cp_only'] = cp_data[cp_data['CONCEPT_ID'].isin(cp_only)][['RECORD_COUNT']].values.flatten().tolist()

    # o2o only
    set_counts['omop2obo_only'] = chco_data[chco_data['CONCEPT_ID'].isin(o2o_only)][
        ['CONCEPT_COUNT_ADJUSTED']].dropna().values.flatten().tolist()

    return set_counts


def process_error_analysis_data(error_analysis, purposefully_unmapped, missing_concepts, cp_data, chco_data):
    set_counts = {'cdm_version': None, 'purposefully_excluded': None, 'missing': None}

    # covered by error analysis
    new_cdm_df = cp_data.merge(error_analysis, left_on='CONCEPT_ID', right_on='TARGET_CONCEPT_ID', how='inner')
    new_cdm = new_cdm_df[new_cdm_df['CONCEPT_ID'].isin(missing_concepts)]
    new_cdm_concepts = set(new_cdm['CONCEPT_ID'])
    set_counts['cdm_version'] = {
        'concepts': new_cdm,
        'counts': new_cdm[['RECORD_COUNT']].values.flatten().tolist()
    }
    new_cdm_concepts = set(new_cdm['CONCEPT_ID'])

    # covered by excluded mapping concepts (anything not mapped that's not None)
    updated_missing_concepts = missing_concepts - new_cdm_concepts
    excluded_df = cp_data[cp_data['CONCEPT_ID'].isin(list(purposefully_unmapped['CONCEPT_ID']))]
    excluded = excluded_df[excluded_df['CONCEPT_ID'].isin(updated_missing_concepts)]
    excluded = excluded.merge(chco_data, on='CONCEPT_ID', how='inner')

    excluded_concepts = set(excluded['CONCEPT_ID'])
    set_counts['purposefully_excluded'] = {
        'concepts': excluded,
        'counts': excluded[['RECORD_COUNT']].values.flatten().tolist()
    }

    # remaining concepts not accounted for concepts
    final_missing_concepts = missing_concepts - (new_cdm_concepts | excluded_concepts)
    set_counts['missing'] = {
        'concepts': cp_data[cp_data['CONCEPT_ID'].isin(final_missing_concepts)],
        'counts': cp_data[cp_data['CONCEPT_ID'].isin(final_missing_concepts)][
            ['RECORD_COUNT']].values.flatten().tolist()
    }

    return set_counts


def gets_group_stats(cp_data, chco_data, grouper, primary_key):
    coverage_dict = dict()
    dbs_db = cp_data.groupby(grouper)
    db_list = set(cp_data[grouper])

    for x in db_list:
        x_db_df = dbs_db.get_group(x)
        covered = x_db_df[x_db_df[primary_key].isin(chco_data[primary_key])]
        missing = x_db_df[~x_db_df[primary_key].isin(chco_data[primary_key])]
        coverage_dict[x] = {'overlap': dict(zip(list(covered[primary_key]), list(covered['RECORD_COUNT']))),
                            'primary_only': dict(zip(list(missing[primary_key]), list(missing['RECORD_COUNT'])))
                            }

    return coverage_dict


def change_width(ax, new_value) :
    for patch in ax.patches :
        current_width = patch.get_width()
        diff = current_width - new_value

        # we change the bar width
        patch.set_width(new_value)

        # we recenter the bar
        patch.set_x(patch.get_x() + diff * .5)
