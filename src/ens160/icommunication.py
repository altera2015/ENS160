"""Interface for communications classes"""

from .enumerations import Registers

class ICommunication:
    """Interface class for Communication classes."""

    def write(self, register: Registers, data: list[int] | int):
        """Write byte data to register."""
        raise NotImplementedError

    def read(self, register: Registers, size: int):
        """Read byte data from register."""
        raise NotImplementedError
