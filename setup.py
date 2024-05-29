import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    LONG_DESCRIPTION = fh.read()
LONG_DESCRIPTION_TYPE = 'text/markdown'

NAME = 'PyCellDyn'
AUTHOR = 'Arturo Moncada-Torres'
AUTHOR_EMAIL = 'a.moncadatorres@umcutrecht.nl'

DESCRIPTION = 'A Python package for working with CELL-DYN (i.e., Sapphire and Alinity hq) data.'
LICENSE = 'Apache License 2.0'

PYTHON_REQ = '>=3.10'


setuptools.setup(
    name=NAME,
    version='0.1.0',
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    include_package_data=True,
    long_description=LONG_DESCRIPTION,
    long_description_content_type=LONG_DESCRIPTION_TYPE,
    url='https://github.com/UPOD-datascience/pycelldyn',
    project_urls = {
        "Issues": "https://github.com/UPOD-datascience/pycelldyn/issues",
        "Documentation": "https://upod-datascience.github.io/pycelldyn/"
    },
    python_requires=PYTHON_REQ,
    license=LICENSE,
    packages=['pycelldyn'],
    package_data={'kipy': ['dictionaries/*.xlsx']},
    install_requires=['missingno>=0.5.2',
                      'numpy>=1.23.5',
                      'openpyxl>=3.0.10',
                      'pandas>=1.4.0', 
                      'pathlib>=1.0.0',
                      'scipy>=1.10.1',
                      'seaborn>=0.11.2',
                      'statannotations>=0.5.0',
                      'statsmodels>=0.13.5'],
)