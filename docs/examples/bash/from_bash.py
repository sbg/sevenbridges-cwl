from sbg import cwl
import textwrap

cwl.from_bash(
    label='Example tool',
    inputs=dict(
        HELLO="HELLO WORLD",
        STR=cwl.String(),
        INT=cwl.Int(),
        FLOAT=cwl.Float(),
        BOOL=cwl.Bool(),
        ANY=cwl.Any(),
        FILE=cwl.File(),
        DIR=cwl.Dir(),
        ENUM=cwl.Enum(['opt1', 'opt2']),
        INT_OR_STR=cwl.Union([cwl.Int(), cwl.String()]),
        # with default value
        STR_DEF=cwl.String(default="hello"),
        INT_DEF=cwl.Int(default=123),
        FLOAT_DEF=cwl.Float(default=24.42),
        BOOL_DEF=cwl.Bool(default=True),
        ANY_DEF=cwl.Any(default="whatever"),
        ENUM_DEF=cwl.Enum(['opt1', 'opt2'], default='opt2'),
        INT_OR_STR_DEF=cwl.Union([cwl.Int(), cwl.String()], default=22)
    ),
    outputs=dict(
        out=cwl.File(glob='stdout')
    ),
    script=textwrap.dedent(
        r"""
        echo $HELLO
        echo $STR
        echo $INT
        echo $FLOAT
        echo $BOOL
        echo $ANY
        echo $FILE
        echo $DIR
        echo $INT_OR_STR
        echo $ENUM
        # echo defaults
        echo $STR_DEF
        echo $INT_DEF
        echo $FLOAT_DEF
        echo $BOOL_DEF
        echo $ANY_DEF
        echo $INT_OR_STR_DEF
        echo $ENUM_DEF
        """.strip()
    ),
    stdout='stdout',
    docker='images.sbgenomics.com/filip_tubic/ubuntu1604bzip'
).dump('tool.cwl')
