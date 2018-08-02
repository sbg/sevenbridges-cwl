__all__ = ['plugins', 'Plugin', 'ToolzPlugin']

from sbg.cwl.serialize.plugins.base import Plugin
from sbg.cwl.serialize.plugins.toolz import ToolzPlugin


plugins = [p() for p in Plugin.__subclasses__()]
