from sbg import cwl

with cwl.tool('tool1.cwl', 'w') as t:
    t.id = 'tool1'
    t.base_command = ['grep']
    t.stdout = '_output_'
    t.add_input(
        cwl.String(required=True),
        'pattern',
        label='pattern',
        input_binding=cwl.InputBinding(
            shell_quote=False,
            position=0
        )
    )

    t.add_input(
        cwl.File(required=True),
        'inFile',
        label='inFile',
        input_binding=cwl.InputBinding(
            shell_quote=False,
            position=1
        )
    )

    t.add_output(
        cwl.File(required=True),
        'out',
        label='Out',
        output_binding=cwl.OutputBinding(glob='_output_')
    )

    t.add_requirement(cwl.Docker(docker_pull='ubuntu:16.04'))
    # required if we want to disable shell_quote
    t.add_requirement(cwl.ShellCommand())
