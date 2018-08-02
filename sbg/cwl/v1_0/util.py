import io
import os
import yaml
import time
import base64
import tarfile
from datetime import datetime


def from_file(cwl):
    """
    Load CWL document from file.

    :param cwl: file (can be either in ``JSON`` or ``YAML`` format)
    :return: ``dict`` representation of loaded file
    """

    if isinstance(cwl, str):
        if os.path.isfile(cwl):
            with open(cwl, 'r') as fp:
                cwl = yaml.load(fp)
        else:
            raise ValueError("Expected yaml/json file got, {}".format(cwl))
    else:
        raise ValueError("Expected file path, got {}".format(cwl))
    return cwl


def is_instance_all(obj, *classes):
    """
    Checks if ``obj`` is a list and all values are an instance of one of
    ``*classes``.
    """

    return isinstance(obj, list) and all(
        isinstance(i, classes) for i in obj
    )


def is_instance_all_dict(obj, *classes):
    """
    Checks if ``obj`` is a dict and all values are an instance of one of
    ``*classes``.
    """

    return isinstance(obj, dict) and all(
        isinstance(v, classes) for _, v in obj.items()
    )


def is_instance_both(obj, *classes):
    """Checks if ``obj`` satisfy ``is_instance_all`` and ``is_instance``"""

    return isinstance(obj, classes) or is_instance_all(obj, *classes)


def archive(names, mode='w:bz2', encode=False, arcnames=None):
    """
    Archives files/dirs using their paths specified by ``names``.

    :param mode: tar modes
    :param encode: encode bundle using base64
    :param arcnames: dict with arcnames for names
    :return: byte stream
    """

    def fix_mtime(tarinfo):
        d = datetime.strptime('1971-01-02', '%Y-%m-%d')
        t = time.mktime(d.timetuple())  # using this archive will look the same
        tarinfo.mtime = t
        return tarinfo

    if not arcnames:
        arcnames = dict()

    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode=mode) as tar:
        for name in sorted(names):
            if os.path.isfile(name) or os.path.isdir(name):
                arcname = arcnames.get(name)
                if not arcname:
                    arcname = os.path.basename(name)
                tar.add(name, arcname=arcname, filter=fix_mtime)
            else:
                raise ValueError(
                    "Expected file or dir, got {}".format(
                        name
                    )
                )
    stream.seek(0)
    if encode:
        return base64.b64encode(stream.read()).decode('ascii')
    return stream
