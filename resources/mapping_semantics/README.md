# Semantic Mapping Representation  

**Wiki Page:** [`Semantic Mapping Representation`](https://github.com/callahantiff/OMOP2OBO/wiki/Semantic-Mapping-Representation) 

***  

## Purpose     
This repository stores information needed to create semantic representations of the `OMOP2OBO` mappings
. The current build (`V1.0`) is designed to generate semantic representations for conditions, drug exposure
ingredients, and measurements. For more information on this process, please see the wiki page referenced in the
heading above. The `OMOP2OBO` framework provides two different ways to construct semantic definitions from the
`OMOP2OBO` mapped clinical data: (1) <u>Single Ontology Definitions</u> and (2) <u>Multiple Ontology Definitions</u>.
Single Ontology Definitions are primarily utilized in order to enable one to test the logical consistency of
definitions that include more than one ontology concept. This means that each mapping that includes more than 1
clinical concept is constructed and added to it's specific ontology. Multiple Ontology Definitions are constructed in
a similar manner, but includes an additional step that combines the Single Ontology Definitions into a single new
class. It is strongly recommended to use the Multiple Ontology Definitions approach unless constructed classes need
 to be experimentally validated. See the [`Consistency Validation`](https://github.com/callahantiff/OMOP2OBO/wiki/Consistency) Wiki page for additional information.
 
 The remainder of this Wiki describes the input data and requirements needed to convert the mapped clinical data into
  semantic definitions.   

## Algorithm Requirements     
A knowledge model or schema that provides the computer with instructions on how to generate biologically meaningful
representations of each clinical mapping. There are two requirements that must be met inorder to run this algorithm:
(1) Mapped Clinical Data and (2) Multiple Ontology Definition Relations. Additional details for each clinical domain
are provided below.

### Mapped Clinical Data - Expected Input  

In order to convert the clinical mappings into the semantic definitions described above, the `OMOP2OBO` algorithm
requires data be formatted in a specific way, which if you are running the full `OMOP2OBO` workflow, will differ by
clinical domain. The lists provided for each clinical domain contain the column names (not including the ontology
mapping columns) the algorithm requires for each clinical domain. There are two input parameters that help the
algorithm navigate the input clinical data: `primary_column` and `secondary_column`. For each of these, provide a
 string that the algorithm can use to find all of the required columns. For example, for the `OMOP Drug Exposure Drug
 and Ingredient Concepts` data: `primary_column` would be "INGREDIENT" and `secondary_column` would be "DRUG".

<br>

**OMOP Condition Occurrence Concepts**  
***  

The condition mappings within the `OMOP2OBO` framework are the most straightforward to convert to semantic definitions
 (see figure below). The clinical columns required to create these definitions are shown in the table below.  
  
<img width="350" src="https://user-images.githubusercontent.com/8030363/100019658-a4067700-2d9b-11eb-98d6-823912793599.png" alt="">

<br><br>  

*Required Clinical Columns*  

Column | Example Data  
:--- | :---:  
CONCEPT_ID | 22945      
CONCEPT_LABEL | Horizontal overbite        
CONCEPT_SYNONYMS (*optional*) | Horizontal overbite (disorder)<br>Overjet<br>Horizontal overbite       
OMOP_VOCABULARY_VERSION | OMOP v5 PEDSnet 3.0      
CONCEPT_VOCAB | SNOMED      
CONCEPT_VOCAB_VERSION | SnomedCT Release 20180131      
CONCEPT_SOURCE_CODE | 70305005       
CUI | C0596028       
SEMANTIC_TYPE | Anatomical Abnormality       

<br>

**OMOP Drug Exposure Drug and Ingredient Concepts**  
***  

The drug and ingredient mappings within the `OMOP2OBO` framework are a bit more complicated to convert to semantic
definitions (see figure below) than the `OMOP` condition occurrence concepts. This is because the `OMOP2OBO` mappings
are created at the ingredient-level, but also include logic to connect each mapped ingredient to it's drug concept
identifier. The clinical columns required to create these definitions are shown in the table below.
  
<a target="_blank" href="https://user-images.githubusercontent.com/8030363/100247695-d7f6af00-2ef7-11eb-8abc-7834b1298aaf.png"> <img src="https://user-images.githubusercontent.com/8030363/100247695-d7f6af00-2ef7-11eb-8abc-7834b1298aaf.png" alt=""></a>

<br><br>  

*Required Clinical Columns*  

Column | Example Data  
:--- | :---: 
DRUG_ID | 712620    
DRUG_LABEL | ziprasidone 40 MG Oral Capsule     
DRUG_SYNONYMS (*optional*) | ziprasidone 40 MG Oral Capsule<br>ziprasidone (as ziprasidone hydrochloride monohydrate) 40 MG Oral Capsule      
DRUG_SOURCE_CODE | 313776  
DRUG_VOCAB | RxNorm    
DRUG_VOCAB_VERSION | RxNorm Full 20180507    
INGREDIENT_ID | 712615    
INGREDIENT_LABEL | ziprasidone     
INGREDIENT_SYNONYMS (*optional*) | ziprasidone     
INGREDIENT_SOURCE_CODE | 115698    
OMOP_VOCABULARY_VERSION | OMOP v5 PEDSnet 3.0    
INGREDIENT_VOCAB | RxNorm    
INGREDIENT_VOCAB_VERSION | RxNorm Full 20180507    
INGREDIENT_CUI | C0380393     
INGREDIENT_SEMANTIC_TYPE | Organic Chemical<br>Pharmacologic Substance     

<br>  

**OMOP Measurement Concepts**  
***  

The measurement and measurement result mappings within the `OMOP2OBO` framework are a bit more complicated to convert to
 semantic definitions (see figure below) than the `OMOP` condition occurrence and drug exposure concepts. This is
because the `OMOP2OBO` mappings are created at the measurement result-level, but also include logic to connect each
mapped result to its associated measurement identifier. To help organize each measurement and measurement result, a
 column called `COMPOSITE_ID` was created which concatenates the `OMOP` concept identifier and it's result type (i.e
 . `Normal`/`Low`/`High` or `Negative`/`Positive`).

The clinical columns required to create these definitions are shown in the table below.
  
<a target="_blank" href="https://user-images.githubusercontent.com/8030363/100476818-cbaf5500-30a3-11eb-9cc6-2a03167e829d.png"> <img width="2000" src="https://user-images.githubusercontent.com/8030363/100476818-cbaf5500-30a3-11eb-9cc6-2a03167e829d.png" alt=""></a>  

<br><br>  

*Required Clinical Columns*  

Column | Example Data  
:--- | :---: 
CONCEPT_ID | 3000456    
CONCEPT_LABEL | Dacrocytes [Presence] in Blood by Light microscopy    
CONCEPT_SYNONYMS (*optional*) | Dacryocytes Bld Ql Smear<br>Dacrocyte<br>HEMATOLOGY/CELL COUNTS<br>Microscopic<br>Ordinal<br>Qual<br>Qualitative<br>Screen<br>Tear drops<br>Teardrop cells<br>Teardrops<br>WB<br>Whole blood     
COMPOSITE_ID | 3000456_Positive  
OMOP_VOCABULARY_VERSION | OMOP v5 PEDSnet 3.0    
CONCEPT_VOCAB | LOINC    
CONCEPT_VOCAB_VERSION | 2.68    
CONCEPT_SOURCE_CODE | 7791-7     
CUI | C0362997     
SEMANTIC_TYPE | Clinical Attribute  
SCALE | Ordinal     
RESULT_TYPE | Positive/Negative    

 
### Other Requirements  

**Required Document:** [`omop2obo_class_relations.txt`](https://github.com/callahantiff/OMOP2OBO/blob/master/resources/semantic_mappings/omop2obo_class_relations.txt) 

As shown in the figures above, the majority of the semantic patterns involve multiple ontologies. The edges between the
 different ontologies are represented using the [Relation Ontology (RO)](http://www.obofoundry.org/ontology/ro.html).
The instructions for which `RO` terms to use between which ontologies is provided in `resources/mapping_semantics
 /omop2obo_class_relations.txt`. An example of what the data in this file looks like is provided below:
 
``` txt
conditions, HP, http://purl.obolibrary.org/obo/RO_0002201, MONDO
conditions, MONDO, http://purl.obolibrary.org/obo/RO_0002200, HP
drugs, CHEBI, http://purl.obolibrary.org/obo/RO_0002180, VO
drugs, CHEBI, http://purl.obolibrary.org/obo/RO_0002180, PR
drugs, VO, http://purl.obolibrary.org/obo/RO_0002162, NCBITAXON
drugs, PR, http://purl.obolibrary.org/obo/RO_0002162, NCBITAXON
measurements, HP, http://purl.obolibrary.org/obo/RO_0002479, UBERON
``` 
