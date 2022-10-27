#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import needed libraries
import json
import os
import pandas as pd
import re
import requests
import shutil
import urllib3

from datetime import datetime, timezone
from tqdm import tqdm
from typing import Dict

# handle warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def url_download(url: str, write_location: str, filename: str) -> None:
    """Downloads a file from a URL and saves it locally.
    Args:
        url: A string that points to the location of a temp mapping file that needs to be processed.
        write_location: A string that points to a file directory.
        filename: A string containing a filepath for where to write data to.
    Returns:
        None.
    """

    print('Downloading Data from {}'.format(url))

    r = requests.get(url, allow_redirects=True, verify=False)
    with open(write_location + '{filename}'.format(filename=filename), 'wb') as outfile:
        try: outfile.write(r.content)
        except OSError:
            block_size = 1000000000
            for i in range(0, len(r.content), block_size):
                outfile.write(r.content[i:i + block_size])
    outfile.close()

    return None


def creates_mapping_dictionary(data: pd.DataFrame) -> Dict:
    """Function takes a Pandas DataFrame, extracts information needed to generate Atlas-formatted JSON files and
    outputs this information as a nested dictionary.

    Args:
        data: A Pandas DataFrame object containing OMOP2OBO mappings.

    Returns:
        omop2obo_map: a nested dictionary keyed by concept_id which contains all of the information needed to
            generate Atlas-formatted concept sets.
    """
    omop2obo_map = dict()
    for idx, row in tqdm(data.iterrows(), total=data.shape[0]):
        omop_id = row['CONCEPT_ID']; concept_name = row['CONCEPT_NAME']; concept_code = row['CONCEPT_CODE']
        concept_vocab = row['CONCEPT_VOCAB']; map_type = row['MAPPING_CATEGORY']; map_evidence = row['MAPPING_EVIDENCE']
        map_logic = row['ONTOLOGY_LOGIC']; ont_id = row['ONTOLOGY_URI'].lower().replace(' ', '')
        ont_label = row['ONTOLOGY_LABEL']
        filename = '{}-{}.json'.format(omop_id,
                                       concept_name.lower().replace(' | ', '|').replace('/', '-').replace(' ', '_'))

        # add to dictionary
        omop2obo_map[omop_id] = {omop_id: {
                'CONCEPT_ID': omop_id, 'CONCEPT_NAME': concept_name, 'CONCEPT_CODE': concept_code,
                'VOCABULARY_ID': concept_vocab, 'MAP_CATEGORY': map_type, 'MAP_EVIDENCE': map_evidence, 'MAP_LOGIC':
                map_logic, 'ONTOLOGY_URI': ont_id, 'ONTOLOGY_LABEL': ont_label},
            'filename': filename}

    return omop2obo_map


def omop_concept_set_exp(concept_id: int, dict_entry: Dict, desc: bool = False) -> dict:
    """Method creates a dictionary containing an OMOP concept set expression.

    Template Source: http://atlas-covid19.ohdsi.org/

    Args:
        concept_id: An integer containing an OMOP concept_id (e.g. 254761).
        dict_entry: A dictionary containing the mapping information for a specific OMOP concept id.
        desc: A boolean value indicating whether or not the descendants of the concept should be included.

    Returns:
        exp: A dictionary containing an OMOP concept set expression.
    """

    # determine mapping membership
    exp = {'concept': {
            'CONCEPT_ID': concept_id,
            'CONCEPT_NAME': dict_entry[concept_id]['CONCEPT_NAME'].title(),
            'STANDARD_CONCEPT': None,
            'STANDARD_CONCEPT_CAPTION': None,
            'CONCEPT_CODE': int(dict_entry[concept_id]['CONCEPT_CODE']),
            'DOMAIN_ID': None,
            'VOCABULARY_ID': dict_entry[concept_id]['VOCABULARY_ID'],
        },
        'isExcluded': False,
        'includeDescendants': desc,
        'includeMapped': True,

        'ONTOLOGY_CONCEPT_MAPPING_MEMBERS': {
            'identifiers': dict_entry[concept_id]['ONTOLOGY_URI'],
            'labels': dict_entry[concept_id]['ONTOLOGY_LABEL']
                                             },
        'ONTOLOGY_CONCEPT_MAPPING_LOGIC': dict_entry[concept_id]['MAP_LOGIC'],
        'MAPPING_CATEGORY': dict_entry[concept_id]['MAP_CATEGORY'],
        'MAPPING_EVIDENCE': dict_entry[concept_id]['MAP_EVIDENCE']
    }

    return exp


