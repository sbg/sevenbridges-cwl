from sbg.cwl.v1_0.base import Cwl
from sbg.cwl.v1_0.check import to_str


class Docker(Cwl):
    """
    Indicates that a wf component should be run in a Docker container,
    and specifies how to fetch or build the image.

    If a CommandLineTool lists DockerRequirement under hints (or requirements),
    it may (or must) be run in the specified Docker container.

    The platform must first acquire or install the correct Docker image as
    specified by dockerPull, dockerImport, dockerLoad or dockerFile.

    The platform must execute the tool in the container using docker run with
    the appropriate Docker image and tool command line.

    The wf platform may provide input files and the designated output
    directory through the use of volume bind mounts. The platform may rewrite
    file paths in the input object to correspond to the Docker bind mounted
    locations.

    When running a tool contained in Docker, the wf platform must not
    assume anything about the contents of the Docker container, such as the
    presence or absence of specific software, except to assume that the
    generated command line represents a valid command within the runtime
    environment of the container.

    Interaction with other requirements

    If EnvVarRequirement is specified alongside a DockerRequirement,
    the environment variables must be provided to Docker using --env or
    --env-file and interact with the container's preexisting environment as
    defined by Docker.
    """
    class_ = 'DockerRequirement'

    def __init__(self, docker_pull=None,
                 docker_load=None, docker_file=None, docker_import=None,
                 docker_image_id=None, docker_output_directory=None):
        super(Docker, self).__init__()
        self['class'] = self.class_
        self.docker_pull = docker_pull
        self.docker_load = docker_load
        self.docker_file = docker_file
        self.docker_import = docker_import
        self.docker_image_id = docker_image_id
        self.docker_output_directory = docker_output_directory

    @property
    def docker_pull(self):
        """
        Specify a Docker image to retrieve using docker pull.
        """
        return self.get('dockerPull')

    @docker_pull.setter
    def docker_pull(self, value):
        self['dockerPull'] = to_str(value)

    @property
    def docker_load(self):
        """
        Specify a HTTP URL from which to download a Docker image using docker
        load.
        """
        return self.get('dockerLoad')

    @docker_load.setter
    def docker_load(self, value):
        self['dockerLoad'] = to_str(value)

    @property
    def docker_file(self):
        """
        Supply the contents of a Dockerfile which will be built using docker
        build.
        """
        return self.get('dockerFile')

    @docker_file.setter
    def docker_file(self, value):
        self['dockerFile'] = to_str(value)

    @property
    def docker_import(self):
        """
        Provide HTTP URL to download and gunzip a Docker images using docker
        import.
        """
        return self.get('dockerImport')

    @docker_import.setter
    def docker_import(self, value):
        self['dockerImport'] = to_str(value)

    @property
    def docker_image_id(self):
        """
        The image id that will be used for docker run. May be a human-readable
        image name or the image identifier hash. May be skipped if dockerPull
        is specified, in which case the dockerPull image id must be used.
        """
        return self.get('dockerImageId')

    @docker_image_id.setter
    def docker_image_id(self, value):
        self['dockerImageId'] = to_str(value)

    @property
    def docker_output_directory(self):
        """
        Set the designated output directory to a specific location inside the
        Docker container.
        """
        return self.get('dockerOutputDirectory')

    @docker_output_directory.setter
    def docker_output_directory(self, value):
        self['dockerOutputDirectory'] = to_str(value)
