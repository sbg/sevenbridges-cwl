import re
import yaml
import json
import hashlib
import inspect
from sbg.cwl.v1_0.util import from_file


class CwlMeta(type):
    """
    This class is meta class for all CWL subclasses.

    It handles object creation by converting CamelCase to underscore arguments.
    This is important because keys in JSON object are in CamelCase, but python
    cls __init__ arguments are in underscore.

    This metaclass also ignore all extensions when calling a constructor.
    Extensions are attached to object after it's creation.
    """
    first_cap_re = re.compile('(.)([A-Z][a-z]+)')
    all_cap_re = re.compile('([a-z0-9])([A-Z])')

    @staticmethod
    def to_(k):
        s1 = CwlMeta.first_cap_re.sub(r'\1_\2', k)
        return CwlMeta.all_cap_re.sub(r'\1_\2', s1).lower()

    @staticmethod
    def params_to_(obj, params):
        kwargs = {}
        for k, v in obj.items():
            k_old = k
            if k.count(":") == 0:
                k = CwlMeta.to_(k)
            if k == 'class':
                continue
            elif k == 'in':
                k = 'in_'
            if k in params:
                kwargs[k] = v
            else:
                kwargs[k_old] = v
        return kwargs

    def __call__(cls, *args, **kwargs):
        signature = inspect.signature(cls.__init__)
        parameters = signature.parameters.values()
        kwargs = CwlMeta.params_to_(kwargs, [p.name for p in parameters])

        if not args:
            args_names = [x.name for x in signature.parameters.values()
                          if x.default == inspect._empty]
            args_names.remove('self')
            args_names = tuple(args)

            args = list(map(lambda x: kwargs[x], args_names))

            for k in args_names:
                if k in kwargs:
                    del kwargs[k]

        parameters = {p.name for p in parameters}
        cwl_kwargs = {k: v for k, v in kwargs.items() if k in parameters}
        obj = type.__call__(cls, *args, **cwl_kwargs)
        empty_keys = [k for k, v in obj.items() if v is None]
        for k in empty_keys:
            del obj[k]

        ext = set(set(kwargs.keys())).difference(set(cwl_kwargs.keys()))
        for k in ext:
            if ':' in k or '$' in k:
                obj[k] = to_salad_recursive(kwargs[k])
            else:
                raise RuntimeError(
                    'Found unsupported salad extension: {}'.format(k)
                )
        return obj


class Cwl(dict, metaclass=CwlMeta):
    """Super class for all CWL v1.0 subclasses."""

    __version__ = 'v1.0'

    def __str__(self):
        return yaml.dump(
            yaml.load(json.dumps(self, indent=2)),
            default_flow_style=False
        )

    def to_json(self):
        """
        Returns serialized JSON representation for this object.

        :return: serialized object
        """
        return json.dumps(self, indent=2)

    def to_dict(self):
        return dict(self)

    def calc_hash(self):
        """
        Returns calculated hash value for this object.

        :return: hash value using hashlib.sha512 encoded with ``utf-8``
        """
        sha = hashlib.sha512()
        sha.update(json.dumps(self, sort_keys=True).encode('utf-8'))
        return sha.hexdigest()

    def __repr__(self):
        return self.__str__()

    def dump(self, path):
        """
        Dump this object into file formated as YAML.

        :param path: file path
        """

        with open(path, 'w') as out:
            out.write(self.__str__())

    def json_dump(self, path):
        """
        Dump this object into file formated as JSON.

        :param path: file path
        """
        with open(path, 'w') as out:
            out.write(self.to_json())

    def resolve(self):
        """
        Resolve all salad schema $directives inside object
        ($mixin, $include, $import).
        """
        resolve(self)


class SaladBase(Cwl):

    def resolve_salad(self):
        raise NotImplementedError()


class SaladInclude(SaladBase):
    """Binding for salad $include directive"""

    def __init__(self, d):
        super(SaladInclude, self).__init__(d)

    def resolve_salad(self):
        with open(self["$include"]) as fp:
            return fp.read()


class SaladImport(SaladBase):
    """Binding for salad $import directive"""

    def __init__(self, d):
        super(SaladImport, self).__init__(d)

    def resolve_salad(self):
        return resolve(from_file(self["$import"]))


class SaladMixin(SaladBase):
    """Binding for salad $mixin directive"""

    def __init__(self, d):
        super(SaladMixin, self).__init__(d)

    def resolve_salad(self):
        x = dict()
        for k, v in self.items():
            if k == "$mixin":
                d = from_file(self["$mixin"])
                for k2, v2 in d.items():
                    if k2 not in self:
                        x[k2] = v2
            else:
                x[k] = v
        return x


def resolve(x):
    """Load all remote salad $directives into object"""

    if isinstance(x, SaladBase):
        x = x.resolve_salad()
    elif isinstance(x, dict):
        for k, v in x.items():
            if isinstance(v, dict):
                x[k] = resolve(v)
            elif isinstance(v, list):
                mapped = list(map(resolve, v))

                if hasattr(x, k):
                    setattr(x, k, mapped)
                else:
                    x[k] = mapped
    return x


def salad(wrapped):
    """Decorator used for handling salad $directives"""

    def wrapper(*args, **kwargs):
        value = args[0]
        if isinstance(value, dict):
            if "$import" in value:
                return SaladImport(value)
            elif "$include" in value:
                return SaladInclude(value)
            elif "$mixin" in value:
                return SaladMixin(value)
        return wrapped(*args, **kwargs)

    return wrapper


@salad
def to_salad_recursive(x):
    """
    Recursively transform keys to salad $directive instances.
    """

    if isinstance(x, dict):
        for k, v in x.items():
            x[k] = to_salad_recursive(v)
    return x
