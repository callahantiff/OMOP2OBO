
## Clinical Data

**Dependencies:**  
- [Observational Medical Outcomes Partnership](https://www.ohdsi.org/data-standardization/the-common-data-model/) formatted data  
- [Accessing Google Service Account Json](https://stackoverflow.com/questions/46287267/how-can-i-get-the-file-service-account-json-for-google-translate-api)  

***

**Purpose:** This repository stores tab-delimited `.csv` files of clinical data that have been manually added by a user or that have been downloaded from a [Google Cloud Storage](https://cloud.google.com/storage) bucket. The algorithm utilized in this repository assumes that a separate file will be provided for each clinical domain (i.e conditions, drugs, or measurements) and that each file will contain at minimum, the following columns for each clinical domain:  
 
<br>

 _CONDITIONS (OMOP `condition_occurrence`)_  
   - **[`Condition_Occurrence Wiki Page`](https://github.com/callahantiff/OMOP2OBO/wiki/Conditions)**  
  - **[`Condition_Occurrence SQl Query`](https://gist.github.com/callahantiff/7b84c1bc063ad162bf5bdf5e578d402f/raw/2c002478192ba376b608bbcb638ce5960a4338a7/OMOPConcepts_ConditionOccurrence.sql)** 
 
CONCEPT_ID | CONCEPT_SOURCE_CODE | CONCEPT_LABEL | CONCEPT_SOURCE_LABEL | CONCEPT_VOCAB | CONCEPT_VOCAB_VERSION | CONCEPT_SYNONYM | ANCESTOR_CONCEPT_ID | ANCESTOR_SOURCE_CODE | ANCESTOR_LABEL | ANCESTOR_VOCAB | ANCESTOR_VOCAB_VERSION
-- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | --
4331309 | snomed:419381000000107 \| read:Gyu5K00 \| snomed:22653005 \| icd10:I40.0 \| icd10:I41.0 \| ciel:115426 \| snomed:194959002 \| read:G52y600 \| icd10cm:I40.0 \| ciel:115427 | Myocarditis due to infectious agent | [X]Myocarditis in other infectious and parasitic diseases classified elsewhere \| Infective myocarditis \| Infective Myocarditis \| Myocarditis due to Infectious Agent \| Myocarditis due to infectious agent \| Septic myocarditis NOS \| Myocarditis in bacterial diseases classified elsewhere | Read \| ICD10 \| CIEL \| SNOMED \| ICD10CM | NHS READV2 21.0.0 20160401000001 + DATAMIGRATION_25.0.0_20180403000001 \| 2016 Release \| ICD10CM FY2018 code descriptions \| Openmrs 1.11.0 20150227 \| SnomedCT Release 20180131 | Myocarditis due to infectious agent \| Infective myocarditis \| Myocarditis due to infectious agent (disorder) | 4027384 \| 4027255 \| 4178818 | snomed:128139000 \| snomed:128599005 \| snomed:251052000 | Arthropod-borne disease \| Inflammatory disorder of mediastinum \| Finding by site | MedDRA \| SNOMED | MedDRA version 19.1 \| SnomedCT Release 20180131
37018594 | snomed:80251000119104 | Complement level below reference range | Complement level below reference range | SNOMED | SnomedCT Release 20180131 | Complement level below reference range \| Complement level below reference range (finding) | 36402192 \| 36313966 \| 36303153 | meddra:10061253 \| snomed:404684003 \| meddra:10027428 | Evaluation finding \| Metabolic disorders NEC \| Measurement finding below reference range | MedDRA \| SNOMED | MedDRA version 19.1 \| SnomedCT Release 20180131
442264 | icd10cm:M67.843 \| read:N22yz12 \| snomed:68172002 \| icd10cm:M67.854 \| icd10cm:M67.853 \| icd10cm:M67.834 \| snomed:307980004 \| snomed:202982002 \| read:N22..00 \| icd10cm:M67.844 \| icd10cm:M67.824 \| icd10cm:M67.873 \| icd10cm:M67.823 \| icd10cm:M67.863 \| icd10cm:M67.874 \| ciel:141984 \| icd10cm:M67.833 \| icd10cm:M67.864 \| snomed:202899002 \| snomed:308181003 | Disorder of tendon | Other specified disorders of tendon, right hand \| Other specified disorders of tendon, right elbow \| Other specified disorders of tendon, left hip \| Other specified disorders of tendon, right hip \| Other specified disorders of tendon, left ankle and foot \| Other disorders of the synovium, tendon and bursa \| Other specified disorders of tendon, right wrist \| Other tendon disorder NOS \| Other specified disorders of tendon, left elbow \| Other specified disorders of tendon, right ankle and foot \| Disorder of tendon \| Other specified disorders of tendon, right knee \| Other specified disorders of tendon, left wrist \| Tendon disorder \| Calcification of tendon NOS \| Disorder of Tendon \| Other specified disorders of tendon, left knee \| Other specified disorders of tendon, left hand | ICD10CM \| Read \| SNOMED \| CIEL | ICD10CM FY2018 code descriptions \| NHS READV2 21.0.0 20160401000001 + DATAMIGRATION_25.0.0_20180403000001 \| Openmrs 1.11.0 20150227 \| SnomedCT Release 20180131 | Disorder of tendon (disorder) \| Disorder of tendon \| Tendon disorder | 36503288 \| 36516772 \| 36303153 | meddra:10022891 \| meddra:10061253 \| snomed:123946008 | Connective tissue disorder \| Musculoskeletal finding \| Disorder of body system | MedDRA \| SNOMED | MedDRA version 19.1 \| SnomedCT Release 20180131

<br>

_MEDICATIONS (OMOP `drug_exposure`)_   
  - **[`Drug Exposure Wiki Page`](https://github.com/callahantiff/OMOP2OBO/wiki/Medications)**  
  - **[`Drug Exposure SQl Query`](https://gist.github.com/callahantiff/7b84c1bc063ad162bf5bdf5e578d402f/raw/2c002478192ba376b608bbcb638ce5960a4338a7/OMOPConcepts_DrugExposure.sql)**  

CONCEPT_ID | CONCEPT_SOURCE_CODE | CONCEPT_LABEL | CONCEPT_VOCAB | CONCEPT_VOCAB_VERSION | CONCEPT_SYNONYM | ANCESTOR_CONCEPT_ID | ANCESTOR_SOURCE_CODE | ANCESTOR_LABEL | ANCESTOR_VOCAB | ANCESTOR_VOCAB_VERSION | INGREDIENT_CONCEPT_ID | INGREDIENT_SOURCE_CODE | INGREDIENT_LABEL | INGREDIENT_VOCAB | INGREDIENT_VOCAB_VERSION | INGREDIENT_SYNONYM | INGRED_ANCESTOR_CONCEPT_ID | INGRED_ANCESTOR_SOURCE_CODE | INGRED_ANCESTOR_LABEL | INGRED_ANCESTOR_VOCAB | INGRED_ANCESTOR_VOCAB_VERSION
-- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | --
19010970 | rxnorm:11251 | Vitamin B Complex | RxNorm | RxNorm Full 20180507 | Vitamin B Complex | 19010970 | rxnorm:11251 | Vitamin B Complex | RxNorm | RxNorm | 19010970 | rxnorm:11251 | Vitamin B Complex | RxNorm | RxNorm Full 20180507 | Vitamin B Complex | 19010970 | rxnorm:11251 | Vitamin B Complex | RxNorm | RxNorm Full 20180507
19136097 | rxnorm:100213 | Bifidobacterium Infantis | RxNorm | RxNorm Full 20180507 | Bifidobacterium Infantis | 19136097 | rxnorm:100213 | Bifidobacterium Infantis | RxNorm | RxNorm | 19136097 | rxnorm:100213 | Bifidobacterium Infantis | RxNorm | RxNorm Full 20180507 | Bifidobacterium Infantis | 19136097 | rxnorm:100213 | Bifidobacterium Infantis | RxNorm | RxNorm Full 20180507
1401440 | rxnorm:198644 | Garlic preparation 100 MG Oral Tablet | RxNorm | RxNorm Full 20180507 | Garlic preparation 100 MG Oral Tablet | 40047801 \| 1401500 \| 36222902 \| 36217214 \| 1401440 \| 36222903 \| 1401437 \| 36217216 | rxnorm:198644 \| rxnorm:1163938 \| rxnorm:1163937 \| rxnorm:265647 \| rxnorm:375084 \| rxnorm:331973 \| rxnorm:1151133 \| rxnorm:1151131 | Garlic preparation 100 MG \| Pill \| Oral Product \| Garlic preparation 100 MG Oral Tablet \| Garlic preparation Oral Tablet \| Garlic preparation Pill \| Garlic preparation Oral Product \| Garlic preparation | RxNorm | RxNorm | 1401437 | rxnorm:265647 | Garlic preparation | RxNorm | RxNorm Full 20180507 | Garlic preparation | 40047801 \| 36222902 \| 1401500 \| 36217214 \| 1401440 \| 1401437 \| 36222903 \| 36217216 | rxnorm:1163937 \| rxnorm:198644 \| rxnorm:265647 \| rxnorm:1163938 \| rxnorm:375084 \| rxnorm:331973 \| rxnorm:1151131 \| rxnorm:1151133 | Garlic preparation 100 MG \| Oral Product \| Pill \| Garlic preparation Oral Tablet \| Garlic preparation Oral Product \| Garlic preparation 100 MG Oral Tablet \| Garlic preparation \| Garlic preparation Pill | RxNorm | RxNorm Full 20180507

<br>

_MEASUREMENTS (OMOP `measurements`)_  
  - **[`Measurement Wiki Page`](https://github.com/callahantiff/OMOP2OBO/wiki/Laboratory-Tests)**  
  - **[`Measurement SQl Query`](https://gist.github.com/callahantiff/7b84c1bc063ad162bf5bdf5e578d402f/raw/2c002478192ba376b608bbcb638ce5960a4338a7/OMOPConcepts_Measurements.sql)**  

CONCEPT_ID | CONCEPT_SOURCE_CODE | CONCEPT_LABEL | CONCEPT_VOCAB | CONCEPT_VOCAB_VERSION | CONCEPT_SYNONYM | ANCESTOR_CONCEPT_ID | ANCESTOR_SOURCE_CODE | ANCESTOR_LABEL | ANCESTOR_VOCAB | ANCESTOR_VOCAB_VERSION | SCALE | RESULT_TYPE
-- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | --
40771573 | loinc:69052-9 | Flow cytometry specialist review of results | LOINC | LOINC 2.64 | Flow cytometry specialist review of results \| Flow cytometry specialist review \| Dynamic; Impression; Impression/interpretation of study; Impressions; Interp; Interpretation; Misc; Miscellaneous; Narrative; Other; Point in time; Random; Report; To be specified in another part of the message; Unspecified | 36208195 \| 36206173 \| 40771573 \| 45876017 | loinc:LP248770-2 \| loinc:69052-9 \| loinc:LP29693-6 \| MISC | Laboratory Categories \| Miscellaneous \| Lab terms not yet categorized \| Flow cytometry specialist review of results | LOINC | LOINC 2.64 | NAR | Normal/Low/High
3050001 | loinc:46252-3 | Acylcarnitine pattern [Interpretation] in Serum or Plasma | LOINC | LOINC 2.64 | Acylcarnitine pattern SerPl-Imp \| Acyl carnitine; Acylcarni; Chemistry; Impression; Impression/interpretation of study; Impressions; Interp; Interpretation; Nominal; Pl; Plasma; Plsm; Point in time; Random; SerP; SerPl; SerPlas; Serum; Serum or plasma; SR \| Acylcarnitine pattern [Interpretation] in Serum or Plasma | 3047123 \| 40785853 \| 40789215 \| 21496441 \| 40792372 \| 36206173 \| 36208195 \| 45876002 \| 40772935 \| 3050001 \| 45876249 \| 40783186 \| 45876033 \| 40794997 \| 40785803 \| 40796128 | loinc:43433-2 \| loinc:LP15318-6 \| loinc:CHEM \| loinc:LP31388-9 \| loinc:LP29693-6 \| loinc:PANEL.CHEM \| loinc:LP71614-9 \| loinc:LP248770-2 \| loinc:LP14482-1 \| loinc:LP32744-2 \| loinc:LP15705-4 \| loinc:46252-3 \| loinc:LP30844-2 \| loinc:PANEL \| loinc:LP14483-9 \| loinc:LP40271-6 | Acylcarnitine panel - Serum or Plasma \| Chemistry \| Order set \| Chemistry, challenge \| Acylcarnitine pattern \| Bld-Ser-Plas \| Carnitine \| Urinalysis \| Acylcarnitine \| Lipids \| Acylcarnitine pattern [Interpretation] in Serum or Plasma \| Acylcarnitine pattern \| Carnitine esters \| Laboratory Categories \| Chemistry order set \| Lab terms not yet categorized | LOINC | LOINC 2.64 | NOM | Normal/Low/High

***  


### Downloading Clinical Data from Google Cloud Storage  
The repo comes with functionality to help users download data from a Google Cloud Storage bucket. In order to utilize this functionality, you need to obtain the following:  
- [x] The name of the Google Cloud Storage Bucket  
- [x] The path to the location of the data within the Google Cloud Storage bucket (e.g. `OMOP2OBO_ClinicalData`). Note that this path should point to a directory where this data is stored rather 
- [x] Service account information for the bucket where the data is stored, specifically, a service account connected to the account needs to be downloaded as a `json` file and should contain the following information (information below is fake; be sure to keep your information private, but place it somewhere in the project that is reachable by the code). For help obtaining this document see [this](https://stackoverflow.com/questions/46287267/how-can-i-get-the-file-service-account-json-for-google-translate-api) post:  

  ```python
  {
  "type": "service_account",
  "project_id": "sandbox-awesome",
  "private_key_id": "999999999999999999",
  "private_key": "-----BEGIN PRIVATE KEY-----\n123456789abcdefghhijklmnopqrstuvwxyz123456789\n-----END PRIVATE KEY-----\n",
  "client_email": "xxxxxxxx.iam.gserviceaccount.com",
  "client_id": "999",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x999/xxxxxxxx.iam.gserviceaccount.com"
   }
  ```
 
 <br>

Once the required information described above has been obtianed, run the following script from the terminal:  
   
```bash
python3 google_cloud_storage_downloader.py 
``` 
   
<br>

You will then be prompted for the information shown below specific content provided as an example):  
- The data to download from Google Cloud Storage (GCS) is stored in a bucket called `sandbox-awesome.appspot.com`  
- The data to download is stored in a directory called `clinical_data` and that directory is located within the `sandbox-awesome.appspot.com` bucket   
- Service account information for this account is stored locally at `resources/programming/google_api/sandbox-tc-43a70953c062.json`
  
```bash
The name of the GCS bucket: sandbox-awesome.appspot.com
The name of the GCS bucket directory to download data from: clinical_data
The filepath to service_account.json file: resources/programming/google_api/sandbox-awesome-99999999.json
 ```
 
_NOTE_. All data is ddownloadedd locally to `resources/clinical_data`
