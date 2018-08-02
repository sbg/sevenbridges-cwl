import io
import sys
import json
import dill
import base64
import tarfile
import importlib


def loads(variable):
    """Load a base64 encoded dill serialized variable"""
    return dill.loads(base64.b64decode(variable))


def b64untar(filename):
    with io.open(filename, 'rb') as f:
        with io.BytesIO() as stream:
            stream.write(base64.b64decode(f.read()))
            stream.seek(0)
            with tarfile.open(fileobj=stream, mode='r:bz2') as tar:
                tar.extractall()
    if sys.version_info[0] == 3:
        importlib.invalidate_caches()


def dump(x):
    return json.dumps(x)


def save(x):
    with open('sbgcwl.out.json', 'w') as fp:
        fp.write(dump(x))