def writes_atlas_json_files(mappings: Dict, output_location: str) -> None:
    """Function takes a dictionary of OMOP2OBO mappings, converts each one to an Atlas-formatted object and writes
    the object as json file to the location specific by the output_location variable. The file name is a formatted
    string containing the OMOP concept id and label (e.g., '22274-neoplasm_of_uncertain_behavior_of_larynx.json').

    Args:
        mappings: A nested dictionary keyed by concept_id which contains all of the information needed to
            generate Atlas-formatted concept sets.
        output_location: A string containing a location to write data to.

    Returns:
        None.
    """

    if not os.path.exists(output_location): os.mkdir(output_location)

    for key, value in tqdm(mappings.items()):
        atlas_dict = {'items': omop_concept_set_exp(int(key), value, False)}

        # write out json file
        with open(output_location + value['filename'], 'w') as outfile:
            json.dump(atlas_dict, outfile, indent=4)
        outfile.close()

    return None


def creates_concept_set_container(map_dict: Dict, output_loc: str, enclave_params: Dict) -> None:
    """Takes input information on the OMOP2OBO mappings and outputs a csv file with the columns required for creating
    the concept set container data.

    Args:
        map_dict: A dictionary keyed by ontology_id that contains data needed to create csv files.
        output_loc: A string containing information on where to write the data and a filename.
        enclave_params: A dictionary keyed by concepts required for creating Enclave CSV files.

    Returns:
        None.
    """

    # process data
    container_set_data = []
    for k, v in tqdm(map_dict.items()):
        intention_parts = []; status = enclave_params['status']; stage = enclave_params['stage']
        concept_set_id = '[OMOP2OBO] {}'.format(v['filename'].split('.')[0])
        concept_set_name = '[OMOP2OBO] {}'.format(v['filename'].split('.')[0])
        assigned_informatician = enclave_params['assigned_informatician']
        assigned_sme = enclave_params['assigned_sme']; project_id = enclave_params['project_id']
        n3c_reviewer = enclave_params['n3c_reviewer']; created_at = enclave_params['created_at']
        ids = v[k]['ONTOLOGY_URI'].lower().replace(' | ', '|')
        labels = v[k]['ONTOLOGY_LABEL'].lower().replace('/', '-').replace(' | ', '|').replace(' ', '_')
        alias = '{}-{}'.format(ids, labels)
        archived = enclave_params['archived']; created_by = enclave_params['created_by']

        # format evidence
        for x in v.items():
            if x[0] != 'filename':
                intention = enclave_params['intention'].format(
                    x[1]['CONCEPT_ID'], x[1]['MAP_CATEGORY'], x[1]['MAP_EVIDENCE'])
                intention_parts.append(intention)
        intention_form = enclave_params['intention_header'] + '\n'.join(intention_parts)

        container_set_data += [[concept_set_id, concept_set_name, intention_form, assigned_informatician, assigned_sme,
                                project_id, status, stage, n3c_reviewer, alias, archived, created_by, created_at]]

    # convert data to pandas DataFrame
    concept_set_container = pd.DataFrame({'concept_set_id': [x[0] for x in container_set_data],
                                          'concept_set_name': [x[1] for x in container_set_data],
                                          'intention': [x[2] for x in container_set_data],
                                          'assigned_informatician': [x[3] for x in container_set_data],
                                          'assigned_sme': [x[4] for x in container_set_data],
                                          'project_id': [x[5] for x in container_set_data],
                                          'status': [x[6] for x in container_set_data],
                                          'stage': [x[7] for x in container_set_data],
                                          'n3c_reviewer': [x[8] for x in container_set_data],
                                          'alias': [x[9] for x in container_set_data],
                                          'archived': [x[10] for x in container_set_data],
                                          'created_by': [x[11] for x in container_set_data],
                                          'created_at': [x[12] for x in container_set_data]})

    concept_set_container.to_csv(output_loc, header=True, index=False, sep=',')

    return None


