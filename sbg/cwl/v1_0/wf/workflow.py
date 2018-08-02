import itertools
from sbg.cwl.v1_0.app import App
from sbg.cwl.v1_0.base import Cwl, salad
from sbg.cwl.v1_0.wf.input import WorkflowInput
from sbg.cwl.v1_0.wf.output import WorkflowOutput
from sbg.cwl.v1_0.cmd.tool import CommandLineTool
from sbg.cwl.v1_0.wf.requirement import to_step_req
from sbg.cwl.v1_0.util import is_instance_all
from sbg.cwl.v1_0.wf.expression_tool import ExpressionTool
from sbg.cwl.v1_0.check import to_str, to_any, to_str_slist
from sbg.cwl.v1_0.wf.methods import ScatterMethod, MergeMethod
from sbg.cwl.v1_0.schema import InputArray, OutputArray, Primitive
from sbg.cwl.v1_0.wf.requirement import (
    StepInputExpression, ScatterFeature, MultipleInputFeature,
    SubworkflowFeature
)
from sbg.cwl.v1_0.requirement import (
    InlineJavascript, Docker, ShellCommand, Resource, InitialWorkDir,
    Software, SchemaDef, EnvVar
)


@salad
def to_steps(value):
    """Converts `value` into workflow steps."""

    @salad
    def map_to_cls(obj):
        return Step(**obj)

    if value is not None:
        if is_instance_all(value, Step):
            return value
        elif isinstance(value, list):
            return list(map(map_to_cls, value))
        else:
            raise TypeError('Expected steps, got: {}'.format(type(value)))


