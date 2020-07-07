# OMOP2OBO

OMOP2OBO is the first health system-wide, disease-agnostic mappings between standardized clinical
 terminologies in the [Observational Medical Outcomes Partnership (OMOP)](https://www.ohdsi.org/data-standardization/the-common-data-model/) common data model and several [Open
    Biomedical Ontologies (OBO)](http://www.obofoundry.org/) foundry ontologies. These mappings were validated by domain experts and their coverage was examined in several health systems.

Please see the [Project Wiki](https://github.com/callahantiff/BioLater/wiki) for more information!

<br>

#### This is a Reproducible Research Repository
This repository contains more than just code, it provides a detailed and transparent narrative of our research process. For detailed information on how we use GitHub as a reproducible research platform, click [here](https://github.com/callahantiff/PheKnowVec/wiki/Using-GitHub-as-a-Reproducible-Research-Platform).

<img src="https://img.shields.io/badge/ReproducibleResearch-AbraCollaboratory-magenta.svg?style=flat-square" alt="git-AbraCollaboratory">

<br>

______

### Getting Started

#### Dependencies  
This repository is built using Python 3.6.2. To install the libraries used in this repository, run the line of code
shown below from the within the project directory.

```
pip install -r requirements.txt
```

This software also relies on [`OWLTools`](https://github.com/owlcollab/owltools). If cloning the repository, the
 `owltools` library file will automatically be included and placed in the correct repository.
 
 - The National of Library Medicine's Unified Medical Language System (UMLS) [`MRCONSO.RRF`](https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html). Using this data requires a
  license agreement. Once the data is obtained, please download the file and place it in the `resources/mappings
  /` directory.  

#### Data    
**Clinical Data**  
This repository assumes that the clinical data that needs mapping has been placed in the `resources/clinical_data
` repository. Each data source provided in this repository is assumed to extracted from the OMOP CDM. An example of
 what is expected for input clinical data can be found [here](https://github.com/callahantiff/OMOP2OBO/tree/master/resources/clinical_data).
 
 **Ontology Data**  
 Ontology data is automatically downloaded from the user provided input file [`ontology_source_list.txt`](https://github.com/callahantiff/OMOP2OBO/blob/master/resources/ontology_source_list.txt).


<!--### Installation

<!--To install and execute the program designate the cloned project folder as the current working directory. Place any outside <!--files within the working directory prior to executing the program.-->


### Contributing
Please read [CONTRIBUTING.md](https://github.com/callahantiff/biolater/blob/master/CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.



<!--## License

<!--This project is licensed under 3-Clause BSD License - see the [LICENSE.md](https://github.com/callahantiff/biolater/blob/master/LICENSE) file for details.