def creates_concept_set_version(map_dict: Dict, id_dict: Dict, output_loc: str, enclave_params: Dict) -> None:
    """Takes input information on the OMOP2OBO mappings and outputs a csv file with the columns required for creating
    the concept set version data.

    Args:
        map_dict: A dictionary keyed by ontology_id that contains data needed to create csv files.
        id_dict: A dictionary keyed by ontology with values that contain enclave codeset_ids.
        output_loc: A string containing information on where to write the data.
        enclave_params: A dictionary keyed by concepts required for creating Enclave CSV files.

    Returns:
        None.
    """

    container_set_data = []
    for k, v in tqdm(map_dict.items()):
        intention_parts = []; codeset_id = id_dict[k]; issues = None; has_review = None; reviewed_by = None
        concept_set_id = '[OMOP2OBO] {}'.format(v['filename'].split('.')[0])
        concept_set_version_title = '[OMOP2OBO] {} (v{})'.format(v['filename'].split('.')[0], enclave_params['version'])
        project = enclave_params['project_id']; source_application = 'OMOP2OBO'
        source_application_version = enclave_params['source_application_version']
        created_at = enclave_params['created_at']; atlas_json = None; update_message = enclave_params['update_message']
        most_recent_version = enclave_params['is_most_recent_version']
        comments = 'Exported from OMOP2OBO and bulk imported to N3C.'
        limitations = 'The OMOP concepts in this set may be mapped at different levels of confidence, please see the ' \
                      'Intention field associated with this concept set for additional informations. '
        status = enclave_params['status']; created_by = enclave_params['created_by']
        provenance = 'This mapping was created using the OMOP2OBO mapping algorithm (' \
                     'https://github.com/callahantiff/OMOP2OBO) V1.0.0. The mappings are governed by the OMOP to OBO ' \
                     'N3C Domain Team (https://covid.cd2h.org/ontology). '
        atlas_json_resource_url = None; parent_version_id = None; is_draft = 'TRUE'

        # format evidence
        for x in v.items():
            if x[0] != 'filename':
                intention = enclave_params['intention'].format(
                    x[1]['CONCEPT_ID'], x[1]['MAP_CATEGORY'], x[1]['MAP_EVIDENCE'])
                intention_parts.append(intention)
        intention_form = enclave_params['intention_header'] + '\n'.join(intention_parts)
        container_set_data += [[codeset_id, concept_set_id, concept_set_version_title, project, source_application,
                                source_application_version, created_at, atlas_json, most_recent_version, comments,
                                intention_form, limitations, issues, update_message, status, has_review, reviewed_by,
                                created_by, provenance, atlas_json_resource_url, parent_version_id, is_draft]]

    # convert data to pandas DataFrame
    concept_set_version = pd.DataFrame({'codeset_id': [x[0] for x in container_set_data],
                                        'concept_set_id': [x[1] for x in container_set_data],
                                        'concept_set_version_title': [x[2] for x in container_set_data],
                                        'project': [x[3] for x in container_set_data],
                                        'source_application': [x[4] for x in container_set_data],
                                        'source_application_version': [x[5] for x in container_set_data],
                                        'created_at': [x[6] for x in container_set_data],
                                        'atlas_json': [x[7] for x in container_set_data],
                                        'most_recent_version': [x[8] for x in container_set_data],
                                        'comments': [x[9] for x in container_set_data],
                                        'intention': [x[10] for x in container_set_data],
                                        'limitations': [x[11] for x in container_set_data],
                                        'issues': [x[12] for x in container_set_data],
                                        'update_message': [x[13] for x in container_set_data],
                                        'status': [x[14] for x in container_set_data],
                                        'has_review': [x[15] for x in container_set_data],
                                        'reviewed_by': [x[16] for x in container_set_data],
                                        'created_by': [x[17] for x in container_set_data],
                                        'provenance': [x[18] for x in container_set_data],
                                        'atlas_json_resource_url': [x[19] for x in container_set_data],
                                        'parent_version_id': [x[20] for x in container_set_data],
                                        'is_draft': [x[21] for x in container_set_data]})

    concept_set_version.to_csv(output_loc, header=True, index=False, sep=',')

    return None