class Workflow(App):
    """
    A wf describes a set of steps and the dependencies between those
    steps. When a step produces output that will be consumed by a second step,
    the first step is a dependency of the second step.

    When there is a dependency, the wf engine must execute the preceeding
    step and wait for it to successfully produce output before executing the
    dependent step. If two steps are defined in the wf graph that are not
    directly or indirectly dependent, these steps are independent, and may
    execute in any order or execute concurrently. A wf is complete when
    all steps have been executed.

    Dependencies between parameters are expressed using the source field on
    wf step input parameters and wf output parameters.

    The source field expresses the dependency of one parameter on another such
    that when a value is associated with the parameter specified by source,
    that value is propagated to the destination parameter. When all data links
    inbound to a given step are fufilled, the step is ready to execute.

    Workflow success and failure
    A completed step must result in one of success, temporaryFailure or
    permanentFailure states. An implementation may choose to retry a step
    execution which resulted in temporaryFailure. An implementation may choose
    to either continue running other steps of a wf, or terminate
    immediately upon permanentFailure.

    - If any step of a wf execution results in permanentFailure, then the
      wf status is permanentFailure.
    - If one or more steps result in temporaryFailure and all other steps
      complete success or are not executed, then the wf status is
      temporaryFailure.
    - If all wf steps are executed and complete with success, then the
      wf status is success.

    """
    class_ = 'Workflow'

    def __init__(self, cwl_version='v1.0', inputs=None,
                 outputs=None, steps=None, id=None, requirements=None,
                 hints=None, label=None, doc=None, **kwargs):
        super(Workflow, self).__init__(
            self.class_, cwl_version=cwl_version, inputs=inputs,
            outputs=outputs, id=id, requirements=requirements, hints=hints,
            label=label, doc=doc
        )
        self.steps = steps

    # region override
    def get_requirements(self, value):
        return to_step_req(value)

    def _get_cls(self):
        return Workflow

    def _get_input_cls(self):
        return WorkflowInput

    def _get_output_cls(self):
        return WorkflowOutput

    # endregion

    # region utils
    def get_step(self, id):
        """Get step by ``id``."""

        for s in self.steps:
            if s.id == id:
                return s

    def add_requirement(self, new_r):
        """Adds ``new_r`` into list of workflow requirements."""

        if isinstance(new_r, (InlineJavascript, SchemaDef, Docker, Software,
                              InitialWorkDir, EnvVar, ShellCommand, Resource,
                              StepInputExpression, ScatterFeature,
                              MultipleInputFeature, SubworkflowFeature)):
            updated = False
            if self.requirements:
                for r in self.requirements:
                    if r.class_ == new_r.class_:
                        r.update(new_r)
                        updated = True
                if not updated:
                    self.requirements.append(new_r)
            else:
                self.requirements = [new_r]
        else:
            raise TypeError('Expected Requirement got: {}'.format(type(new_r)))

    def add_connection(self, src, dst):
        """
        Connects source and destination nodes, specified by `src` and `dst`
        ids respectively.

        :param src: connection source
        :param dst: connection destination
        """

        src_arr = src.split('.')
        src_n = len(src_arr)
        dst_arr = dst.split('.')
        dst_n = len(dst_arr)

        def to_list(x):
            if not x:
                return []
            if isinstance(x, str):
                return [x]
            else:
                return x

        if src_n < 2 and dst_n < 2:
            raise ValueError("Connection have to contain minimum one step.")

        if src_n == 1 and dst_n == 2:
            step_id = dst_arr[0]
            input_id = dst_arr[1]
            for s in self.steps:
                if s.id == step_id:
                    for x in s.in_:
                        if x.id == input_id:
                            x.source = to_list(x.source)
                            x.source = list(set.union(set(x.source), {src}))
                            if len(x.source) == 1:
                                x.source = x.source[0]
                            return
                    s.in_.append(StepInput(input_id, source=src))
                    break
        elif src_n == 2 and dst_n == 1:
            step_id = src_arr[0]
            output_id = src_arr[1]
            for s in self.steps:
                if s.id == step_id:
                    for x in s.out:
                        if x.id == output_id:
                            return
                    s.out.append(StepOutput(output_id))
                    break

            for o in self.outputs:
                if o.id == dst_arr[0]:
                    o.output_source = to_list(o.output_source)
                    o.output_source = list(set.union(
                        set(o.output_source), {"{}/{}".format(
                            step_id, output_id
                        )}
                    ))
                    if len(o.output_source) == 1:
                        o.output_source = o.output_source[0]
        elif src_n == 2 and dst_n == 2:
            src_step_id = src_arr[0]
            src_output_id = src_arr[1]
            dst_step_id = dst_arr[0]
            dst_input_id = dst_arr[1]
            done_in, done_out = False, False

            for s in self.steps:
                if not done_out and s.id == src_step_id:
                    for o in s.out:
                        if o.id == src_output_id:
                            done_out = True
                            break
                    if not done_out:
                        s.out.append(StepOutput(src_output_id))
                        done_out = True

                elif not done_in and s.id == dst_step_id:
                    for i in s.in_:
                        if i.id == dst_input_id:
                            i.source = to_list(i.source)
                            i.source = list(set.union(
                                set(i.source), {"{}/{}".format(
                                    src_step_id, src_output_id
                                )}
                            ))
                            if len(i.source) == 1:
                                i.source = i.source[0]
                            done_in = True
                            break
                    if not done_in:
                        s.in_.append(StepInput(
                            dst_input_id,
                            source="{}/{}".format(
                                src_step_id, src_output_id
                            ))
                        )
                        done_in = True
        else:
            raise ValueError(
                'Unsupported value arguments: {}, {}'.format(src, dst)
            )

    def scatter(self, step, ports, method):
        """
        Scatter input ports on ``step``.

        :param step: step on which scatter is performed
        :param ports: step ports
        :param method: scatter method, required when len(ports) > 1
        """

        def find_sink(step):
            for id in map(lambda x: x.id, step.out):
                for o in self.outputs:
                    if o.output_source == '{}/{}'.format(step.id, id):
                        yield o

        def find_source(source):
            if not isinstance(source, list):
                source = [source]
            for s in source:
                i = self.get_input(s)
                if i:
                    yield i

        step.scatter = ports
        if method:
            step.scatter_method = method

        # outputs
        if not isinstance(ports, list):
            ports = [ports]
        if method == ScatterMethod.NESTED_CROSSPRODUCT:
            for o in find_sink(step):
                required = App.is_required(o.type)
                new_type = App.set_required(o.type, True)
                for _ in range(len(ports)):
                    new_type = OutputArray(new_type)
                o.type = App.set_required(new_type, required)
        else:
            for o in find_sink(step):
                required = App.is_required(o.type)
                o.type = App.set_required(
                    OutputArray(
                        App.set_required(o.type, True)
                    ), required
                )

        # inputs
        for i in filter(lambda x: x.id in ports, step.in_):
            for j in find_source(i.source):
                required = App.is_required(j.type)
                j.type = InputArray(
                    items=j.type if required else [
                        Primitive.NULL, App.set_required(j.type, True)
                    ]
                )

    def add_step(self, step, id=None, in_=None, out=None, expose=None,
                 expose_except=None, scatter=None, scatter_method=None):
        """
        Adds step into workflow.

        :param step: can be either instance of ``App`` subclass or
                     ``WorkflowStep``
        :param id: step id
        :param in_: step inputs
        :param out: step outputs
        :param expose: list or map of keys to be exposed as workflow IO
                       (default expose everything)
        :param expose_except: list of ports to be excluded from exposing
        :param scatter: scatter inputs
        :param scatter_method: scattering method required when ``scatter`` is
                               a list with > 1 port
        """

        def wf_io(new_step, k, id=None):
            if not id:
                id = k

            i = 0
            while self.get_input(id) or self.get_output(id):
                i += 1
                id = '{}_{}'.format(k, i)

            label = id
            obj = new_step.run.get_input(k)
            if obj:  # input
                param = WorkflowInput(
                    id=id,
                    label=label,
                    doc=obj.doc,
                    secondary_files=obj.secondary_files,
                    streamable=obj.streamable,
                    format=obj.format,
                    type=obj.type
                )
                if not self.inputs:
                    self.inputs = []
                self.inputs.append(param)
                self.add_connection(id, "{}.{}".format(
                    new_step.id, k
                ))
            else:  # output
                obj = new_step.run.get_output(k)
                param = WorkflowOutput(
                    id=id,
                    label=label,
                    doc=obj.doc,
                    secondary_files=obj.secondary_files,
                    streamable=obj.streamable,
                    format=obj.format,
                    type=obj.type
                )
                if not self.outputs:
                    self.outputs = []
                self.outputs.append(param)
                self.add_connection("{}.{}".format(
                    new_step.id, k
                ), id)

        s_id = id if id else step.id
        if not self.steps:
            self.steps = []
        for s in self.steps:
            if s.id == s_id:
                raise ValueError(
                    'Step with id: {} already exists'.format(s_id)
                )
        if isinstance(step, Step):
            if id:
                step.id = id
            new_step = step
        elif isinstance(step, (CommandLineTool, Workflow, ExpressionTool)):
            new_step = Step(s_id, in_, out, run=step)
        else:
            raise ValueError(
                'Not supported step type: {}'.format(type(step))
            )

        self.steps += [new_step]
        if isinstance(step, Workflow):
            self.add_requirement(SubworkflowFeature())

        expose_except = {} if not expose_except else set(expose_except)
        if expose is None:
            i_keys = map(lambda x: x.id, new_step.run.inputs)
            o_keys = map(lambda x: x.id, new_step.run.outputs)
            expose = set(itertools.chain(i_keys, o_keys)).difference(
                expose_except
            )
        elif isinstance(expose, dict):
            expose = {
                k: v for k, v in expose.items() if k not in expose_except
            }
        else:
            expose = set(expose).difference(expose_except)

        if isinstance(expose, dict):
            for k, v in expose.items():
                wf_io(new_step, k, id=v)
        else:
            for i in expose:
                wf_io(new_step, i)

        if scatter:
            self.add_requirement(ScatterFeature())
            self.scatter(new_step, scatter, scatter_method)

        return new_step

    # endregion

    # region properties
    @property
    def steps(self):
        """
        The individual steps that make up the wf. Each step is executed
        when all of its input data links are fufilled. An implementation may
        choose to execute the steps in a different order than listed and/or
        execute steps concurrently, provided that dependencies between steps
        are met.
        """
        return self.get('steps')

    @steps.setter
    def steps(self, value):
        self['steps'] = to_steps(value)

    # endregion


