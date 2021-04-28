import os
import io
from os import path
from datetime import datetime
from setuptools import setup, find_packages

NAME = 'sevenbridges-cwl'
VERSION = '0.0.1'
DIR = path.abspath(path.dirname(__file__))
NOW = datetime.utcnow()

if os.path.exists('./VERSION'):
    with io.open('./VERSION', 'r') as f:
        VERSION = f.read().strip()

with open(path.join(DIR, 'README.md')) as f:
    long_description = f.read()

setup(
    name=NAME,
    version=VERSION,
    packages=find_packages(),
    platforms=['POSIX', 'MacOS', 'Windows'],
    install_requires=[
        "sevenbridges-python>=0.13.2",
        "dill==0.3.3",
        "PyYAML==5.4.1"
    ],
    author='Seven Bridges Genomics Inc.',
    maintainer='Seven Bridges Genomics Inc.',
    maintainer_email='filip.tubic@sbgenomics.com',
    author_email='filip.tubic@sbgenomics.com',
    description='SBG Python library to create CWL tools and workflows',
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    license='Copyright (c) {} Seven Bridges Genomics'.format(NOW.year),
    classifiers=[
        'Intended Audience :: Developers',
        'License :: Other/Proprietary License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
    ],
    keywords='seven bridges cwl common workflow language'
)
