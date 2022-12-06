import pytest
from cargoplane import CargoPlane


class TestCargoPlane:
    def test_cargo_plane(self):
        test = CargoPlane("test")
        assert test.cmd == "docker run test"