@salad
def to_run(value):
    @salad
    def map_dict(d):
        if d['class'] == 'CommandLineTool':
            return CommandLineTool(**d)
        elif d['class'] == 'Workflow':
            return Workflow(**d)
        elif d['class'] == 'ExpressionTool':
            return ExpressionTool(**d)
        else:
            raise ValueError('Unsupported class: {}'.format(d['class']))

    if value is not None:
        if isinstance(value, (str, CommandLineTool, Workflow,
                              ExpressionTool)):
            return value
        elif isinstance(value, dict):
            return map_dict(value)
        else:
            raise TypeError('TypeError, got: {}'.format(type(value)))


@salad
def to_in(value):
    @salad
    def map_to_cls(obj):
        return StepInput(**obj)

    if value is not None:
        if isinstance(value, list):
            return list(map(map_to_cls, value))
        elif isinstance(value, dict):
            in_ = []
            for k, v in value.items():
                if isinstance(v, dict):
                    v = map_to_cls(v)
                else:
                    v = StepInput(id=k, source=v)
                in_.append(v)
            return in_
        else:
            raise TypeError('Unsupported type: {}'.format(type(value)))
    else:
        return []


@salad
def to_out(value):
    @salad
    def map_obj(obj):
        if isinstance(obj, str):
            return obj
        return StepOutput(**obj)

    if value is not None:
        if is_instance_all(value, str, StepOutput):
            return value
        elif is_instance_all(value, dict, str):
            return list(map(map_obj, value))
        else:
            raise TypeError('TypeError, got: {}'.format(type(value)))
    else:
        return []


