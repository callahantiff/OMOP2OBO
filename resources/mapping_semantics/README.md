## Semantic Mapping Representation  

**Wiki Page:** [`Semantic Mapping Representation`](https://github.com/callahantiff/OMOP2OBO/wiki/Semantic-Mapping-Representation) 

***  

**Purpose:**  This repository stores information needed to create semantic representations of the `OMOP2OBO` mappings
. The current build (`V1.0`) is designed to generate semantic representations for conditions, drug exposure
 ingredients, and measurements. For more information on this process, please see the wiki page referenced in the
  heading above.


  **Requirements:** A knowledge model or schema that provides the computer with instructions on how to generate
   biologically meaningful representations of each mapping. The figure shown below provides examples of several
    patterns, by clinical domain, utilized in `V1.0` of the `OMOP2OBO` mappings.

![kr_mappings](https://user-images.githubusercontent.com/8030363/99009348-29b93580-2505-11eb-9300-be2d98354604.png)  


As shown in the figure above, the majority of the patterns involve multiple ontologies. The edges between the
 different ontologies are represented using the [Relation Ontology (RO)](http://www.obofoundry.org/ontology/ro.html
 ). The instructions for which `RO` terms to use between which ontologies is provided in `resources/mapping_semantics
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

