omop2obo
=========================================================================================
|travis| |sonar_quality| |sonar_maintainability| |codacy| 

|coveralls| |sonar_coverage| |code_climate_coverage|  

|ABRA|

.. |pip| |downloads|


``omop2obo`` is a health system-wide, disease-agnostic mappings between standardized clinical terminologies in the Observational Medical Outcomes Partnership (`OMOP`_) common data model and several Open Biomedical Ontologies (`OBO`_) foundry ontologies.

This repository stores releases of validated versions of the mappings as well as provides code to enable automatic mapping between OMOP clinical concepts and OBO concepts using the following steps:  
  - Aligns UMLS CUI and Semantic Types       
  - Creates DbXRef and Exact String Mapping    
  - Performs TF-IDF Cosine Similarity Mapping    

Please see the Project `Wiki`_ for more details!

|

Releases
----------------------------------------------

Coming soon!

.. All code and output for each release are free to download, see `Wiki <https://github.com/callahantiff/PheKnowLator/wiki>`__ for full release .. archive.
.. 
.. **Current Release:**  
.. 
.. - ``v2.0.0`` ➞ data and code can be directly downloaded `here <https://github.com/callahantiff/PheKnowLator/wiki/v2.0.0>`__.
.. 
.. **Prior Releases:**  
.. 
.. - ``v1.0.0`` ➞ data and code can be directly downloaded (PUT DOID MAP HERE) `here <https://github.com/callahantiff/PheKnowLator/wiki/v1.0.0>`__.
.. 

|

Getting Started
------------------------------------------

**Install Library**   

This program requires Python version 3.6. To install the library from PyPI, run:

.. code:: shell

  pip install omop2obo

|

You can also clone the repository directly from GitHub by running:

.. code:: shell

  git clone https://github.com/callahantiff/OMOP2OBO.git

|

Set-Up Environment     
^^^^^^^^^^^^

The ``omop2obo`` library requires a specific project directory structure. Please make sure that your project directory includes the following sub-directories:  

.. code:: shell

    OMOP2OBO/  
        |
        |---- resources/
        |         |
        |     clinical_data/
        |         |
        |     mappings/
        |         |
        |     ontologies/

|
|

Dependencies
^^^^^^^^^^^^

*APPLICATIONS* 

- This software also relies on `OWLTools <https://github.com/owlcollab/owltools>`__. If cloning the repository, the ``owltools`` library file will automatically be included and placed in the correct repository.

-  The National of Library Medicine's Unified Medical Language System (UMLS) `MRCONSO <https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html>`__ and `MRSTY <https://www.ncbi.nlm.nih.gov/books/NBK9685/table/ch03.Tf/>`_. Using these data requires a license agreement. Note that in order to get the `MRSTY` file you will need to download the UMLS Metathesaurus and run MetamorphoSys. Once both data sources are obtained, please place the files in the ``resources/mappings`` directory.

*DATA*

- **Clinical Data:** This repository assumes that the clinical data that needs mapping has been placed in the ``resources/clinical_data`` repository. Each data source provided in this repository is assumed to extracted from the OMOP CDM. An example of what is expected for input clinical data can be found `here <https://github.com/callahantiff/OMOP2OBO/tree/master/resources/clinical_data>`__.

- **Ontology Data:** Ontology data is automatically downloaded from the user provided input file ``ontology_source_list.txt`` (`here <https://github.com/callahantiff/OMOP2OBO/blob/master/resources/ontology_source_list.txt>`__).

|

Contributing
------------------------------------------

Please read `CONTRIBUTING.md <https://github.com/callahantiff/biolater/blob/master/CONTRIBUTING.md>`__ for details on our code of conduct, and the process for submitting pull requests to us.

|

License
------------------------------------------
This project is licensed under MIT - see the `LICENSE.md <https://github.com/callahantiff/OMOP2OBO/blob/master/LICENSE>`__ file for details.

|

Citing this Work
--------------

.. code:: shell

   @software{callahan_tiffany_j_2020_3902767,  
             author     =  {Callahan, Tiffany J},  
             title      = {OMOP2OBO},  
             month      = jun,  
             year       = 2020,  
             publisher  = {Zenodo},   
             version    = {v1.0.0},   
             doi        = {10.5281/zenodo.3902767},   
             url        = {https://doi.org/10.5281/zenodo.3902767}.  
      }

|

Contact
--------------

We’d love to hear from you! To get in touch with us, please `create an issue`_ or `send us an email`_ 💌


.. |travis| image:: https://travis-ci.org/callahantiff/OMOP2OBO.png
   :target: https://travis-ci.org/callahantiff/OMOP2OBO
   :alt: Travis CI build

.. |sonar_quality| image:: https://sonarcloud.io/api/project_badges/measure?project=callahantiff_OMOP2OBO&metric=alert_status
    :target: https://sonarcloud.io/dashboard/index/callahantiff_OMOP2OBO
    :alt: SonarCloud Quality

.. |sonar_maintainability| image:: https://sonarcloud.io/api/project_badges/measure?project=callahantiff_OMOP2OBO&metric=sqale_rating
    :target: https://sonarcloud.io/dashboard/index/callahantiff_OMOP2OBO
    :alt: SonarCloud Maintainability

.. |sonar_coverage| image:: https://sonarcloud.io/api/project_badges/measure?project=callahantiff_OMOP2OBO&metric=coverage
    :target: https://sonarcloud.io/dashboard/index/callahantiff_OMOP2OBO
    :alt: SonarCloud Coverage

.. |coveralls| image:: https://coveralls.io/repos/github/callahantiff/OMOP2OBO/badge.svg?branch=master
    :target: https://coveralls.io/github/callahantiff/OMOP2OBO?branch=master
    :alt: Coveralls Coverage

.. |pip| image:: https://badge.fury.io/py/omop2obo.svg
    :target: https://badge.fury.io/py/omop2obo
    :alt: Pypi project

.. |downloads| image:: https://pepy.tech/badge/omop2obo
    :target: https://pepy.tech/project/omop2obo
    :alt: Pypi total project downloads

.. |codacy| image:: https://app.codacy.com/project/badge/Grade/a6b93723ccb2466bb20cdb9763c2f0c5
    :target: https://www.codacy.com/manual/callahantiff/OMOP2OBO?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=callahantiff/OMOP2OBO&amp;utm_campaign=Badge_Grade
    :alt: Codacy Maintainability

.. |code_climate_maintainability| image:: https://api.codeclimate.com/v1/badges/5ad93b637f347255c848/maintainability
    :target: https://codeclimate.com/github/callahantiff/OMOP2OBO/maintainability
    :alt: Maintainability

.. |code_climate_coverage| image:: https://api.codeclimate.com/v1/badges/5ad93b637f347255c848/test_coverage
    :target: https://codeclimate.com/github/callahantiff/OMOP2OBO/test_coverage
    :alt: Code Climate Coverage
    
.. |ABRA| image:: https://img.shields.io/badge/ReproducibleResearch-AbraCollaboratory-magenta.svg
   :target: https://github.com/callahantiff/Abra-Collaboratory 
    
.. _OMOP: https://www.ohdsi.org/data-standardization/the-common-data-model/

.. _OBO: http://www.obofoundry.org/

.. _Wiki: https://github.com/callahantiff/BioLater/wiki

.. _`create an issue`: https://github.com/callahantiff/OMOP2OBO/issues/new/choose

.. _`send us an email`: https://mail.google.com/mail/u/0/?view=cm&fs=1&tf=1&to=callahantiff@gmail.com
