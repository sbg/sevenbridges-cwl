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
                
                import os
                
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(tar)
    if sys.version_info[0] == 3:
        importlib.invalidate_caches()


def dump(x):
    return json.dumps(x)


def save(x):
    with open('sbgcwl.out.json', 'w') as fp:
        fp.write(dump(x))
