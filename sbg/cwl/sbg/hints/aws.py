from sbg.cwl.sbg.hints.hint import Hint


class AwsInstance(object):
    def __init__(self, name, cores, ram, storage):
        self.name = name
        self.cores = cores
        self.ram = ram
        self.storage = storage
        self._name = None
        self._cores = None
        self._ram = None
        self._storage = None

    @property
    def name(self):
        """AWS instance name"""

        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def cores(self):
        """Number of cores available on instance"""

        return self._cores

    @cores.setter
    def cores(self, value):
        self._cores = value

    @property
    def ram(self):
        """RAM [GB] available on instance"""

        return self._ram

    @ram.setter
    def ram(self, value):
        self._ram = value

    @property
    def storage(self):
        """Storage [GB] available on instance"""

        return self._storage

    @storage.setter
    def storage(self, value):
        self._storage = value

    def __repr__(self):
        return "<AwsInstance name={}, cores={}, ram={}, storage={}>".format(
            self.name, self.cores, self.ram, self.storage
        )

    def __eq__(self, other):
        return isinstance(other, AwsInstance) and self.name == other.name

    def __hash__(self):
        return hash((self.name, self.cores, self.ram, self.storage,))


class AwsHint(Hint):
    class_ = 'sbg:AWSInstanceType'

    def __init__(self, instance=None, storage=None, value=None):
        """
        Configures the type of all the AWS instances provisioned for this
        workflow/node/tool.
        Priority: workflow > node > tool

        :param instance: instance name (eg. `'c3.8xlarge'`)
        :param storage: storage size
        :param value: instance name + storage size
        :param class_: always `sbg:AWSInstanceType`
        """
        super(AwsHint, self).__init__()
        self['class'] = self.class_
        if value:
            self.value = value
        else:
            if storage and (not isinstance(storage, int) or storage < 2):
                raise ValueError(
                    'Storage have to be int greater than 1.'
                )

            if instance:
                self.value = "{val}".format(
                    val=instance.split(';')[0],
                )
            else:
                self.value = "{val};ebs-gp2;{store}".format(
                    val=instance.split(';')[0],
                    store=instance
                )

    @property
    def value(self):
        """AWS instance value"""

        return self.get('value')

    @value.setter
    def value(self, value):
        self['value'] = value
