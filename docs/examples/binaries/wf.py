from sbg import cwl

with cwl.workflow('wf.cwl', 'w') as w:

    #  load tools from CWL file
    tool1 = cwl.load('tool1.cwl')
    tool2 = cwl.load('tool2.cwl')

    #  add wf steps
    w.add_step(tool1, expose=['inFile', 'pattern'])
    w.add_step(tool2, expose=['count'])

    #  set connections
    w.add_connection('{}.out'.format(tool1.id), '{}.inFile'.format(tool2.id))
