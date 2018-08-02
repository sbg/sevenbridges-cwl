__all__ = ['AwsHint', 'SaveLogs', 'SbgFs', 'MaxNumberOfParallelInstances']

from sbg.cwl.sbg.hints.fs import SbgFs
from sbg.cwl.sbg.hints.aws import AwsHint
from sbg.cwl.sbg.hints.logs import SaveLogs
from sbg.cwl.sbg.hints.parallel import MaxNumberOfParallelInstances
