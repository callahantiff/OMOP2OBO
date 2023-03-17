#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import glob
import pandas as pd

from tqdm import tqdm
from typing import Optional, Union
from omop2obo.utils import *


class OMOPDataProcessor(object):
    """Class is designed to process and prepare specific OMOP CDM tables needed to support mapping. This class assumes
    that at minimum, there is a directory of OMOP CDM data files (i.e., concept.csv, concept_synonym.csv, vocabulary.csv,
    concept_relationship.csv, and concept_ancestor.csv) stored in the resources/clinical_data directory. Similar to the
    processes performed on the UMLS data by the UMLSDataProcessor class, this class processes the clinical data to
    create a Pandas DataFrame. Also note that columns are added to the OMOP data in order to directly align it to the
    UMLS data.

    Raises:
        IndexError:
            If omop_data directory is empty.
        FileNotFoundError:
            If the concept.csv file is not in the resources/umls_data directory.
            If the concept_synonym.csv file is not in the resources/umls_data directory.
            If the vocabulary.csv file is not in the resources/umls_data directory.
            If the concept_relationship.csv file is not in the resources/umls_data directory.
            If the concept_ancestor.csv file is not in the resources/umls_data directory.
    """

    def __init__(self) -> None:
        self.omop_data_files: list = glob.glob('resources/clinical_data/vocabulary_*/*.csv', recursive=True)
        self.omop_merged: Optional[pd.DataFrame] = None

        # check umls data directory for needed mapping files
        if len(self.omop_data_files) == 0: raise IndexError('The "resources/clinical_data" directory is empty')
        else:
            if len(self.omop_data_files) == 0:
                raise FileNotFoundError('concept.csv missing from "resources/clinical_data/"')
            else:
                self.concept: Union[str, pd.DataFrame] = [x for x in self.omop_data_files if 'CONCEPT.csv' in x][0]
            if len(self.omop_data_files) == 0:
                raise FileNotFoundError('concept_synonym.csv missing from "resources/clinical_data/"')
            else:
                self.concept_synonym: Union[str, pd.DataFrame] = [x for x in self.omop_data_files if 'SYNONYM' in x][0]
            if len(self.omop_data_files) == 0:
                raise FileNotFoundError('vocabulary.csv missing from "resources/clinical_data/"')
            else:
                self.vocabulary: Union[str, pd.DataFrame] = [x for x in self.omop_data_files if 'VOCABULARY' in x][0]
            if len(self.omop_data_files) == 0:
                raise FileNotFoundError('concept_relationship.csv missing from "resources/clinical_data/"')
            else:
                self.concept_rel: Union[str, pd.DataFrame] = [x for x in self.omop_data_files if 'RELATIONSHIP' in x][0]
            if len(self.omop_data_files) == 0:
                raise FileNotFoundError('concept_ancestor.csv missing from "resources/clinical_data/"')
            else:
                self.concept_anc: Union[str, pd.DataFrame] = [x for x in self.omop_data_files if 'ANCESTOR' in x][0]


    def _processes_concept(self) -> None:
        """Function reads in and processes data in the CONCEPT.csv file. The data are filtered and output as a Pandas
        DataFrame. An example row from the output DataFrame is shown below.
            concept_id                    40341563
            STRING                   Solvent S - Z
            SAB                             SNOMED
            CODE                         259275000
            STRING_TYPE               concept_name
            SEMANTIC_TYPE    Observation_Substance

        Returns:
            None
        """

        print('\t- Creating DataFrame and Processing Data')
        cols = [0, 1, 2, 3, 4, 5, 6, 9]
        self.concept = pd.read_csv(self.concept, sep='\t', usecols=cols, header=0, low_memory=False)
        self.concept = self.concept.drop_duplicates().fillna('None').astype(str)
        self.concept = self.concept[self.concept['invalid_reason'] == 'None'].drop(['invalid_reason'], axis=1)
        self.concept = self.concept.drop_duplicates()
        var_dict = {'concept_name': 'STRING', 'concept_code': 'CODE', 'vocabulary_id': 'SAB'}
        self.concept.rename(columns=var_dict, inplace=True)
        # add missing context columns
        self.concept['STRING_TYPE'] = 'concept_name'
        self.concept['SEMANTIC_TYPE'] = self.concept['domain_id'] + '_' + self.concept['concept_class_id']
        # drop unneeded columns
        concepts_org = self.concept.copy()
        self.omop_merge = concepts_org.drop(['domain_id', 'concept_class_id', 'standard_concept'], axis=1)
        # remove "no matching concept"
        self.omop_merge = self.omop_merge[~self.omop_merge['concept_id'].isin(['0', '1'])]
        self.omop_merge = self.omop_merge.fillna('None').drop_duplicates()

        return None

    def _processes_concept_synonym(self) -> None:
        """Function reads in and processes data in the CONCEPT_SYNONYM.csv file. The data are filtered and output as a
        Pandas DataFrame. An example row from the output DataFrame is shown below.
            concept_id                                   40341563
            STRING           Solvent S - Z (navigational concept)
            SAB                                            SNOMED
            CODE                                        259275000
            STRING_TYPE                                   synonym
            SEMANTIC_TYPE                   Observation_Substance

        Returns:
            None
        """

        print('\t- Creating DataFrame and Processing Data')
        self.concept_synonym = pd.read_csv(self.concept_synonym, sep='\t', header=0, low_memory=False)
        self.concept_synonym = self.concept_synonym[self.concept_synonym.language_concept_id == 4180186]
        self.concept_synonym = self.concept_synonym.drop_duplicates().fillna('None').astype(str)
        self.concept_synonym = self.concept_synonym[['concept_id', 'concept_synonym_name']].drop_duplicates()
        self.concept_synonym.rename(columns={'concept_synonym_name': 'STRING'}, inplace=True)
        self.concept_synonym['STRING_TYPE'] = 'synonym'
        # merge synonyms with full dataset
        merge_cols = ['concept_id', 'STRING', 'STRING_TYPE']
        o_merged = self.omop_merge.merge(self.concept_synonym, on=merge_cols, how='outer')
        # fill NA values by concept_id
        omop_out = o_merged.set_index('concept_id').combine_first(self.omop_merge.set_index('concept_id'))
        self.omop_merge = omop_out[omop_out.index.isin(o_merged.concept_id)].reset_index()
        self.omop_merge = self.omop_merge.fillna('None').drop_duplicates()

        return None

    def _processes_vocabulary(self) -> None:
        """Function reads in and processes data in the VOCABULARY.csv file. The data are filtered and output as a Pandas
        DataFrame. An example row from the output DataFrame is shown below.
            concept_id                                                 1001704
            STRING           Coagulation factor VIII inhibitor [Units/volum...
            SAB                                                          LOINC
            CODE                                                       93450-5
            STRING_TYPE                                           concept_name
            SEMANTIC_TYPE                                 Measurement_Lab Test
            SAB_NAME           Logical Observation Identifiers Names and Codes
                               (Regenstrief Institute) (2.69)

        Returns:
            None
        """

        print('\t- Creating DataFrame and Processing Data')
        self.vocabulary = pd.read_csv(self.vocabulary, sep='\t', header=0, usecols=[0, 1, 2, 3], low_memory=False)
        self.vocabulary = self.vocabulary.drop_duplicates().fillna('None').astype(str)
        self.vocabulary.rename(columns={'vocabulary_id': 'SAB'}, inplace=True)
        self.omop_merge = self.omop_merge.merge(self.vocabulary, on='SAB', how='left').fillna('None')
        sab_names = self.omop_merge['vocabulary_name'] + ' (' + self.omop_merge['vocabulary_version'] + ')'
        self.omop_merge['SAB_NAME'] = sab_names
        # drop unneeded columns
        drop_cols = ['vocabulary_name', 'vocabulary_reference', 'vocabulary_version']
        self.omop_merge = self.omop_merge.drop(drop_cols, axis=1).astype(str).fillna('None').drop_duplicates()

        return None

    def _processes_concept_relationship(self) -> None:
        """Function reads in and processes data in the CONCEPT_RELATIONSHIP.csv file. The data are filtered and output
        as a Pandas DataFrame. An example row from the output DataFrame is shown below.
            concept_id                                                       19008339
            DBXREF_concept_id                                                 1104874
            relationship_id                                               Mapped from
            STRING                                                          vitamin A
            SAB                                                                RxNorm
            CODE                                                                11246
            STRING_TYPE                                                  concept_name
            SEMANTIC_TYPE                                             Drug_Ingredient
            SAB_NAME                                   RxNorm (NLM) (RxNorm 20210802)
            DBXREF_STRING           NOVAFERRUM MULTIVITAMIN WITH IRON PEDIATRIC DR...
            DBXREF_SAB                                                            NDC
            DBXREF_CODE                                                   52304071650
            DBXREF_STRING_TYPE                                           concept_name
            DBXREF_SEMANTIC_TYPE                                    Drug_11-digit NDC
            DBXREF_SAB_NAME         National Drug Code (FDA and manufacturers) (ND...

        Returns:
            None
        """

        print('\t- Creating DataFrame and Processing Data')
        self.concept_rel = pd.read_csv(self.concept_rel, sep='\t', header=0, usecols=[0, 1, 2], low_memory=False)
        self.concept_rel = self.concept_rel.drop_duplicates().fillna('None').astype(str)
        keep_rels = ['Concept same_as from', 'Concept replaced by', 'Concept alt_to from', 'Concept alt_to to',
                     'Concept poss_eq from', 'Concept poss_eq to', 'Concept replaced by', 'Concept replaces',
                     'Concept same_as to', 'Mapped from', 'Maps to']
        self.concept_rel = self.concept_rel[self.concept_rel['relationship_id'].isin(keep_rels)].drop_duplicates()
        self.concept_rel = self.concept_rel[self.concept_rel['concept_id_1'] != self.concept_rel['concept_id_2']]
        self.concept_rel = self.concept_rel.astype(str)
        # merge relationships with concept_id_1 (primary concepts)
        primary = self.concept_rel.merge(self.omop_merge, left_on='concept_id_1', right_on='concept_id', how='left')
        primary = primary.drop(['concept_id'], axis=1).fillna('None').drop_duplicates()
        # secondary_concepts -- concept_id_2
        secondary = self.concept_rel.merge(self.omop_merge, left_on='concept_id_2', right_on='concept_id', how='left')
        secondary = secondary.drop(['concept_id'], axis=1).fillna('None').drop_duplicates()
        ren = {'CODE': 'DBXREF_CODE', 'STRING': 'DBXREF_STRING', 'SAB': 'DBXREF_SAB', 'SAB_NAME': 'DBXREF_SAB_NAME',
               'STRING_TYPE': 'DBXREF_STRING_TYPE', 'SEMANTIC_TYPE': 'DBXREF_SEMANTIC_TYPE'}
        secondary.rename(columns=ren, inplace=True)
        # add everything back together
        merge_cols = list(set(primary).intersection(set(secondary.columns)))
        self.omop_merge = primary.merge(secondary, on=merge_cols, how='left')
        self.omop_merge.rename(columns={'concept_id_1': 'concept_id', 'concept_id_2': 'DBXREF_concept_id'}, inplace=True)
        # add back concepts without any relationships
        sub = self.omop_merge[~self.omop_merge['concept_id'].isin(self.omop_merge['concept_id'])]
        self.omop_merge = pd.concat([self.omop_merge, sub]).fillna('None').drop_duplicates()

        return None

    def _processes_concept_ancestor(self) -> None:
        """Function reads in and processes data in the CONCEPT_ANSCESTOR.csv file. The data are filtered and output as a
        Pandas DataFrame. The resulting Pandas DataFrame is then processed into a dictionary to make it easier to
        identify a concept's ancestors. Example output is shown below.
            {'35619487': {
                    '0': {'35619484', '37209200'},
                    '1': {'37209201', '35626947'},
                    '2': {'4169265'},
                    '3': {'4126705'}}
            }

        for each concept_id's ancestor dictionary, the keys are string-ints representing location in hierarchy where '0'
        is the immediate parent node of the AUI listed as the primary key. The largest number in the list is the root
        node.

        Returns:
            None.
        """

        print('\t- Creating DataFrame and Processing Data')
        self.concept_anc = pd.read_csv(self.concept_anc, sep='\t', header=0, usecols=[0, 1, 2], low_memory=False)
        self.concept_anc = self.concept_anc.drop_duplicates().fillna('None').astype(str)
        # filter data to only include relevant concepts and remove concepts listed as their own ancestor
        concs = list(set(self.omop_merge['concept_id']))
        self.concept_anc = self.concept_anc[self.concept_anc['descendant_concept_id'].isin(concs)]
        self.concept_anc = self.concept_anc[self.concept_anc['min_levels_of_separation'] != '0'].drop_duplicates()
        # sort data and create reset min_levels_of_separation to start from 0 and sort data
        adj_sep_level = self.concept_anc['min_levels_of_separation'].apply(lambda i: str(int(i) - 1))
        self.concept_anc['min_levels_of_separation'] = adj_sep_level
        # create a new variable that combines the min_levels_of_separation and ancestor_concept_id columns
        new_var = self.concept_anc['min_levels_of_separation'] + ':' + self.concept_anc['ancestor_concept_id']
        self.concept_anc['ancestor_position'] = new_var
        # aggregate combined ancestor information by descendant concept
        print('\t- Aggregating Ancestors by Concept (this process takes several minutes)')
        anc_agg = aggregates_column_values(self.concept_anc, 'descendant_concept_id', ['ancestor_position'], '|')
        print('\t- Converting Ancestor Hierarchy DataFrame to Dictionary (this process takes several minutes)')
        concept_hier_map = dict()
        for idx, row in tqdm(anc_agg.iterrows(), total=anc_agg.shape[0]):
            path_dict = {}
            for y in sorted(row['ancestor_position'].split('|')):
                k, v = y.split(':')
                if k in path_dict.keys(): path_dict[k].add(v)
                else: path_dict[k] = {v}
            concept_hier_map[row['descendant_concept_id']] = path_dict
        self.concept_anc = concept_hier_map

        return None

    def _tidy_and_filter(self) -> None:
        """Function performs the final steps needed to tidy the data, adding metadata (i.e., omop domain and standard
        concept indicator), and reformat labels. An example row of the final output is shown below.
            concept_id                                                          19014160
            DBXREF_concept_id                                                   42857709
            relationship_id                                                  Mapped from
            STRING                               nalmefene 0.1 mg/ml injectable solution
            SAB                                                                   RxNorm
            CODE                                                                  314133
            STRING_TYPE                                                     concept_name
            SEMANTIC_TYPE                                             Drug_Clinical Drug
            SAB_NAME                                      RxNorm (NLM) (RxNorm 20210802)
            DBXREF_STRING                            nalmefene hcl 100mcg/ml inj,amp,1ml
            DBXREF_SAB                                                        VA Product
            DBXREF_CODE                                                      N0000160670
            DBXREF_STRING_TYPE                                              concept_name
            DBXREF_SEMANTIC_TYPE                                         Drug_VA Product
            DBXREF_SAB_NAME            VA National Drug File Product (VA) (RXNORM 201...
            domain_id                                                               Drug
            concept_class_id                                               Clinical Drug
            standard_concept                                                           S
            DBXREF_domain_id                                                        Drug
            DBXREF_concept_class_id                                           VA Product
            DBXREF_standard_concept                                                 None

        Returns:
            None.
        """

        # get domain id concept standard and concept class
        concepts = self.concept[['concept_id', 'domain_id', 'concept_class_id', 'standard_concept']]
        self.omop_merge = self.omop_merge.merge(concepts, on='concept_id', how='left')
        self.omop_merge = self.omop_merge.fillna('None').drop_duplicates()
        # add for dbxref terms
        var_dict = {'concept_id': 'DBXREF_concept_id', 'standard_concept': 'DBXREF_standard_concept',
                    'domain_id': 'DBXREF_domain_id', 'concept_class_id': 'DBXREF_concept_class_id'}
        concepts.rename(columns=var_dict, inplace=True)
        self.omop_merge = self.omop_merge.merge(concepts, on='DBXREF_concept_id', how='left')
        self.omop_merge = self.omop_merge.fillna('None').drop_duplicates()
        self.omop_merge['STRING'] = self.omop_merge['STRING'].str.lower()
        self.omop_merge['DBXREF_STRING'] = self.omop_merge['DBXREF_STRING'].str.lower()

        return None

    def data_processor(self) -> dict:
        """Function operates as a main function that processes several OMOP CDM data tables. Two data structures are
        created and output as a single data structure. The first object is a dictionary which is keyed by UMLS AUI (see
        the _processes_concept_ancestor function for more detail). The second object is a Pandas DataFrame that contains
        the remaining OMOP CDM tables merged into a single object (see the tidy_and_filter function for more detail).
        These two objects are pickled to: resources/clinical_data/OMOP_MAP_PANEL.pkl (self.omop_merge) and
        resources/clinical_data/OMOP_MAP_Ancestor_Dictionary.pkl (self.concept_anc). These two objects are returned as a
        dictionary using the following keys: {'omop_full': omop_merged, 'concept_ancestors': concept_anc}.

        Returns:
            None.
        """

        # process umls data
        print('\n' + '===' * 15 + '\nPROCESSING OMOP CDM DATA\n' + '===' * 15)
        print('--> Processing CONCEPT.csv')
        self._processes_concept()
        print('--> Processing CONCEPT_SYNONYM.csv')
        self._processes_concept_synonym()
        print('--> Processing VOCABULARY.csv')
        self._processes_vocabulary()
        print('--> Processing CONCEPT_RELATIONSHIP.csv')
        self._processes_concept_relationship()
        print('--> Processing CONCEPT_ANCESTOR.csv')
        self._processes_concept_ancestor()

        # clean up final data set
        self._tidy_and_filter()

        # write data to disc --  defensive way to write pickle.write, allowing for very large files on all platforms
        print('--> Saving OMOP Mapping Data')
        filepath = 'resources/clinical_data/'
        print('\t- Writing Pandas DataFrame containing processed OMOP concepts')
        pickle_large_data_structure(self.omop_merge, filepath + 'OMOP_MAP_PANEL.pkl')
        print('\t- Writing OMOP concept ancestor dictionary')
        pickle_large_data_structure(self.concept_anc, filepath + 'OMOP_MAP_Ancestor_Dictionary.pkl')

        # combine objects into single dictionary
        omop_data_dict = {'umls_full': self.omop_merge, 'aui_ancestors': self.concept_anc}

        return omop_data_dict
