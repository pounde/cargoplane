import sky


class CargoPlane:
    def __init__(
        self,
        image: str,
        resources: dict = None,
        file_mounts: dict = None,
        container_mounts: dict = None,
        setup: str = None,
        entrypoint: str = None,
        args: iter = None,
        docker_flags: iter = None,
        cleanup: str = None,
        use_spot: bool = True,
        down: bool = True,  # Todo: test that if use_spot is true down and warn that 'down' is not relevant
    ):
        """
        Class to build docker run command.
        Args:
            image (str): Docker image to run. No authentication in handled. If authentication is required, that should be passed in 'setup' command.
            resources (dict, optional): SkyPilot resources required. Normally used to allocate GPU's to instance. Defaults to None.
            file_mounts (dict, optional): SkyPilot mounts for remote instance. Defaults to None.
            container_mounts (dict, optional): Mounts from remote instance to Docker container. Defaults to None.
            setup (str, optional): Command to run on remote instance prior to launching Docker container. Defaults to None.
            entrypoint (str, optional): Docker image entrypoint override, passed to 'docker run' with '--entrypoint'. Defaults to None.
            args (iter, optional): Arguments to pass to docker application. Defaults to None.
            docker_flags (iter, optional): Additional flags to pass to docker. Defaults to None.
            cleanup (str, optional): Command(s) to run after Docker container exits. Multiple commands can be passed by separating them with '&&'. Defaults to None.
            use_spot (bool, optional): Use spot instance. Defaults to True.
            down (bool, optional): Shutdown instance after Docker container exits. Defaults to True.

        Raises:
            ValueError: _description_
        """
        self.image = image
        self.entrypoint = entrypoint
        self.resources = resources
        self.file_mounts = file_mounts
        self.container_mounts = [
            f"-v {k}:{v}" for k, v in container_mounts.items()
        ] if container_mounts else None  # Todo: maybe abstract this ie {container_mnt: {instance_mnt: {'source': s3-bucket}}}
        self.setup = setup
        self.args = args  # Todo: add ability to pass iterable or string
        self.docker_flags = docker_flags
        self.cleanup = cleanup  # Todo: add ability to pass iterable or string
        self.use_spot = use_spot
        self.down = down
        self.cmd = self._gen_cmd()

        # if entrypoint contains white space it will be interpreted as the image
        if self.entrypoint and self.entrypoint.__contains__(" "):
            raise ValueError("Entrypoint cannot contain whitespace.")

    def _gen_cmd(self):
        cmd = "docker run "
        cmd += f'{" ".join(self.docker_flags)} ' if self.docker_flags else ""
        cmd += f'{" ".join(self.container_mounts)} ' if self.container_mounts else ""
        cmd += f"--entrypoint {self.entrypoint} " if self.entrypoint else ""
        cmd += f"{self.image} "
        cmd += " ".join(self.args) if self.args else ""
        cmd += f" && {self.cleanup}" if self.cleanup else ""
        return cmd.strip()

    def run(self):
        """Runs Docker image on SkyPilot
        """

        docker_run = sky.Task(setup=self.setup, run=self.cmd)

        if self.file_mounts:
            docker_run.set_storage_mounts(
                {
                    k: sky.Storage(source=v.get("source"))
                    for k, v in self.file_mounts.items()
                }
            )

        # Set resources if required
        if self.resources:
            docker_run.set_resources(
                sky.Resources.from_yaml_config(self.resources),
            )

        if self.use_spot:
            sky.spot_launch(
                docker_run,
            )
        else:
            sky.launch(docker_run, down=self.down)
