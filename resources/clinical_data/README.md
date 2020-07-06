
## Clinical Data

**Dependencies:**  
- [Observational Medical Outcomes Partnership](https://www.ohdsi.org/data-standardization/the-common-data-model/) formatted data  
- [Accessing Google Service Account Json](https://stackoverflow.com/questions/46287267/how-can-i-get-the-file-service-account-json-for-google-translate-api)

***

**Purpose:** This repository stores tab-delimited `.csv` files of clinical data that have been manually added by a user or that have been downloaded from a [Google Cloud Storage](https://cloud.google.com/storage) bucket. The algorithm utilized in this repository assumes that a separate file will be provided for each clinical domain (i.e conditions, drugs, or measurements) and that each file will contain at minimum, the following columns for each clinical domain:  
 
<br>

 _CONDITIONS (OMOP `condition_occurrence`)_  
CONCEPT_ID | CONCEPT_SOURCE_CODE | CONCEPT_LABEL | CONCEPT_VOCAB | CONCEPT_VOCAB_VERSION | CONCEPT_SYNONYM | ANCESTOR_CONCEPT_ID | ANCESTOR_SOURCE_CODE | ANCESTOR_LABEL | ANCESTOR_VOCAB | ANCESTOR_VOCAB_VERSION
-- | -- | -- | -- | -- | -- | -- | -- | -- | -- | --
4331309 | 22653005 | Myocarditis due to infectious   agent | SNOMED | SnomedCT Release 20180131 | Myocarditis due to infectious   agent \| Infective myocarditis \| Myocarditis due to infectious agent   (disorder) | 4027384 \| 4027255 \| 4178818 | 128139000 \| 128599005 \|   251052000 | Arthropod-borne disease \|   Inflammatory disorder of mediastinum \| Finding by site | MedDRA \| SNOMED | MedDRA version 19.1 \| SnomedCT   Release 20180131
37018594 | 8.0251E+13 | Complement level below reference   range | SNOMED | SnomedCT Release 20180131 | Complement level below reference   range \| Complement level below reference range (finding) | 36402192 \| 36313966 \| 36303153 | 10061253 \| 404684003 \| 10027428 | Evaluation finding \| Metabolic   disorders NEC \| Measurement finding below reference range | MedDRA \| SNOMED | MedDRA version 19.1 \| SnomedCT   Release 20180131
442264 | 68172002 | Disorder of tendon | SNOMED | SnomedCT Release 20180131 | Disorder of tendon (disorder) \|   Disorder of tendon \| Tendon disorder | 36503288 \| 36516772 \| 36303153 | 10022891 \| 10061253 \| 123946008 | Connective tissue disorder \|   Musculoskeletal finding \| Disorder of body system | MedDRA \| SNOMED | MedDRA version 19.1 \| SnomedCT   Release 20180131

<br>

_MEDICATIONS (OMOP `drug_exposure`_  
CONCEPT_ID | CONCEPT_SOURCE_CODE | CONCEPT_LABEL | CONCEPT_VOCAB | CONCEPT_VOCAB_VERSION | CONCEPT_SYNONYM | ANCESTOR_CONCEPT_ID | ANCESTOR_SOURCE_CODE | ANCESTOR_LABEL | ANCESTOR_VOCAB | ANCESTOR_VOCAB_VERSION | INGREDIENT_CONCEPT_ID | INGREDIENT_SOURCE_CODE | INGREDIENT_LABEL | INGREDIENT_VOCAB | INGREDIENT_VOCAB_VERSION | INGRED_ANCESTOR_CONCEPT_ID | INGRED_ANCESTOR_SOURCE_CODE | INGRED_ANCESTOR_LABEL | INGRED_ANCESTOR_VOCAB | INGRED_ANCESTOR_VOCAB_VERSION
-- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | --
19010970 | 11251 | Vitamin B Complex | RxNorm | RxNorm Full 20180507 | Vitamin B Complex | 19010970 | 11251 | Vitamin B Complex | RxNorm | RxNorm | 19010970 | 11251 | Vitamin B Complex | RxNorm | RxNorm Full 20180507 | 19010970 | 11251 | Vitamin B Complex | RxNorm | RxNorm Full 20180507
19136097 | 100213 | Bifidobacterium Infantis | RxNorm | RxNorm Full 20180507 | Bifidobacterium Infantis | 19136097 | 100213 | Bifidobacterium Infantis | RxNorm | RxNorm | 19136097 | 100213 | Bifidobacterium Infantis | RxNorm | RxNorm Full 20180507 | 19136097 | 100213 | Bifidobacterium Infantis | RxNorm | RxNorm Full 20180507
1401440 | 198644 | Garlic preparation 100 MG Oral Tablet | RxNorm | RxNorm Full 20180507 | Garlic preparation 100 MG Oral Tablet | 40047801 \| 1401500 \| 36222902 \| 36217214 \| 1401440 \| 36222903 \| 1401437 \|   36217216 | 1163937 \| 198644 \| 1163938 \| 265647 \| 375084 \| 331973 \| 1151131 \| 1151133 | Garlic preparation 100 MG \| Oral Product \| Pill \| Garlic preparation Oral   Tablet \| Garlic preparation Oral Product \| Garlic preparation 100 MG Oral   Tablet \| Garlic preparation Pill \| Garlic preparation | RxNorm | RxNorm | 1401437 | 265647 | Garlic preparation | RxNorm | RxNorm Full 20180507 | 1401440 \| 36222903 \| 1401437 \| 36217216 \| 40047801 \| 1401500 \| 36222902 \|   36217214 | 375084 \| 331973 \| 1151131 \| 1151133 \| 198644 \| 1163938 \| 1163937 \| 265647 | Garlic preparation 100 MG Oral Tablet \| Garlic preparation Oral Tablet \|   Garlic preparation Pill \| Garlic preparation Oral Product \| Garlic   preparation \| Garlic preparation 100 MG \| Oral Product \| Pill | RxNorm | RxNorm Full 20180507

<br>

_MEASUREMENTS (OMOP `measurements`)_  
CONCEPT_ID | CONCEPT_SOURCE_CODE | CONCEPT_LABEL | CONCEPT_VOCAB | CONCEPT_VOCAB_VERSION | CONCEPT_SYNONYM | ANCESTOR_CONCEPT_ID | ANCESTOR_SOURCE_CODE | ANCESTOR_LABEL | ANCESTOR_VOCAB | ANCESTOR_VOCAB_VERSION | SCALE | RESULT_TYPE
-- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | --
40771573 | 69052-9 | Flow cytometry specialist review of results | LOINC | LOINC 2.64 | Flow cytometry specialist review of results \| Flow cytometry specialist   review \| Dynamic; Impression; Impression/interpretation of study;   Impressions; Interp; Interpretation; Misc; Miscellaneous; Narrative; Other;   Point in time; Random; Report; To be specified in another part of the   message; Unspecified | 36208195 \| 36206173 \| 40771573 \| 45876017 | LP248770-2 \| 69052-9 \| LP29693-6 \| MISC | Laboratory Categories \| Miscellaneous \| Lab terms not yet categorized \|   Flow cytometry specialist review of results | LOINC | LOINC 2.64 | NAR | Normal/Low/High
3050001 | 46252-3 | Acylcarnitine pattern [Interpretation] in Serum or Plasma | LOINC | LOINC 2.64 | Acylcarnitine pattern SerPl-Imp \| Acyl carnitine; Acylcarni; Chemistry;   Impression; Impression/interpretation of study; Impressions; Interp;   Interpretation; Nominal; Pl; Plasma; Plsm; Point in time; Random; SerP;   SerPl; SerPlas; Serum; Serum or plasma; SR \| Acylcarnitine pattern   [Interpretation] in Serum or Plasma | 3047123 \| 40785853 \| 40789215 \| 21496441 \| 40792372 \| 36206173 \| 36208195   \| 45876002 \| 40772935 \| 3050001 \| 45876249 \| 40783186 \| 45876033 \| 40794997 \|   40785803 \| 40796128 | 43433-2 \| LP15318-6 \| CHEM \| LP31388-9 \| LP29693-6 \| PANEL.CHEM \|   LP71614-9 \| LP248770-2 \| LP14482-1 \| LP32744-2 \| LP15705-4 \| 46252-3 \|   LP30844-2 \| PANEL \| LP14483-9 \| LP40271-6 | Acylcarnitine panel - Serum or Plasma \| Chemistry \| Order set \|   Chemistry, challenge \| Acylcarnitine pattern \| Bld-Ser-Plas \| Carnitine \|   Urinalysis \| Acylcarnitine \| Lipids \| Acylcarnitine pattern [Interpretation]   in Serum or Plasma \| Acylcarnitine pattern \| Carnitine esters \| Laboratory   Categories \| Chemistry order set \| Lab terms not yet categorized | LOINC | LOINC 2.64 | NOM | Normal/Low/High

***  


### Downloading Clinical Data from Google Cloud Storage  
The repo comes with functionality to help users download data from a Google Cloud Storage bucket. In order to utilize this functionality, you need to obtain the following:  
- [ ] The name of the Google Cloud Storage Bucket  
- [ ] The path to the location of the data within the Google Cloud Storage bucket (e.g. `OMOP2OBO_ClinicalData`). Note that this path should point to a directory where this data is stored rather 
- [ ] Service account information for the bucket where the data is stored, specifically, a service account connected to the account needs to be downloaded as a `json` file and should contain the following information (information below is fake; be sure to keep your information private, but place it somewhere in the project that is reachable by the code). For help obtaining this document see [this](https://stackoverflow.com/questions/46287267/how-can-i-get-the-file-service-account-json-for-google-translate-api) post:  

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
