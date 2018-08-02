import os
import ast
import dill
import types
import base64
import inspect
import textwrap
import importlib
from operator import itemgetter
from sbg.cwl.serialize.plugins import plugins
from sbg.cwl.serialize.inspector import Function


class Context(object):
    def __init__(self, func):
        self.to_tool = func
        self.imports = {}
        self.functions = {}
        self.classes = {}
        self.variables = {}
        self.modules = set()
        self.working_dir = os.getcwd()

    def _import(self, key, obj):
        if isinstance(obj, types.ModuleType):
            # Local modules should be completely included as resources
            if hasattr(obj, '__file__'):
                if obj.__file__.startswith(self.working_dir):
                    self.modules.add(obj.__file__)
        elif not obj.__module__.startswith('_'):  # not cpython extension
            module = importlib.import_module(obj.__module__)
            if hasattr(module, '__file__'):
                module_file = os.path.abspath(module.__file__)
                if module_file.startswith(self.working_dir):
                    # Add local modules to tar
                    if module_file.endswith('.pyc'):
                        module_file = module_file[:-1]
                    self.modules.add(module_file)
        self.imports[key] = obj

    def add(self, key, obj):
        if isinstance(obj, types.ModuleType):
            self._import(key, obj)
        elif isinstance(obj, types.BuiltinFunctionType):
            if hasattr(obj, '__module__') and obj.__module__ is None:
                self.variables[key] = obj
            else:
                self._import(key, obj)
        elif isinstance(obj, types.FunctionType):
            if obj.__module__ == self.to_tool.__module__:
                # If function is in self.to_tool.__module__
                # serialize the function and all it's dependencies
                func = Function(obj)
                self.functions[func.name] = func
                for key, val in func.dependencies:
                    self.add(key, val)
            else:
                # If function is not in to_tool.__module__
                # just add it as an import
                self._import(key, obj)
        elif isinstance(obj, type):  # for classes
            if obj.__module__ == self.to_tool.__module__:
                self.classes[key] = obj
                items = obj.__dict__.items()
                for name, obj in items:
                    if isinstance(obj, (types.FunctionType, types.MethodType)):
                        func = Function(obj)
                        for key, val in func.dependencies:
                            self.add(key, val)
            else:
                self._import(key, obj)
        else:
            # It's a variable, try it first against the plugins
            for plugin in plugins:
                if plugin.can_serialize(obj):
                    plugin.serialize(self, key, obj)
                    break
            # If none of the plugins work, just pickle it
            else:
                self.variables[key] = obj

    def create_imports(self):
        def create_import(alias, obj):
            name = obj.__name__
            if isinstance(obj, (type, types.FunctionType,
                                types.BuiltinFunctionType)):
                # cpython extensions have convention of prefixing with _ module
                # names so we need to strip it (eg. _functools)
                imp = 'from {} import {}'.format(
                    obj.__module__.lstrip('_'), name
                )
            elif isinstance(obj, types.ModuleType):
                imp = 'import {}'.format(name)
            return imp + ('' if name == alias else ' as {}'.format(alias))

        return sorted([
            create_import(alias, obj) for alias, obj in self.imports.items()
        ], key=lambda i: ('0' if i[0] == 'i' else '1') + i)

    def create_variables(self):
        def encode_variable(name, variable):
            variable = base64.b64encode(dill.dumps(variable))
            return '''{} = sbgcwl_util.loads({})\n\n'''.format(name, variable)

        return [
            encode_variable(name, var)
            for name, var in
            sorted(self.variables.items(), key=itemgetter(0))
        ]

    @staticmethod
    def _create_function(f):
        source = inspect.getsource(f.func)
        func_def = ast.parse(textwrap.dedent(source)).body[0]
        offset = -1 if inspect.getdoc(f.func) is None else 0
        lineno = func_def.body[0].lineno + offset
        body_lines = inspect.getsourcelines(f.func)[0][lineno:]
        sig = inspect.signature(f.func)
        new_f = 'def {fname}({args}):\n{body}'.format(
            fname=f.name,
            args=', '.join([p for p in sig.parameters]),
            body=''.join(body_lines)
        )

        return new_f

    def create_functions(self):

        # sort by decorators
        return [
            self._create_function(func)
            for _, func in sorted(self.functions.items(), key=itemgetter(1))
        ]

    def create_classes(self):
        return [
            inspect.getsource(c)
            for _, c in self.classes.items()
        ]
