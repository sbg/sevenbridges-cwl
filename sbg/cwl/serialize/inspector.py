import re
import dis
import types
import inspect
import textwrap
import itertools
import functools


class Function(object):
    def_re = re.compile('^\s*def\s+')
    deco_re = re.compile(r'^\s*(?P<deco>@([^\d\W]\w*\.?)+)', re.UNICODE)
    brace_re = re.compile('^\s*\(')
    empty_brace_re = re.compile('^\s*\(\s*\)')

    def __init__(self, func):
        self.func = func
        self.func_source, self.decorators = self._parse(self.source)

    @classmethod
    def _braces(cls, s):
        empty_brace = cls.empty_brace_re.match(s)
        if empty_brace:
            return s[empty_brace.start():empty_brace.end()].lstrip()
        else:
            match = cls.brace_re.match(s)
            if match is None:
                return ''
            balance = 1
            pos = match.end()
            while balance != 0:
                pos += 1
                balance += {'(': 1, ')': -1}.get(s[pos], 0)
            return s[:pos + 1]

    @classmethod
    def _parse(cls, s):
        if cls.def_re.match(s) is not None:
            # There are no decorators, just return the function
            return s.strip(), tuple()
        else:
            match = cls.deco_re.match(s)
            if match is None:
                # I have no idea what this is, treat as no decorator
                return s, tuple()
            deco = match.groupdict()['deco']
            braces = cls._braces(s[match.end():])
            pos = match.end() + len(braces)
            func, decos = cls._parse(s[pos:])
            return func, (deco + braces,) + decos

    @property
    def name(self):
        return self.func.__name__

    @property
    def source(self):
        return textwrap.dedent(inspect.getsource(self.func).strip())

    def nested(self, instructions):
        def only_str_global(block):
            return list(filter(
                lambda i: i.opname == 'LOAD_GLOBAL' and isinstance(
                    i.argval, str
                ),
                block
            ))

        instructions_per_block = [
            list(dis.get_instructions(i.argval))
            for i in
            filter(lambda x: hasattr(x.argval, 'co_code'), instructions)
        ]

        non_code_globals = list(map(
            lambda block: only_str_global(block), instructions_per_block
        ))

        variables = {
            i.argval for i in itertools.chain(*non_code_globals)
        }

        if instructions_per_block:
            return variables.union(
                functools.reduce(
                    set.union,  # union operation
                    list(map(self.nested, instructions_per_block)),  # sequence
                    set()  # initial
                )
            )
        else:
            return set()

    @property
    def dependencies(self):
        """Returns a sanitized version of global variables dict needed for the
        provided function"""

        # Disassemble the function code and search for all LOAD_GLOBAL
        # operation names and get their argument values. This is a set of all
        # global names that this function actually uses.

        instructions = list(dis.get_instructions(self.func))
        variables = {
            i.argval for i in instructions
            if i.opname == 'LOAD_GLOBAL'
        }.union(self.nested(instructions))

        # Closure variables
        for key in variables:
            if key in self.func.__globals__:
                obj = self.func.__globals__[key]
                # Skip builtins module
                if (isinstance(obj, types.ModuleType) and
                        obj.__name__ == 'builtins'):
                    continue
                # Skip types and functions from builtins
                if hasattr(obj, '__module__') and obj.__module__ == 'builtins':
                    continue
                yield key, obj

        if not hasattr(self.func, 'to_tool_args'):  # except @to_tool
            # Decorators
            for deco in self.decorators:
                # find dependencies inside decorator arguments
                # decorator name starting with @
                deco_name = Function.deco_re.match(
                    deco
                ).groupdict()['deco']
                # decorator arguments
                deco_args = list(map(
                    lambda x: x.strip(),
                    filter(
                        lambda x: x and not x.startswith('@'),
                        deco.replace(deco_name, '').strip('()').split(',')
                    )
                ))
                if deco_args:
                    # if there are, try to find some in global dependencies of
                    # func def

                    for arg in deco_args:
                        items = arg.split('=')
                        v = items[len(items) - 1].strip()
                        if v in self.func.__globals__:
                            yield v, self.func.__globals__[v]

                key = deco_name.strip('@').split('.')[0]
                yield key, self.func.__globals__[key]

    def __str__(self):
        return self.source

    def decorated_by(self, func):
        """
        Checks if ``func`` argument decorates ``self.func``.

        :param func: an instance of ``Function``
        :return: bool
        """
        deco = "@{}".format(func.func.__name__)
        for d in self.decorators:
            if d.startswith(deco):
                return True
        return False

    def __lt__(self, other):
        return not self.decorated_by(other)

    def __gt__(self, other):
        return self.decorated_by(other)
