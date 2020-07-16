import os
import re
# To use a consistent encoding
from codecs import open as copen

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the relevant file
with copen(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


def read(*parts):
    with copen(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


__version__ = find_version("omop2obo", "__version__.py")

test_deps = [
    "pytest",
    "pytest-cov",
    "coveralls",
    "validate_version_code",
    "codacy-coverage"
]

extras = {
    'test': test_deps,
}

setup(
    name='omop2obo',
    version=__version__,
    description="OMOP2OBO is the first health system-wide, disease-agnostic mappings between standardized clinical "
                "terminologies in the Observational Medical Outcomes Partnership (OMOP) common data model and several "
                "Open Biomedical Ontologies (OBO).",
    long_description=long_description,
    url="https://github.com/callahantiff/OMOP2OBO",
    author="callahantiff@gmail.com",
    author_email="callahantiff",
    # Choose your license
    license='MIT',
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3'
    ],
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    tests_require=test_deps,
    # Add here the package dependencies
    install_requires=[
        'click',
        'google-api-core==1.17.0',
        'google-auth==1.14.1',
        'google-auth-oauthlib==0.4.1',
        'google-cloud==0.34.0',
        'google-cloud-core==1.3.0',
        'google-cloud-storage==1.28.0',
        'lxml',
        'nltk==3.5',
        'oauth2client==4.1.3',
        'pandas==1.0.3',
        'rdflib==5.0.0',
        'responses==0.10.12',
        'scipy==1.4.1',
        'scikit-learn==0.22.1',
        'tqdm==4.42.0'],
    extras_require=extras,
)
