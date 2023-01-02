import pytest
from cargoplane import CargoPlane


class TestCargoPlane:
    test_data = [
        # ("image", "container_mounts", "entrypoint", "args", "docker_flags", "cleanup", "expected"),
        ("test", None, None, None, None, None, "docker run test"),
        (
            "test",
            None,
            "entry_ovrd",
            None,
            None,
            None,
            "docker run --entrypoint entry_ovrd test",
        ),
    ]

    @pytest.mark.parametrize(
        "image,container_mounts,entrypoint,args,docker_flags,cleanup,expected",
        test_data,
    )
    def test_gen_cmd(
        self, image, container_mounts, entrypoint, args, docker_flags, cleanup, expected
    ):
        test = CargoPlane.gen_cmd(
            image, container_mounts, entrypoint, args, docker_flags, cleanup
        )
        assert test == expected