def creates_concept_set_expression_items(map_dict: Dict, id_dict: Dict, output_loc: str, enclave_params: Dict) -> None:
    """Takes input information on the OMOP2OBO mappings and outputs a csv file with the columns required for creating
    the concept set expression items data.

    Args:
        map_dict: A dictionary keyed by ontology_id that contains data needed to create csv files.
        id_dict: A dictionary keyed by ontology with values that contain enclave codeset_ids.
        output_loc: A string containing information on where to write the data.
        enclave_params: A dictionary keyed by concepts required for creating Enclave CSV files.

    Returns:
        None.
    """

    container_set_data = []
    for k, v in tqdm(map_dict.items()):
        codeset_id = id_dict[k]
        for x in v.items():
            if x[0] != 'filename':
                concept_id = x[1]['CONCEPT_ID']; code = x[1]['CONCEPT_CODE']; code_system = x[1]['VOCABULARY_ID']
                is_excluded = 'FALSE'; include_descendants = 'FALSE'; include_mapped = 'TRUE'
                item_id = None; annotation = 'Exported from OMOP2OBO and bulk imported to N3C'
                created_by = enclave_params['created_by']; created_at = enclave_params['created_at']
                ont_id = v[k]['ONTOLOGY_URI']; ont_label = v[k]['ONTOLOGY_LABEL']; map_category = v[k]['MAP_CATEGORY']
                map_logic = v[k]['MAP_LOGIC']; map_evidence = v[k]['MAP_EVIDENCE']

                container_set_data += [[codeset_id, concept_id, code, code_system, ont_id, ont_label,
                                        map_category, map_logic, map_evidence, is_excluded, include_descendants,
                                        include_mapped, item_id, annotation, created_by, created_at]]

    # convert data to pandas DataFrame
    concept_set_items = pd.DataFrame({'codeset_id': [x[0] for x in container_set_data],
                                      'concept_id': [x[1] for x in container_set_data],
                                      'code': [x[2] for x in container_set_data],
                                      'codeSystem': [x[3] for x in container_set_data],
                                      'ontology_id': [x[4] for x in container_set_data],
                                      'ontology_label': [x[5] for x in container_set_data],
                                      'mapping_category': [x[6] for x in container_set_data],
                                      'mapping_logic': [x[7] for x in container_set_data],
                                      'mapping_evidence': [x[8] for x in container_set_data],
                                      'isExcluded': [x[9] for x in container_set_data],
                                      'includeDescendants': [x[10] for x in container_set_data],
                                      'includeMapped': [x[11] for x in container_set_data],
                                      'item_id': [x[12] for x in container_set_data],
                                      'annotation': [x[13] for x in container_set_data],
                                      'created_by': [x[14] for x in container_set_data],
                                      'created_at': [x[15] for x in container_set_data]})

    concept_set_items.to_csv(output_loc, header=True, index=False, sep=',')

    return None


