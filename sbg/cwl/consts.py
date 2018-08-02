import os

EXPRESSION_LIB = os.path.join(
    os.path.join(
        os.path.dirname(__file__), 'resources', 'expression_lib.js'
    )
)

BASH_LIB = os.path.join(
    os.path.join(
        os.path.dirname(__file__), 'resources', 'bash', 'util.sh'
    )
)

BASH_BUNDLE_NAME = 'sbg.lib.tar.bz2.b64'

INHERIT_SINGLE = '''\
${{
    {preprocess}
    if (!isNull(self)){{
        return inheritMetadata(self[0], inputs.{input})
    }}
    return self
}}
'''

INHERIT_MULTI = '''\
${{
    {preprocess}
    if (!isNull(self)) {{
        return self.map(function(x) {{
            return inheritMetadata(x, inputs.{input})
        }})
    }}
    return self
}}
'''

SBG_NAMESPACE = 'https://sevenbridges.com'
