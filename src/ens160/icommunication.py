"""Interface for communications classes"""

from .registers import Registers

# pylint: disable-next=missing-class-docstring
class ICommunication:
    def write(self, register: Registers, data: list[int] | int):
        """Write byte data to register."""
        raise NotImplementedError

    def read(self, register: Registers, size: int):
        """Read byte data from register."""
        raise NotImplementedError
