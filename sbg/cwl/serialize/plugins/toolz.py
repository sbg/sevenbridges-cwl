from sbg.cwl.serialize.plugins.base import Plugin


class ToolzPlugin(Plugin):
    def can_serialize(self, obj):
        return (
            hasattr(obj, '__class__') and
            '{0.__module__}.{0.__name__}'.format(obj.__class__) in (
                'toolz.functoolz.curry', 'cytoolz.functoolz.curry'
            )
        )

    def serialize(self, context, name, obj):
        context.add(name, obj.func)