class Step(Cwl):
    """
    A wf step is an executable element of a wf. It specifies the
    underlying process implementation (such as CommandLineTool or another
    Workflow) in the run field and connects the input and output parameters of
    the underlying process to wf parameters.
    More on http://www.commonwl.org/v1.0/Workflow.html#WorkflowStep
    """

    def __init__(self, id, in_, out, run,
                 requirements=None, hints=None, label=None, doc=None,
                 scatter=None, scatter_method=None):
        super(Step, self).__init__()
        self.id = id
        self.in_ = in_
        self.out = out
        self.run = run
        self.requirements = requirements
        self.hints = hints
        self.label = label
        self.doc = doc
        self.scatter = scatter
        self.scatter_method = scatter_method

    # region utils
    def link_merge(self, id, method=MergeMethod.MERGE_NESTED):
        """Link merge port with ``id`` using ``method``."""

        for i in self.in_:
            if i.id == id:
                i.link_merge = method
                return

    def is_scattered(self, k):
        """Checks if port specified by ``k`` is scattered."""

        if self.scatter == k or k in self.scatter:
            return True
        return False

    # endregion

    # region properties
    @property
    def id(self):
        """The unique identifier for this wf step."""
        return self.get('id')

    @id.setter
    def id(self, value):
        self['id'] = to_str(value)

    @property
    def in_(self):
        """
        Defines the input parameters of the wf step. The process is
        ready to run when all required input parameters are associated with
        concrete values. Input parameters include a schema for each parameter
        which is used to validate the input object. It may also be used build a
        user interface for constructing the input object.
        """
        return self.get('in')

    @in_.setter
    def in_(self, value):
        self['in'] = to_in(value)

    @property
    def out(self):
        """
        Defines the parameters representing the output of the process.
        May be used to generate and/or validate the output object.
        """
        return self.get('out')

    @out.setter
    def out(self, value):
        self['out'] = to_out(value)

    @property
    def run(self):
        """
        Specifies the process to run.
        """
        return self.get('run')

    @run.setter
    def run(self, value):
        self['run'] = to_run(value)

    @property
    def requirements(self):
        """
        Declares requirements that apply to either the runtime environment or
        the wf engine that must be met in order to execute this wf
        step. If an implementation cannot satisfy all requirements, or a
        requirement is listed which is not recognized by the implementation, it
        is a fatal error and the implementation must not attempt to run the
        process, unless overridden at user option.
        """
        return self.get('requirements')

    @requirements.setter
    def requirements(self, value):
        self['requirements'] = to_step_req(value)

    @property
    def hints(self):
        """
        Declares hints applying to either the runtime environment or the
        wf engine that may be helpful in executing this wf step.
        It is not an error if an implementation cannot satisfy all hints,
        however the implementation may report a warning.
        """
        return self.get('hints')

    @hints.setter
    def hints(self, value):
        self['hints'] = to_any(value)

    @property
    def label(self):
        """
        A short, human-readable label of this process object.
        """
        return self.get('label')

    @label.setter
    def label(self, value):
        self['label'] = to_str(value)

    @property
    def doc(self):
        """
        A long, human-readable description of this process object.
        """
        return self.get('doc')

    @doc.setter
    def doc(self, value):
        self['doc'] = to_str(value)

    @property
    def scatter(self):
        """
        The scatter field specifies one or more input parameters which will be
        scattered. An input parameter may be listed more than once.
        The declared type of each input parameter is implicitly becomes an
        array of items of the input parameter type. If a parameter is listed
        more than once, it becomes a nested array. As a result, upstream
        parameters which are connected to scattered parameters must be arrays.
        """
        return self.get('scatter')

    @scatter.setter
    def scatter(self, value):
        self['scatter'] = to_str_slist(value)

    @property
    def scatter_method(self):
        """
        Required if scatter is an array of more than one element.
        """
        return self.get('scatterMethod')

    @scatter_method.setter
    def scatter_method(self, value):
        self['scatterMethod'] = to_str(value)

    # endregion


