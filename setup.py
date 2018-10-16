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
        "dill==0.2.7.1",
        "PyYAML==3.12"
    ],
    author='Seven Bridges Genomics Inc.',
    maintainer='Seven Bridges Genomics Inc.',
    maintainer_email='filip.tubic@sbgenomics.com',
    author_email='filip.tubic@sbgenomics.com',
    description='SevenBridges Common Workflow Language',
    long_description=long_description,
    include_package_data=True,
    license='Copyright (c) {} Seven Bridges Genomics'.format(NOW.year),
    classifiers=[
        'Intended Audience :: Developers',
        'License :: Other/Proprietary License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
    ],
    keywords='seven bridges cwl'
)
