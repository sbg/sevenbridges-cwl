SCAFOLD = '''\
import io
import sys
import json
import base64
import tarfile
import argparse
import importlib

# First we need to untar all modules to be able to import them
{b64untar}
b64untar('{archive_name}.tar.bz2.b64')
import sbgcwl_util


# Imports
{imports}


# Variables
{variables}


#Functions
{functions}


#Classes
{classes}

with open('input.json', 'r') as fp:
    args = json.loads(fp.read())

# Filter out optional arguments that are not provided
kwargs = {{k: v for k, v in args.items()}}
result = sbgcwl_util.save({function}(**kwargs))
'''

OUT_PATH = 'sbgcwl.out.json'
UTIL_PATH = 'sbgcwl_util.py'
