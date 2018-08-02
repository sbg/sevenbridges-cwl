__all__ = [
    'StepInputExpression', 'ScatterFeature', 'MultipleInputFeature',
    'SubworkflowFeature'
]

from sbg.cwl.v1_0.base import salad
from sbg.cwl.v1_0.wf.requirement.scatter_feature import (
    ScatterFeature
)
from sbg.cwl.v1_0.wf.requirement.subworkflow_feature import (
    SubworkflowFeature
)
from sbg.cwl.v1_0.util import (
    is_instance_all_dict, is_instance_all
)
from sbg.cwl.v1_0.wf.requirement.step_input_expression import (
    StepInputExpression
)
from sbg.cwl.v1_0.wf.requirement.multiple_input_feature import (
    MultipleInputFeature
)
from sbg.cwl.v1_0.requirement import (
    InlineJavascript, SchemaDef, Docker, Software, InitialWorkDir, EnvVar,
    ShellCommand, Resource
)


@salad
def to_step_req(value):
    @salad
    def map_obj(obj):
        return obj

    @salad
    def map_to_cls(d):
        m = dict(
            InlineJavascriptRequirement=InlineJavascript,
            SchemaDefRequirement=SchemaDef,
            DockerRequirement=Docker,
            SoftwareRequirement=Software,
            InitialWorkDirRequirement=InitialWorkDir,
            EnvVarRequirement=EnvVar,
            ShellCommandRequirement=ShellCommand,
            ResourceRequirement=Resource,
            SubworkflowFeatureRequirement=SubworkflowFeature,
            ScatterFeatureRequirement=ScatterFeature,
            MultipleInputFeatureRequirement=MultipleInputFeature,
            StepInputExpressionRequirement=StepInputExpression
        )
        if 'class' in d:
            return m[d['class']](**d)
        else:
            raise Exception("Unsupported class: {}".format(d['class']))

    if value is not None:
        if is_instance_all(
                value, InlineJavascript, SchemaDef, Docker, Software,
                InitialWorkDir, EnvVar, ShellCommand, Resource,
                SubworkflowFeature, ScatterFeature, MultipleInputFeature,
                StepInputExpression
        ):
            return value
        elif is_instance_all_dict(
                value, InlineJavascript, SchemaDef, Docker, Software,
                InitialWorkDir, EnvVar, ShellCommand, Resource,
                SubworkflowFeature, ScatterFeature, MultipleInputFeature,
                StepInputExpression
        ):
            return value
        elif isinstance(value, list):
            return list(map(map_to_cls, value))
        elif isinstance(value, dict):
            return {k: map_obj(v) for k, v in value.items()}
        else:
            raise TypeError('TypeError got: {}'.format(type(value)))
