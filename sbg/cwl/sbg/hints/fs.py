from sbg.cwl.sbg.hints.hint import Hint


class SbgFs(Hint):
    class_ = "sbg:useSbgFS"
    ALLOWED_VALUES = {
        True: 'true',
        False: 'false'
    }

    def __init__(self, value):
        """
        Hint for using SbgFS.

        :param value: can be either `True` or `False`
        """

        super(SbgFs, self).__init__()
        self['class'] = self.class_
        self.value = value

    @property
    def value(self):
        """SBG Fs value"""
        return self['value']

    @value.setter
    def value(self, value):
        v = SbgFs.ALLOWED_VALUES.get(value)
        if v:
            self['value'] = v
        else:
            raise ValueError(
                'Expected bool, but got: {}'.format(type(value))
            )