def main():

    ### Step 0: set/update hard-coded variables
    # update hard-coded attributes
    version = 'v2.0.0'
    main_dir = 'releases/v1.0/collaborations/N3C OMOP2OBO Working Group/'
    write_loc = main_dir + 'enclave_codeset_builder/omop2obo_concept_set_csvs/v2.0.0/'
    id_dict = main_dir + 'enclave_codeset_builder/omop2obo_concept_set_csvs/omop2obo_enclave_codeset_id_dict.json'
    version_id = write_loc + 'omop2obo_enclave_codeset_id_dict_{}.json'.format(str(version))
    json_files = write_loc + 'atlas_json_files_{}/'.format(version)
    zenodo_mappings = [
        'https://zenodo.org/record/7250177/files/OMOP2OBO_V1.5_Condition_Occurrence_Mapping_Oct2020.xlsx?download=1'
    ]

    # enclave parameters
    enclave_id = 'c91cf525-aa2e-4ad8-b6d0-f83122ee48b5'
    n3c_project_id = 'RP-453C03'
    enclave_parameters = {
        'assigned_informatician': enclave_id, 'assigned_sme': enclave_id, 'project_id':  n3c_project_id,
        'status': 'Under Construction', 'stage': 'Awaiting Editing', 'n3c_reviewer': enclave_id, 'archived': 'FALSE',
        'created_by': enclave_id, 'created_at': datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + 'Z',
        'source_application_version': version, 'is_most_recent_version': 'TRUE', 'version': 2,
        'update_message': 'Version 2',
        'intention_header': 'Mixed - This mapping was created using the OMOP2OBO mapping algorithm (' +
                            'https://github.com/callahantiff/OMOP2OBO).\nThe Mapping Category and Evidence ' +
                            'supporting the mappings are provided below, by OMOP concept:\n',
        'intention': '\n{}\n*******\nMapping Category: {'
                     '}\n------------------------------------------------\nMapping Provenance\n------------------\n{}'
    }

    ### Step 1: download mappings from Zenodo
    # download omop2obo mappings from zenodo -- verify link is latest version: https://github.com/callahantiff/OMOP2OBO
    print('***STEP 1:*** Download OMOP2OBO Mappings')
    for url in zenodo_mappings:
        file_name = re.sub(r'\?.*', '', url.split('/')[-1])
        if not os.path.exists(write_loc + file_name): url_download(url, write_loc, file_name)
        # read in the mapping data
        print('\t - Reading in mapping data from OMOP2OBO')
        map_data = pd.read_excel(write_loc + file_name, sep=',', header=0, sheet_name="OMOP2OBO_HPO_Mapping_Results")
        map_filtered = map_data.fillna('None')
        map_filtered = map_filtered[map_filtered['MAPPING_CATEGORY'] != 'Unmapped']

        ### Step 2: convert mappings to dictionary
        print('***STEP 2:*** Converting OMOP2OBO Mapping Dataframe into Dictionary')
        omop2obo_map = creates_mapping_dictionary(map_filtered)

        ### Step 3: write Atlas-formatted concept expression sets
        print('***STEP 3:*** Writing Atlas-formatted Json Files to: {}'.format(json_files))
        writes_atlas_json_files(omop2obo_map, json_files)
        # zip directory containing json files and delete original
        shutil.make_archive(json_files, 'zip', write_loc)
        shutil.rmtree(json_files)

        ### Step 4: create n3c enclave data files
        # reading in an existing file
        if os.path.exists(id_dict):
            codeset_ids = json.load(open(id_dict, 'r'))
        else:
            codeset_ids = dict(); starting_id = 900000000
            for k in tqdm(omop2obo_map.keys()):
                codeset_ids[k] = starting_id; starting_id += 1
            json.dump(codeset_ids, open(id_dict, 'w')); json.dump(codeset_ids, open(version_id, 'w'))  # versioned dir

        #### STEP 3: create
        print('***STEP 4:*** Creating N3C-formatted Enclave Files')
        print('\t - Generating Concept Set Container File')
        output_loc = write_loc + 'OMOP2OBO_{}_N3C_Enclave_CSV_concept_set_container.csv'.format(version)
        creates_concept_set_container(omop2obo_map, output_loc, enclave_parameters)

        print('\t - Generating Concept Set Version File')
        output_loc = write_loc + 'OMOP2OBO_{}_N3C_Enclave_CSV_concept_set_version.csv'.format(version)
        creates_concept_set_version(omop2obo_map, codeset_ids, output_loc, enclave_parameters)

        print('\t - Generating Concept Set Expression File')
        output_loc = write_loc + 'OMOP2OBO_{}_N3C_Enclave_CSV_concept_set_expression_items.csv'.format(version)
        creates_concept_set_expression_items(omop2obo_map, codeset_ids, output_loc, enclave_parameters)


if __name__ == '__main__':
    main()
