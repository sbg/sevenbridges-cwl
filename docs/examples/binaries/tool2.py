from sbg import cwl

with cwl.tool('tool2.cwl', 'w') as t:
    t.id = 'tool2'
    t.base_command = ['cat']
    t.arguments = [
        cwl.InputBinding(
            value_from="| wc -l > out.txt",
            shell_quote=False,
            position=2
        )
    ]

    t.add_input(
        cwl.File(required=True),
        'inFile',
        label='inFile',
        stage=True,
        input_binding=cwl.InputBinding(
            shell_quote=False,
            position=1
        )
    )

    t.add_output(
        cwl.Int(required=True),
        'count',
        label='count',
        output_binding=cwl.OutputBinding(
            glob="out.txt",
            load_contents=True,
            output_eval="$(parseInt(self[0].contents))"
        )
    )

    t.add_requirement(cwl.Docker(docker_pull='ubuntu:16.04'))
    t.add_requirement(cwl.ShellCommand())
    # required for js expression evaluation
    t.add_requirement(cwl.InlineJavascript())
