import abc


class Plugin(object):
    @abc.abstractmethod
    def can_serialize(self, obj):
        raise NotImplementedError()

    @abc.abstractmethod
    def serialize(self, context, name, obj):
        raise NotImplementedError()
