
## UMLS Data  

**Purpose:** This directory stores vocabulary data downloaded from the [UMLS Release File Archive](https://www.nlm.nih.gov/research/umls/licensedcontent/umlsarchives04.html). It also stores these data after they have been modified using
the functionality in the `omop2obo/process_umls_data.py` script.

**Primary Script:** `omop2obo/process_umls_data.py`  

**Output Data:**  
- `resources/umls_data/UMLS_MAP_Ancestor_Dictionary.pkl`  
- `resources/umls_data/UMLS_MAP_PANEL.pkl`  

 
<br>

### Required UMLS Data  
The UMLS data (required files listed below) can be downloaded from the [UMLS Release File Archive](https://www.nlm.nih.gov/research/umls/licensedcontent/umlsarchives04.html) and should be placed under the `resources/umls_data/` directory.
  - [`MRCONSO.RRF`](https://www.ncbi.nlm.nih.gov/books/NBK9685/table/ch03.T.concept_names_and_sources_file_mr/)    
  - [`MRDEF.RRF`](https://www.ncbi.nlm.nih.gov/books/NBK9685/table/ch03.T.definitions_file_mrdef_rrf/)    
  - [`MRHIER.RRF`](https://www.ncbi.nlm.nih.gov/books/NBK9685/table/ch03.T.computable_hierarchies_file_mrhie/)    
  - [`MRMAP.RRF`](https://www.ncbi.nlm.nih.gov/books/NBK9685/table/ch03.T.mappings_file_mrmap_rrf/)    
  - [`MRSAB.RRF`](https://www.ncbi.nlm.nih.gov/books/NBK9685/table/ch03.T.source_information_file_mrsab_rrf/)   
  - [`MRSTY.RRF`](https://www.ncbi.nlm.nih.gov/books/NBK9685/table/ch03.Tf/)    

Take the folder that is downloaded from the [UMLS Release File Archive](https://www.nlm.nih.gov/research/umls/licensedcontent/umlsarchives04.html)
and place it under the `resources/umls_data/` directory. Run the required steps to generate the data, which are provided
with the download and described on the UMLS website. Once downloaded, there is no need to change the name of the folder
as long as you have downloaded `AA`, release data the program  is designed to find it as long as it is placed in the
`resources/clinical_data/` directory. If you have limited storage space, you can delete all other data files that are
not listed above. Please note that obtaining UMLS data requires a license. Details are provided on the UMLS website.

### Data Processing  
The functionality in the `omop2obo/process_umls_data.py` script is designed to process specific OMP vocabulary data and
create two data structures. The first object is a dictionary which is keyed by UMLS `AUI`. The second object is a
Pandas `DataFrame` that contains the remaining OMOP CDM tables merged into a single object. These two objects are
pickled to: `resources/umls_data/UMLS_MAP_Ancestor_Dictionary.pkl` and `resources/umls_data/UMLS_MAP_PANEL.pkl`.
An example of what the data within each object looks like is shown below.  

#### `UMLS_MAP_Ancestor_Dictionary.pkl`  
```python
{'A32648871': {
                'UMLS_CUI': 'C5441266',
                'UMLS_SAB': 'SNOMEDCT_US',
                'ANCS': {'3': 'A3684559', '2': 'A2895444', '1': 'A3647338', '0': 'A3253161'}}
            }
```

#### `UMLS_MAP_PANEL.pkl`
```python
UMLS_CUI                                                         C0000727
UMLS_AUI                                                         A2988568
CODE                                                              9209005
STRING                                                      acute abdomen
UMLS_STRING_TYPE                                Designated preferred name
UMLS_SEMANTIC_TYPE                                        Sign or Symptom
UMLS_SAB                                                      SNOMEDCT_US
UMLS_SAB_NAME                         US Edition of SNOMED CT, 2021_03_01
UMLS_DBXREF_TYPE                                                mapped_to
DBXREF                                                              R10.0
UMLS_DBXREF_SAB                                                   ICD10CM
UMLS_DBXREF_SAB_NAME         International Classification of Diseases,...
```
