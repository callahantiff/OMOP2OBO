
## Open Biological and Biomedical Ontologies Foundry Data  

**Purpose:** This directory stores OBO Foundry data downloaded from the `resources/ontology_source_list.txt` file. It
also stores these data after they have been modified using the functionality in the scripts listed below.

**Primary Scripts:**  
- `omop2obo/ontology_downloader.py`  
- `omop2obo/ontology_explorer.py`

**Input Data**  
- `resources/ontology_source_list.txt`

**Output Data:**  
- `resources/ontologies/ontology_source_metadata.txt`
- `resources/ontologies/processed_obo_data_dictionary.pkl`

 
<br>

### Required UMLS Data  
The `omop2obo` functionality is designed to download all OBO Foundry ontologies that are listed in the
`resources/ontology_source_list.txt`. An example of what the data in this file look like is shown below.

```text
cl, http://purl.obolibrary.org/obo/cl.owl
chebi, http://purl.obolibrary.org/obo/chebi.owl
hp, http://purl.obolibrary.org/obo/hp.owl
mondo, http://purl.obolibrary.org/obo/mondo.owl
ncbitaxon, http://purl.obolibrary.org/obo/ncbitaxon.owl
pr, http://purl.obolibrary.org/obo/pr.owl
uberon, http://purl.obolibrary.org/obo/uberon/ext.owl
vo, http://purl.obolibrary.org/obo/vo.owl
```


### Data Processing  
The functionality in the `omop2obo/ontology_downloader.py` script is used to download all the ontologies that are
listed in the `resources/ontology_source_list.txt` script. Each file is downloaded as an `.owl` file and saved to the
`resources/ontologies/` directory. Metadata for all downloaded files are recorded and written to 
`resources/ontologies/ontology_source_metadata.txt`. The second script (`omop2obo/ontology_explorer.py`) is then run
which processes each downloaded ontology creating the following objects for each ontology: a Pandas `DataFrame`
containing ontology metadata and a dictionary for each ontology class that contains its ancestors and children concepts.
Note that a dictionary containing the three objects for each ontology is pickled to `resources/ontologies/processed_obo_data_dictionary.pkl`.
The keys in this file are ontology aliases and each alias has three keys: 'df', 'ancestors', and 'children'. An example
of what the data within each object looks like is shown below for the `Cell Ontology`. A final example showing what the
master dictionary holding all ontology data is also provided below.

#### `cl_ontology_hierarchy_information.pkl`  
```python
obo_id                       http://purl.obolibrary.org/obo/CL_0002188
code                                                        CL:0002188
string                                     glomerular endothelial cell
string_type                                                class label
dbx                                                            0004632
dbx_type                                            oboInOwl:hasDbXref
dbx_source                                                         bto
dbx_source_name                                                    bto
obo_source           http://purl.obolibrary.org/obo/cl/releases/202...
obo_semantic_type                                                   cl
```

#### `cl_ontology_ancestors.json`  
For each ontology class that has at least one ancestor or child concept, there is a dictionary where keys are numbers
representing the number of levels above (ancestors) that each concept is found.

```python
'http://purl.obolibrary.org/obo/CL_0002188': {
     '0': ['http://purl.obolibrary.org/obo/CL_1000746',
           'http://purl.obolibrary.org/obo/CL_0000115',
           'http://purl.obolibrary.org/obo/CL_0000666'],
     '1': ['http://purl.obolibrary.org/obo/CL_1000612',
           'http://purl.obolibrary.org/obo/CL_0000213',
           'http://purl.obolibrary.org/obo/CL_0002078'],
     '2': ['http://purl.obolibrary.org/obo/CL_0002584',
           'http://purl.obolibrary.org/obo/CL_1000449',
           'http://purl.obolibrary.org/obo/CL_0000215'],
     '3': ['http://purl.obolibrary.org/obo/CL_0002518',
           'http://purl.obolibrary.org/obo/CL_0002681'],
     '4': ['http://purl.obolibrary.org/obo/CL_0000066',
           'http://purl.obolibrary.org/obo/CL_1000497'],
     '5': ['http://purl.obolibrary.org/obo/CL_0002371',
           'http://purl.obolibrary.org/obo/CL_0000548'],
     '6': ['http://purl.obolibrary.org/obo/CL_0000255'],
     '7': ['http://purl.obolibrary.org/obo/CL_0000003'],
     '8': ['http://purl.obolibrary.org/obo/CL_0000000']
}
```

#### `cl_ontology_children.json`  
For each ontology class that has at least one ancestor or child concept, there is a dictionary where keys are numbers
representing the number of levels below (children) that each concept is found.

```python
'http://purl.obolibrary.org/obo/CL_0002188': {
     '0': ['http://purl.obolibrary.org/obo/CL_1001005']
}
```

#### `processed_obo_data_dictionary.pkl`  
```python
{
    
}
```