class StepInput(Cwl):
    """
    The input of a wf step connects an upstream parameter (from the
    wf inputs, or the outputs of other workflows steps) with the input
    parameters of the underlying step.

    Input object

    A WorkflowStepInput object must contain an id field in the form #fieldname
    or #prefix/fieldname. When the id field contains a slash / the field name
    consists of the characters following the final slash (the prefix portion
    may contain one or more slashes to indicate scope). This defines a field of
    the wf step input object with the value of the source parameter(s).

    Merging

    To merge multiple inbound data links, MultipleInputFeatureRequirement must
    be specified in the wf or wf step requirements.

    If the sink parameter is an array, or named in a wf scatter operation,
    there may be multiple inbound data links listed in the source field.
    The values from the input links are merged depending on the method
    specified in the linkMerge field. If not specified, the default method
    is "merge_nested".

        - merge_nested
          The input must be an array consisting of exactly one entry for each
          input link. If "merge_nested" is specified with a single link, the
          value from the link must be wrapped in a single-item list.

        - merge_flattened
          1. The source and sink parameters must be compatible types, or the
          source type must be compatible with single element from the "items"
          type of the destination array parameter.
          2. Source parameters which are arrays are concatenated.
          Source parameters which are single element types are appended
          as single elements.

    """

    def __init__(self, id, source=None, link_merge=None, default=None,
                 value_from=None):
        super(StepInput, self).__init__()
        self.id = id
        self.source = source
        self.link_merge = link_merge
        self.default = default
        self.value_from = value_from

    @property
    def id(self):
        """A unique identifier for this wf input parameter."""
        return self.get('id')

    @id.setter
    def id(self, value):
        self['id'] = to_str(value)

    @property
    def source(self):
        """
        Specifies one or more wf parameters that will provide input to the
        underlying step parameter.
        """
        return self.get('source')

    @source.setter
    def source(self, value):
        self['source'] = to_str_slist(value)

    @property
    def link_merge(self):
        """
        The method to use to merge multiple inbound links into a single array.
        If not specified, the default method is "merge_nested".
        """
        return self.get('linkMerge')

    @link_merge.setter
    def link_merge(self, value):
        self['linkMerge'] = to_str(value)

    @property
    def default(self):
        """
        The default value for this parameter to use if either there is no
        source field, or the value produced by the source is null. The default
        must be applied prior to scattering or evaluating valueFrom.
        """
        return self.get('default')

    @default.setter
    def default(self, value):
        if value is not None:
            self['default'] = to_any(value)

    @property
    def value_from(self):
        """
        To use valueFrom, StepInputExpressionRequirement must be specified in
        the wf or wf step requirements.

        If valueFrom is a constant string value, use this as the value for this
        input parameter.

        If valueFrom is a parameter reference or expression, it must be
        evaluated to yield the actual value to be assiged to the input field.

        The self value of in the parameter reference or expression must be the
        value of the parameter(s) specified in the source field, or null if
        there is no source field.

        The value of inputs in the parameter reference or expression must be
        the input object to the wf step after assigning the source values,
        applying default, and then scattering. The order of evaluating
        valueFrom among step input parameters is undefined and the result of
        evaluating valueFrom on a parameter must not be visible to evaluation
        of valueFrom on other parameters.
        """
        return self.get('valueFrom')

    @value_from.setter
    def value_from(self, value):
        self['valueFrom'] = to_str(value)


class StepOutput(Cwl):
    """
    Associate an output parameter of the underlying process with a wf
    parameter. The wf parameter (given in the id field) be may be used as
    a source to connect with input parameters of other wf steps, or with
    an output parameter of the process.
    """

    def __init__(self, id):
        super(StepOutput, self).__init__()
        self.id = id

    @property
    def id(self):
        """
        A unique identifier for this wf output parameter.
        This is the identifier to use in the source field of WorkflowStepInput
        to connect the output value to downstream parameters.
        """
        return self.get('id')

    @id.setter
    def id(self, value):
        self['id'] = to_str(value)
