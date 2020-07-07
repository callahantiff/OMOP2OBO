omop2obo
=========================================================================================
|travis| |sonar_quality| |sonar_maintainability| |codacy|
|code_climate_maintainability| |pip| |downloads|

TODO - update

How do I install this package?
----------------------------------------------
As usual, just download it using pip:

.. code:: shell

    pip install omop2obo

Tests Coverage
----------------------------------------------
Since some software handling coverages sometimes
get slightly different results, here's three of them:

|coveralls| |sonar_coverage| |code_climate_coverage|

OMOP2OBO is the first health system-wide, disease-agnostic mappings
between standardized clinical

terminologies in the `Observational Medical Outcomes Partnership
(OMOP) <https://www.ohdsi.org/data-standardization/the-common-data-model/>`__
common data model and several [Open

::

    Biomedical Ontologies (OBO)](http://www.obofoundry.org/) foundry ontologies. These mappings were validated by domain experts and their coverage was examined in several health systems.

Please see the `Project
Wiki <https://github.com/callahantiff/BioLater/wiki>`__ for more
information!

This is a Reproducible Research Repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This repository contains more than just code, it provides a detailed and
transparent narrative of our research process. For detailed information
on how we use GitHub as a reproducible research platform, click
`here <https://github.com/callahantiff/PheKnowVec/wiki/Using-GitHub-as-a-Reproducible-Research-Platform>`__.

--------------

Getting Started
~~~~~~~~~~~~~~~

Dependencies
^^^^^^^^^^^^

This repository is built using Python 3.6.2. To install the libraries
used in this repository, run the line of code

shown below from the within the project directory.

::


    pip install -r requirements.txt

This software also relies on
```OWLTools`` <https://github.com/owlcollab/owltools>`__. If cloning the
repository, the

``owltools`` library file will automatically be included and placed in
the correct repository.

-  The National of Library Medicine's Unified Medical Language System
   (UMLS)
   ```MRCONSO.RRF`` <https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html>`__.
   Using this data requires a

license agreement. Once the data is obtained, please download the file
and place it in the \`resources/mappings

/\` directory.

Data
^^^^

**Clinical Data**

This repository assumes that the clinical data that needs mapping has
been placed in the \`resources/clinical\_data

\` repository. Each data source provided in this repository is assumed
to extracted from the OMOP CDM. An example of

what is expected for input clinical data can be found
`here <https://github.com/callahantiff/OMOP2OBO/tree/master/resources/clinical_data>`__.

**Ontology Data**

Ontology data is automatically downloaded from the user provided input
file
```ontology_source_list.txt`` <https://github.com/callahantiff/OMOP2OBO/blob/master/resources/ontology_source_list.txt>`__.

.. raw:: html

   <!--### Installation



   <!--To install and execute the program designate the cloned project folder as the current working directory. Place any outside <!--files within the working directory prior to executing the program.-->

Contributing
~~~~~~~~~~~~

Please read
`CONTRIBUTING.md <https://github.com/callahantiff/biolater/blob/master/CONTRIBUTING.md>`__
for details on our code of conduct, and the process for submitting pull
requests to us.

<!--## License

<!--This project is licensed under 3-Clause BSD License - see the
`LICENSE.md <https://github.com/callahantiff/biolater/blob/master/LICENSE>`__
file for details.

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
