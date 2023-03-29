#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import glob
import os
import pandas as pd  # type: ignore
import pickle


from datetime import date, datetime
from tqdm import tqdm  # type: ignore
from typing import Optional, Tuple

from omop2obo.utils import *


class ConceptMapper(object):
    """Class generates mappings between OBO foundry class identifiers and and concepts within the UMLS Metathesaurus and
    OMOP.

    For additional detail see: https://github.com/callahantiff/OMOP2OBO/wiki/V2.0----beta

    TODO:
        - Need to add tests
        - Need to add logic that enables mappings to be created OBO --> OMOP and OMOP --> OBO. Right now, they are only
          generated OBO --> OMOP. If users what OMOP --> OBO mappings they need to use the V1.0 release.

    Attributes:
        filter_vocabs: A list of source vocabulary aliases to use them only wanting to map to certain vocabularies.
        id_list: A set containing 1 or more OBO class identifiers to map.
        obo_df: A Pandas DataFrame containing processed OBO data.
        obo_dict: A dictionary keyed by "ancestor" and "children" containing class ancestor and children information.
        ont_alias: A string containing the alis for a specific ontology.
        omop_df: A Pandas DataFrame containing processed OMOP data.
        omop_dict: A dictionary of OMOP concept ancestor information where the keys are string-ints representing
            location in hierarchy where '0' is the immediate parent node of the concept listed as the primary key. The
            largest number in the list is the root node.
        sab_matches: A dictionary keyed by vocabulary abbreviation with results stored in the dictionary key.
        source_code: A dictionary where keys represent data source strings and values contain a primary string to use
            for normalizing the sources.
        umls_df: A Pandas DataFrame containing processed UMLS data.
        umls_dict: A dictionary of UMLS concept ancestor information where the keys are string-ints representing
            location in hierarchy where '0' is the immediate parent node of the AUI listed as the primary key. The
            largest number in the list is the root node.
        write_loc: A string containing the directory where all mapping output will be written to.

    Raises:
        IndexError:
            If umls_data directory is empty.
            If clinical_data directory is empty.
            If ontologies directory is empty.
        FileNotFoundError:
            If the UMLS_MAP_PANEL.pkl file is not in the resources/umls_data directory.
            If the UMLS_MAP_Ancestor_Dictionary.pkl file is not in the resources/umls_data directory.
            If the OMOP_MAP_PANEL.pkl file is not in the resources/clinical_data directory.
            If the OMOP_MAP_Ancestor_Dictionary.pkl file is not in the resources/clinical_data directory.
            If the processed_obo_data_dictionary.pkl file is not in the resources/ontologies directory.
    """

    def __init__(self, ontology_alias: Optional[str] = None, id_list: Optional[set] = None,
                 filter_vocabs: Optional[list] = None) -> None:

        umls_dir = glob.glob('resources/umls_data/*.pkl')
        omop_dir = glob.glob('resources/clinical_data/*.pkl')
        obo_dir = glob.glob('resources/ontologies/*data_dictionary.pkl')
        self.source_code: str = 'releases/v1.0/collaborations/AllofUs/resources/source_vocabularies_v2.csv'
        self.source_code_map: Optional[dict] = None
        self.ont_alias: str = ontology_alias
        self.filter_vocabs: list = filter_vocabs
        self.write_loc: Optional[str] = None
        self.sab_matches: Optional[dict] = None

        # read in umls data
        d1 = "resources/umls_data/"
        if len(umls_dir) == 0: raise IndexError('The "resources/umls_data" directory is empty')
        else:
            umls_df = [x for x in umls_dir if 'UMLS_MAP_PANEL' in x]
            if len(umls_df) == 0: raise FileNotFoundError('UMLS_MAP_PANEL.pkl missing from ' + d1)
            else: self.umls_df: pd.DataFrame = read_pickled_large_data_structure(umls_df[0])
            umls_dict = [x for x in umls_dir if 'UMLS_MAP_Ancestor_Dictionary' in x]
            if len(umls_dict) == 0: raise FileNotFoundError('UMLS_MAP_Ancestor_Dictionary.pkl missing from + dir')
            else: self.umls_dict: dict = read_pickled_large_data_structure(umls_dict[0])
        # read in omop data
        d2 = "resources/clinical_data"
        if len(omop_dir) == 0: raise IndexError('The "resources/clinical_data" directory is empty')
        else:
            omop_df = [x for x in omop_dir if 'OMOP_MAP_PANEL' in x]
            if len(omop_df) == 0: raise FileNotFoundError('OMOP_MAP_PANEL.pkl missing from ' + d2)
            else: self.omop_df: pd.DataFrame = read_pickled_large_data_structure(omop_df[0])
            omop_dict = [x for x in umls_dir if 'OMOP_MAP_Ancestor_Dictionary' in x]
            if len(omop_dict) == 0: raise FileNotFoundError('OMOP_MAP_Ancestor_Dictionary.pkl missing from ' + d2)
            else: self.omop_dict: dict = read_pickled_large_data_structure(omop_dict[0])
        # read in obo data
        d3 = "resources/ontologies/"
        if len(obo_dir) == 0: raise FileNotFoundError('processed_obo_data_dictionary.pkl missing from ' + d3)
        else: obo_dict = read_pickled_large_data_structure(obo_dir[0])
        temp_dict = obo_dict[self.ont_alias]
        self.obo_df: pd.DataFrame = temp_dict['df']
        self.obo_dict: dict = {'ancestors': temp_dict['ancestors'], 'children': temp_dict['children']}
        self.id_list: set = set(self.obo_df['CODE']) if id_list is None else id_list


    def _create_output_directory(self) -> None:
        """Function creates a directory called "29MAR2023_MAPPINGS" in resources/mappings/ and writes all mapping data
        there.

        Return:
             None.
        """

        date_today = datetime.strftime(datetime.strptime(str(date.today()), '%Y-%m-%d'), '%d%b%Y').upper() + '_MAPPINGS'
        self.write_loc = 'resources/mappings/' + date_today + '/'

        if not os.path.exists(self.write_loc):
            os.makedirs(self.write_loc)

        return None


    def _normalize_abbreviations(self) -> None:
        """Function reads in the normalized source code dictionary and normalizes the aliases of the sources providing
        data in the UMLS, OMOP, and OBO data sets.

        Return:
            None.
        """

        self.source_code_map = dict()
        with open(self.source_code, 'r') as f:
            for x in f.read().splitlines()[1:]:
                secondary_idx, primary_idx = x.split(',')[2], x.split(',')[1]
                if secondary_idx != '' and primary_idx != '': self.source_code_map[secondary_idx] = primary_idx

        # normalize source concept aliases
        self.obo_df = normalizes_source_codes(
            self.source_code_map, self.obo_df, [['CODE', 'OBO_SAB'], ['DBXREF', 'OBO_DBXREF_SAB']])
        self.umls_df = normalizes_source_codes(
            self.source_code_map, self.umls_df, [['CODE', 'UMLS_SAB'], ['DBXREF', 'UMLS_DBXREF_SAB']])
        self.omop_df = normalizes_source_codes(
            self.source_code_map, self.omop_df.copy(),  [['CODE', 'SAB'], ['DBXREF_CODE', 'DBXREF_SAB']])

        return None


    def _filter_data_for_specific_sources(self, filter_terms: list) -> pd.DataFrame:
        """Function applies filtering logic to reduce the dataset to only contains information for specific
        vocabularies.

        Return:
            filtered_df: A Pandas DataFrame that has been filtered to only contain certain terminologies.
        """

        cols = ['UMLS_SAB', 'UMLS_DBXREF_SAB']
        umls_filt = normalizes_source_terminologies(self.source_code_map, self.umls_df, cols)
        umls_filtered = umls_filt[
            (umls_filt['UMLS_SAB_TEMP'].isin(filter_terms)) | (umls_filt['UMLS_DBXREF_SAB_TEMP'].isin(filter_terms))]
        filtered_df = umls_filtered.copy()

        return filtered_df


    def _generating_initial_mappings(self, umls_df: pd.DataFrame, obo_df: pd.DataFrame) -> Tuple:
        """Function performs the initial mapping stage creating mappings of three types: (1) looking for exact matches
        to OBO concept identifiers in the UMLS data; (2) looking for exact matches between OBO concepts cross-references
        and UMLS concepts; and (3) looking for exact matches between OBO concept labels and synonyms and concepts labels
        and synonyms in the UMLS data.

        Args:
            umls_df: A Pandas DataFrame containing the filtered UMLS data.
            obo_df:  A Pandas DataFrame containing the subset of the OBO data that needs to be mapped.

        Returns:
            A tuple containing the three Pandas DataFrames, each with the results from a different part of the mapping
            process.
        """

        # merge and match on codes
        print('\t- Identifying Exact Matches to Ontology Identifiers')
        cols1 = ['OBO_ontology_id', 'CODE', 'OBO_SAB', 'OBO_SAB_NAME', 'OBO_SEMANTIC_TYPE']
        cols2 = ['UMLS_CUI', 'UMLS_AUI', 'CODE']
        meta = ['CODE', ['OBO', None], ['UMLS', None]]
        test_code = merges_dataframes('EXACT CODE', obo_df.copy(), cols1, umls_df.copy(), cols2, meta)
        test_code.to_csv(self.write_loc + '/temp_code_output.csv', index=False, sep='\t')
        # merge and match on dbxrefs
        print('\t- Identifying Exact Matches to Database Cross-References')
        cols1 = ['OBO_ontology_id', 'DBXREF', 'OBO_DBXREF_TYPE', 'OBO_DBXREF_SAB_NAME', 'OBO_SEMANTIC_TYPE',
                 'OBO_DBXREF_SAB']
        cols2 = ['UMLS_CUI', 'UMLS_AUI', 'DBXREF']
        meta = ['DBXREF', ['OBO', 'OBO_DBXREF_TYPE'], ['UMLS', 'UMLS_DBXREF_TYPE']]
        test_dbx = merges_dataframes('EXACT DBXREF', obo_df.copy(), cols1, umls_df.copy(), cols2, meta)
        test_dbx.to_csv(self.write_loc + '/temp_dbx_output.csv', index=False, sep='\t')
        # merge and match on strings
        print('\t- Identifying Exact Matches to Concept Labels and Synonyms')
        cols1 = ['OBO_ontology_id', 'STRING', 'OBO_STRING_TYPE', 'OBO_SEMANTIC_TYPE', 'OBO_SAB', 'OBO_SAB_NAME']
        cols2 = ['UMLS_CUI', 'UMLS_AUI', 'STRING']
        meta = ['STRING', ['OBO', 'OBO_STRING_TYPE'], ['UMLS', 'UMLS_STRING_TYPE']]
        test_str = merges_dataframes('EXACT STRING', obo_df.copy(), cols1, umls_df.copy(), cols2, meta)
        test_str.to_csv(self.write_loc + '/temp_str_output.csv', index=False, sep='\t')

        return test_code, test_dbx, test_str


    def _result_formatter(self, match_df: pd.DataFrame, match_df_kids: pd.DataFrame, fuzzy_match_dict: dict,
                          match_df_anc: pd.DataFrame, omop_code_concept_dict: dict, obo_version: str, obo_dict: dict,
                          c_matches: int, anc_matches: int, kid_matches: int, fuzzy_matches: int) -> None:
        """Function formats mapping results after searching for additional mappings to ancestor and children concepts.

        Args:
            match_df: A Pandas DataFrame containing the results of the results of processing the mappings.
            match_df_kids: A Pandas DataFrame containing the results of the results of identifying exact child mappings.
            fuzzy_match_dict: A Pandas DataFrame containing the results of the results of identifying fuzzy child mappings.
            match_df_anc: A Pandas DataFrame containing the results of the results of identifying ancestor mappings.
            omop_code_concept_dict: A dictionary containing mappings between the OMOP concepts and source codes.
            obo_version: A string containing version information for the OBO ontology.
            obo_dict: A nested dictionary of OBO concept ancestors and children for each ontology class.
            c_matches: An integer representing the count of mapped concepts.
            anc_matches: An integer representing the count of mapped concepts with an ancestor mapping.
            kid_matches: An integer representing the count of mapped concepts with an exact child mapping.
            fuzzy_matches: An integer representing the count of mapped concepts with a fuzzy child mapping.

        Returns:
             None.
        """

        print('\t- Formatting Concept Mapping Results')
        master_matches = {}; primary_key_col = 'OBO_ontology_id'; no_map = []; no_children = []
        concept_match_set = set(match_df[primary_key_col])
        for ont_id in tqdm(self.id_list):
            ont_id = ont_id if 'htt' in ont_id else 'http://purl.obolibrary.org/obo/' + ont_id.replace(':', '_').upper()
            matches = {}; idx_matches = []
            if ont_id in concept_match_set:
                idx_matches += [[match_df[match_df[primary_key_col] == ont_id], 'concept']]
                if match_df_kids is not None and ont_id in match_df_kids.keys():
                    idx_matches += [[match_df_kids[ont_id], 'child']]
                elif fuzzy_match_dict is not None and ont_id in fuzzy_match_dict.keys():
                    idx_matches += [[fuzzy_match_dict[ont_id], 'child - fuzzy string']]
                else: no_children.append(ont_id)
            elif match_df_anc is not None and ont_id in match_df_anc.keys():
                idx_matches += [[match_df_anc[ont_id], 'ancestor']]
            else: no_map.append(ont_id); idx_matches = None
            if idx_matches is not None:
                for result_df, c_level in idx_matches:
                    for idx, row in result_df.iterrows():
                        if row['CODE'] != 'None' and row['CODE'] in omop_code_concept_dict.keys():
                            omop_concept_id = omop_code_concept_dict[row['CODE']]; hit = row['CODE']
                        elif row['DBXREF'] != 'None' and row['DBXREF'] in omop_code_concept_dict.keys():
                            omop_concept_id = omop_code_concept_dict[row['DBXREF']]; hit = row['DBXREF']
                        else: omop_concept_id = None; hit = None
                        if omop_concept_id is not None and hit is not None:
                            res_dict = {'MATCH': {row['MATCH']}, 'MATCH_TYPE': {row['MATCH_TYPE']}}
                            if hit in matches.keys():
                                if omop_concept_id in matches[hit].keys():
                                    if c_level in matches[hit][omop_concept_id].keys():
                                        matches[hit][omop_concept_id][c_level]['MATCH'] |= res_dict['MATCH']
                                        matches[hit][omop_concept_id][c_level]['MATCH_TYPE'] |= res_dict['MATCH_TYPE']
                                    else: matches[hit][omop_concept_id][c_level] = res_dict
                                else: matches[hit][omop_concept_id] = {c_level: res_dict}
                            else: matches[hit] = {omop_concept_id: {c_level: res_dict}}
            if len(matches) > 0:
                master_matches[ont_id] = {'ont_label': obo_dict[ont_id], 'ont_version': obo_version, 'mappings': matches}
        # descriptions
        s = '{}: {} concept matches, {} ancestor matches, {} concept-children matches, {} fuzzy matches - {} NO MATCHES'
        s = s.format(self.ont_alias, c_matches, anc_matches, kid_matches, fuzzy_matches, len(set(no_map)))
        print('\t\t- ' + s)
        # update dictionary
        r = {'processed_mappings': master_matches, 'no_mappings': no_map, 'no_child_mappings': no_children, 'stats': s}
        self.sab_matches['|'.join(self.ont_alias)] = r

        return None


    def _hierarchy_search(self, filter_terms: list, obo_umls_merged_df: pd.DataFrame, keys: list,
                          obo_df_temp: pd.DataFrame, umls_df_temp: pd.DataFrame, column_keys: list,
                          filtered_df: pd.DataFrame, fuzzy_children: bool, obo_version: str,
                          omop_code_concept_dict: dict, obo_dict: dict) -> None:
        """Function performs additional searches for concepts where no exact match could be found. For concepts where
        no exact match was found, the OBO hierarchy is searched. For all matched concepts, additional searches are
        performed with the goal of providing additional mapping precision for concepts that are broad. For example, when
        the concept is something like "cancer of the lung" this search would return all relevant OBO concepts that are
        a type of cancer in the lung.

        Args:
            filter_terms: A list of source vocabulary aliases.
            obo_umls_merged_df: A Pandas DataFrame containing the results of exact mapping.
            keys: A list of columns to include in final Pandas DataFrame.
            obo_df_temp: A version of the OBO Pandas DataFrame where the source vocabularies have been normalized.
            umls_df_temp:  A version of the OBO Pandas DataFrame where the source vocabularies have been normalized.
            column_keys: A list of columns to use when performing the hierarchical search.
            filtered_df: A Pandas DataFrame that has been filtered to only contain certain terminologies.
            fuzzy_children: A bool variable used to indicate whether fuzzy child mappings should be returned.
            obo_version: A string containing version information for the OBO ontology.
            omop_code_concept_dict: A dictionary containing mappings between the OMOP concepts and source codes.
            obo_dict: A nested dictionary of OBO concept ancestors and children for each ontology class.

        Returns:
            None.
        """

        for sab in tqdm(filter_terms):
            no_match_df_anc, match_df_anc, match_df_no_kids, match_df_kids, fuzzy_match_dict = [None] * 5
            print('\t- Determining Mapping Level for Processed Results in {} Vocabulary(ies)'.format(sab))
            cols = ['UMLS_SAB', 'UMLS_DBXREF_SAB', 'OBO_SAB', 'OBO_DBXREF_SAB']
            merged_df = normalizes_source_terminologies(self.source_code_map, obo_umls_merged_df, cols)
            no_match_df, match_df = processes_input_concept_mappings([self.ont_alias], self.id_list, merged_df, keys)
            c_matches = len(set(match_df['OBO_ontology_id']))
            if len(no_match_df) > 0:
                print('\t- Searching for Ancestor Matches in the {} Vocabulary(ies)'.format(sab))
                anc_dfs = [no_match_df.copy(), obo_df_temp.copy(), umls_df_temp.copy(), self.obo_df]
                no_match_df_anc, match_df_anc = finds_entity_mappings(
                    'Ancestor', self.obo_dict['ancestors'], column_keys, anc_dfs, [self.ont_alias])
                anc_matches = len(set(match_df_anc.keys())) if match_df_anc is not None else 0
            else: anc_matches = 0
            if len(match_df) > 0:
                print('\t- Searching for Children Matches')
                kid_dfs = [match_df.copy(), obo_df_temp.copy(), umls_df_temp.copy(), self.obo_df]
                match_df_no_kids, match_df_kids = finds_entity_mappings(
                    'Child', self.obo_dict['children'], column_keys, kid_dfs, [self.ont_alias])
                kid_matches = len(set(match_df_kids.keys())) if match_df_kids is not None else 0
            else: kid_matches = 0
            if len(match_df) > 0 and fuzzy_children is not None:
                print('\t- Searching for Fuzzy Matches')
                fuzzy_dfs = [match_df_no_kids.copy(), filtered_df.drop_duplicates().copy()]
                keys = ['OBO_ontology_id', 'UMLS_AUI', 'UMLS_CUI', 'UMLS_SAB_TEMP', 'UMLS_DBXREF_SAB_TEMP']
                fuzzy_match_dict = finds_entity_fuzzy_matches(
                    'UMLS', fuzzy_dfs, keys, [self.ont_alias], ['OBO_SAB', obo_version])
                fuzzy_matches = len(set(fuzzy_match_dict.keys())) if fuzzy_match_dict is not None else 0
            else: fuzzy_matches = 0

            self._result_formatter(match_df, match_df_kids, fuzzy_match_dict, match_df_anc, omop_code_concept_dict,
                                   obo_version, obo_dict, c_matches, anc_matches, kid_matches, fuzzy_matches)

        return None


    def generate_exact_mappings(self) -> None:

        # original workflow can be found here: "releases/v1.0/collaborations/AllofUs/scratch_o2o_v2.py"

        print('\n' + '===' * 15 + '\nGENERATING MAPPINGS\n' + '===' * 15)
        self._create_output_directory()
        print('--> Mappings Output Location: {}'.format(self.write_loc))


        # STEP 1: Normalize Data Source Abbreviations
        print('--> STEP 1: Normalizing Source Abbreviations')
        self._normalize_abbreviations()
        # filter obo_df to only contains concepts that need to be mapped
        df = self.obo_df[self.obo_df['CODE'].isin(self.id_list)].drop_duplicates()


        # STEP 2: Filter OBO, OMOP, and UMLS Data to Only Contain Vocabularies of Interest
        print('--> STEP 2: Filtering UMLS and OMOP Data to Contain Concepts for Specific Vocabularies')
        filt = list(set(v for v in self.source_code_map.values())) if self.filter_vocabs is None else self.filter_vocabs
        filtered_df = self._filter_data_for_specific_sources(filt)


        ### STEP 3: Merge Unfiltered OBO Data with Filtered UMLS Data
        print('--> STEP 3: Generating Mappings')
        test_code, test_dbx, test_str = self._generating_initial_mappings(filtered_df, df)
        # merging the mapping results
        merge_cols = list(set(test_code.columns).intersection(set(test_dbx.columns)))
        merged1 = test_code.merge(test_dbx, on=merge_cols, how='outer').fillna('None').drop_duplicates()
        # codes + dbxrefs + strings
        merge_cols = list(set(merged1.columns).intersection(set(test_str.columns)))
        merged2 = merged1.merge(test_str, on=merge_cols, how='outer').fillna('None').drop_duplicates()
        obo_umls_merged_df = merged2.copy()


        #### STEP 4: Look for Ancestor and Children Matches for Concepts Not Matched in Prior Step
        print('--> STEP 4: Searching Vocabulary Hierarchies for Concepts Not Matched in Prior Step')
        # convert OMOP data to dictionary
        omop_code_concept_dict = dict(zip(self.omop_df['CODE'], self.omop_df['concept_id']))
        # ontology dictionary
        obo_df_cut = self.obo_df[self.obo_df['OBO_STRING_TYPE'] == 'class label'].drop_duplicates()
        obo_dict = dict(zip(obo_df_cut['OBO_ontology_id'], obo_df_cut['STRING']))
        # search for mappings
        filter_terms = filt; fuzzy_children = True; obo_version = list(set(self.obo_df['OBO_SAB']))[0]
        obo_df_temp = normalizes_source_terminologies(self.source_code_map, self.obo_df, ['OBO_DBXREF_SAB'])
        umls_df_temp = normalizes_source_terminologies(self.source_code_map, filtered_df, ['UMLS_SAB', 'UMLS_DBXREF_SAB'])
        column_keys = ['OBO_ontology_id', 'OBO_DBXREF_SAB_TEMP', 'UMLS_CUI', 'UMLS_SAB_TEMP', 'UMLS_DBXREF_SAB_TEMP']
        keys = ['OBO_ontology_id', 'UMLS_CUI', 'UMLS_SAB_TEMP', 'UMLS_DBXREF_SAB_TEMP', 'OBO_SAB_TEMP', 'OBO_DBXREF_SAB_TEMP']
        self._hierarchy_search(filter_terms, obo_umls_merged_df, keys, obo_df_temp, umls_df_temp, column_keys,
                               filtered_df, fuzzy_children, obo_version, omop_code_concept_dict, obo_dict)
        # write the full set of results
        pickle.dump(self.sab_matches, open(self.write_loc + '/temp_allJoined_sab_ancestors_dict.pkl', 'wb'))


        #### STEP 5: Finalize Mapping Output
        print('--> STEP 5: Finalize Mappings and Generate Output by Clinical Source Vocabulary')
        for keys in list(self.sab_matches.keys()):
            print('\t- Processing: {}'.format(str(keys)))
            data = []; children_data = []; mapping_dict = self.sab_matches[keys]['processed_mappings']
            subset = ['concept_id', 'STRING', 'SAB', 'CODE_ORG', 'domain_id', 'concept_class_id', 'standard_concept']
            omop_sub = self.omop_df[subset]
            for k, v in tqdm(mapping_dict.items()):
                ont_id = k; ont_label = v['ont_label']; ont_version = v['ont_version']; mappings = v['mappings']
                for code in mappings.keys():
                    for omop_id in mappings[code].keys():
                        for level, res in mappings[code][omop_id].items():
                            match = ' | '.join(res['MATCH']); match_type = ' | '.join(res['MATCH_TYPE'])
                            res_cols = [code, omop_id, ont_id, ont_label, ont_version, level, match, match_type]
                            if 'child' in level: children_data += [res_cols]
                            else: data += [res_cols]
            ## convert to data frame
            # concept-level data
            map_df_c = pd.DataFrame({'concept_id': [x[1] for x in data], 'ontology_id': [x[2] for x in data],
                                     'ontology_label': [x[3] for x in data], 'ontology_version': [x[4] for x in data],
                                     'map_level': [x[5] for x in data], 'map_type': [x[6] for x in data],
                                     'map_evidence': [x[7] for x in data]})
            # add omop data
            map_df_c = map_df_c.merge(omop_sub, on=['concept_id'], how='left').drop_duplicates()
            map_df_c.rename(
                columns={'STRING': 'concept_name', 'SAB': 'vocabulary_id', 'CODE_ORG': 'concept_code'}, inplace=True)
            # reorder columns
            ordered_cols = ['ontology_id', 'ontology_label', 'ontology_version', 'concept_id', 'concept_code',
                            'concept_name', 'concept_class_id', 'vocabulary_id', 'domain_id', 'standard_concept',
                            'map_level', 'map_type', 'map_evidence']
            map_df_c = map_df_c[ordered_cols]
            # refine filtering for parents
            map_df_c = map_df_c[map_df_c['vocabulary_id'].isin([x.upper() for x in keys.split('|')])].drop_duplicates()
            map_df_c = map_df_c[map_df_c['concept_id'] != 'None'].drop_duplicates()
            # concept-level data children
            if len(children_data) > 0:
                map_df_k = pd.DataFrame(
                    {'concept_id': [x[1] for x in children_data], 'ontology_id': [x[2] for x in children_data],
                     'ontology_label': [x[3] for x in children_data], 'ontology_version': [x[4] for x in children_data],
                     'map_level': [x[5] for x in children_data], 'map_type': [x[6] for x in children_data],
                     'map_evidence': [x[7] for x in children_data]})
                omop_sub_child = omop_sub.copy()
                omop_sub_child.rename(columns={
                    'STRING': 'concept_name', 'SAB': 'vocabulary_id', 'CODE_ORG': 'concept_code'}, inplace=True)
                map_df_k = map_df_k.merge(omop_sub_child, on=['concept_id'], how='left')
            else: map_df_k = None
            # reorder columns
            ordered_cols = ['ontology_id', 'ontology_label', 'ontology_version', 'concept_id', 'concept_code',
                            'concept_name', 'concept_class_id', 'vocabulary_id', 'domain_id', 'standard_concept',
                            'map_level', 'map_type', 'map_evidence']
            map_df_k = map_df_k[ordered_cols]
            # refine filtering for parents and children
            vocab_keys = [x.upper() for x in keys.split('|')]
            map_df_k = map_df_k[map_df_k['vocabulary_id'].isin(vocab_keys)].drop_duplicates()
            map_df_k = map_df_k[map_df_k['concept_id'] != 'None'].drop_duplicates()
            # write data
            map_df_c['map_evidence'] = map_df_c['map_evidence'].str.replace('\n\n', '\n')
            o = len(set(map_df_c['ontology_id'])); c = len(map_df_c['concept_id'])
            print('\t-Concept Mappings: {} ontology concepts mapped to {} OMOP concepts'.format(str(o), str(c)))
            print(map_df_c.groupby(['map_level'])['ontology_id'].count())
            f_src = self.write_loc + '/omop2obo_{}_mappings_v2beta.tsv'.format(keys)
            map_df_c.to_csv(f_src, header=True, index=False, sep='\t')
            if map_df_k is not None:  # concept children data
                map_df_k['map_evidence'] = map_df_k['map_evidence'].str.replace('\n\n', '\n')
                o = len(set(map_df_k['ontology_id'])); c = len(map_df_k['concept_id'])
                print('\t- Child Mappings: {} ontology concepts mapped to {} OMOP concepts'.format(str(o), str(c)))
                print(map_df_k.groupby(['map_level'])['ontology_id'].count())
                f_src = self.write_loc + '/omop2obo_{}_children_mappings_v2beta.tsv'.format(keys)
                map_df_k.to_csv(f_src, header=True, index=False, sep='\t')
