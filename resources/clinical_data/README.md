
## OMOP Vocabulary Data  

**Purpose:** This directory stores vocabulary data downloaded from the [Observational Health Data Sciences and Informatics
(OHDSI) Athena](https://athena.ohdsi.org/) web application. It also stores these data after they have been modified using
the functionality in the `omop2obo/process_omop_data.py` script.

**Primary Script:** `omop2obo/process_omop_data.py`  

**Output Data:**  
- `resources/clinical_data/OMOP_MAP_Ancestor_Dictionary.pkl`  
- `resources/clinical_data/OMOP_MAP_PANEL.pkl`  

 
<br>

### Required OMOP Data  
The OMOP vocabulary data (required files listed below) can be downloaded from the [OHDSI Athena](https://athena.ohdsi.org/)
web application and should be placed under the `resources/clinical_data/` directory.
  - [`CONCEPT.csv`](https://github.com/chop-dbhi/data-models/blob/master/omop/v5/definitions/concept.csv)   
  - [`CONCEPT_ANCESTOR.csv`](https://github.com/chop-dbhi/data-models/blob/master/omop/v5/definitions/concept_ancestor.csv)   
  - [`CONCEPT_RELATIONSHIP.csv`](https://github.com/chop-dbhi/data-models/blob/master/omop/v5/definitions/concept_relationship.csv)   
  - [`CONCEPT_SYNONYM.csv`](https://github.com/chop-dbhi/data-models/blob/master/omop/v5/definitions/concept_synonym.csv)   
  - [`VOCABULARY.csv`](https://github.com/chop-dbhi/data-models/blob/master/omop/v5/definitions/vocabulary.csv)  

Take the folder that is downloaded from the [OHDSI Athena](https://athena.ohdsi.org/) web application and place it under
the `resources/clinical_data/` directory. Unzip the folder here, no need to change the name of the folder, the program
is designed to find it as long as it is placed in the `resources/clinical_data/` directory. If you have limited storage
space, you can delete all other data files that are not listed above.  

### Data Processing  
The functionality in the `omop2obo/process_omop_data.py` script is designed to process specific OMP vocabulary data and
create two data structures. The first object is a dictionary which is keyed by `omop_concept`. The second object is a
Pandas `DataFrame` that contains the remaining OMOP CDM tables merged into a single object. These two objects are
pickled to: `resources/clinical_data/OMOP_MAP_Ancestor_Dictionary.pkl` and `resources/clinical_data/OMOP_MAP_PANEL.pkl`.
An example of what the data within each object looks like is shown below.  

#### `OMOP_MAP_Ancestor_Dictionary.pkl`  
```python
{'35619487': {
                '0': {'35619484', '37209200'},
                '1': {'37209201', '35626947'},
                '2': {'4169265'},
                '3': {'4126705'}}
            }
```

#### `OMOP_MAP_PANEL.pkl`
```python
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
```
