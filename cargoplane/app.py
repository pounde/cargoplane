import sky


# TODO: this should also support compose


class CargoPlane:
    def __init__(
        self,
        image: str,
        resources: dict = None,
        file_mounts: dict = None,
        storage_mounts: dict = None,
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
            args (iter, optional): Arguments to pass to docker entrypoint. Defaults to None.
            docker_flags (iter, optional): Additional flags to pass to docker. Defaults to None.
            cleanup (str, optional): Command(s) to run after Docker container exits. Multiple commands can be passed by separating them with '&&'. Defaults to None.
            use_spot (bool, optional): Use spot instance. Defaults to True.
            down (bool, optional): Shutdown instance after Docker container exits. Defaults to True.

        Raises:
            ValueError: _description_
        """

        self.cmd = self.gen_cmd(
            image, container_mounts, entrypoint, args, docker_flags, cleanup
        )
        self.task = self.gen_task(
            setup, self.cmd, file_mounts, storage_mounts, resources
        )
        self.use_spot = use_spot
        self.down = down

    @staticmethod
    def gen_task(setup, cmd, file_mounts, storage_mounts, resources):
        # set-up SkyPilot task
        task = sky.Task(setup=setup, run=cmd)
        if file_mounts:
            task.set_file_mounts(file_mounts)

        if storage_mounts:
            task.set_storage_mounts(
                {k: sky.Storage(**v) for k, v in storage_mounts.items()}
            )

        if resources:
            task.set_resources(
                sky.Resources.from_yaml_config(resources),
            )

        return task

    @staticmethod
    def gen_cmd(image, container_mounts, entrypoint, args, docker_flags, cleanup):

        # if entrypoint contains white space it will be interpreted as the image
        if entrypoint and entrypoint.__contains__(" "):
            raise ValueError("Entrypoint cannot contain whitespace.")

        container_mounts = (
            [f"-v {k}:{v}" for k, v in container_mounts.items()]
            if container_mounts
            else None
        )
        cmd = "docker run "
        cmd += f'{" ".join(docker_flags)} ' if docker_flags else ""
        cmd += f'{" ".join(container_mounts)} ' if container_mounts else ""
        cmd += f"--entrypoint {entrypoint} " if entrypoint else ""
        cmd += f"{image} "
        cmd += (
            " ".join(args) if args else ""
        )  # Todo: add ability to pass iterable or string
        cmd += (
            f" && {cleanup}" if cleanup else ""
        )  # Todo: add ability to pass iterable or string

        return cmd.strip()

    def run(self):
        """Runs Docker image on SkyPilot"""

        if self.use_spot:
            sky.spot_launch(
                self.task,
            )
        else:
            sky.launch(self.task, down=self.down)
