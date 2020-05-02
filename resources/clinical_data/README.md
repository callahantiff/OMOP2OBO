
## Clinical Data

**Dependencies:** [Observational Medical Outcomes Partnership](https://www.ohdsi.org/data-standardization/the-common-data-model/) formatted data   
**Resources:** [Accessing Google Service Account Json]( https://stackoverflow.com/questions/46287267/how-can-i-get-the-file-service-account-json-for-google-translate-api)

***

**Purpose:** This repository stores tab-delimited `.csv` files of clinical data that have been manually added by a user or that have been downloaded from a [Google Cloud Storage](https://cloud.google.com/storage) bucket.

The algorithm utilized in this repository assumes that a separate file will be provided for each clinical domain (i.e conditions, drugs, or measurements) and that each file will contain at minimum, the following columns for each clinical domain:  
 
<br>

 _CONDITIONS_  
 
OMOP | SNOMED | SNOMED LABEL | SNOMED SYNONYM | SNOMED ANCESTOR | SNOMED ANCESTOR LABEL
-- | -- | -- | -- | -- | --
4243060 | 6002006 | 10p partial monosomy syndrome | 10p partial monosomy syndrome (disorder)\|10p partial monosomy syndrome | 726380001 | deletion of part of chromosome 10
4266333 | 400153009 | abdominal fibromatosis | abdominal desmoid tumourvabdominal fibromatosis (disorder)\|abdominal desmoid tumor\|abdominal fibromatosis | 399994005 | desmoid fibromatosis
4160896 | 398963001 | abducens nerve weakness | abducens nerve weakness\|sixth cranial nerve weakness\|abducens nerve weakness (disorder) | 398925009 | abducens nerve disorder

<br>

_MEDICATIONS_  

OMOP_ID | RXNORM_ID | RXNORM_Label | Ingredient_OMOP | Ingredient | Ingredient_Label
-- | -- | -- | -- | -- | --
1036941 | 644287 | lidocaine 70 mg / tetracaine 70 mg medicated patch | 989878 | 6387 | lidocaine
1037006 | 197634 | tetrahydrocannabinol 10 mg oral capsule | 1037005 | 10402 | tetrahydrocannabinol
1036233 | 314234 | sucralfate 1000 mg oral tablet | 1036228 | 10156 | sucralfate

<br>

_MEASUREMENTS_  

OMOP_ID | LOINC_ID | LOINC Label | LOINC_SYN | Ancestor | Ancestor_Label | Result
-- | -- | -- | -- | -- | -- | --
3000185 | 2502-3 | Iron saturation [Mass Fraction] in Serum or Plasma | Iron saturation [Mass Fraction] in Serum or Plasma\|Iron Satn MFr SerPl\|Chemistry\|Fe\|FE/TIBC\|Iron Satn\|Iron/Iron binding capacity.total\|Mass fraction\|Percent\|Pl\|Plasma\|Plsm\|Point in time\|QNT\|Quan\|Quant\|Quantitative\|Random\|SAT\|Satn\|SerP\|SerPl\|SerPlas\|Serum\|Serum or plasma\|SR\| Transferrin saturation | 50190-8\|70299-3\|CHEM\|LP248770-2 | Iron and Iron binding capacity panel - Serum or Plasma\|Lab terms not yet categorized\|ESRD anemia management panel\|Chemistry | Low
3000185 | 2502-3 | Iron saturation [Mass Fraction] in Serum or Plasma | Iron Satn MFr SerPl\|Chemistry\|Fe\|FE/TIBC\|Iron Satn\|Iron/Iron binding capacity.total\|Mass fraction\|Percent\|Pl\|Plasma\|Plsm\|Point in time\|QNT\|Quan\|Quant\|Quantitative\|Random\|SAT\|Satn\|SerP\|SerPl\|SerPlas\|Serum\|Serum or plasma\|SR\|Transferrin saturation\|Iron saturation [Mass Fraction] in Serum or Plasma | LP248770-2\|50190-8\|CHEM\|70299-3 | Iron and Iron binding capacity panel - Serum or Plasma\|Chemistry\|ESRD anemia management panel\|Lab terms not yet categorized | High
