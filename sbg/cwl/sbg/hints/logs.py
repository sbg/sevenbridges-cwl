from sbg.cwl.sbg.hints.hint import Hint


class SaveLogs(Hint):
    class_ = "sbg:SaveLogs"

    def __init__(self, value):
        """
        Configures the additional files to preserve as logs inside the project.

        :param value: regular expression for pattern matching to set
                      which files will be caught as log files
        """
        super(SaveLogs, self).__init__()
        self['class'] = self.class_
        self.value = value

    @property
    def value(self):
        """SBG SaveLogs value"""
        return self['value']

    @value.setter
    def value(self, value):
        self['value'] = value
