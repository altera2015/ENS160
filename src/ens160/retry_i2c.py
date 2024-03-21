"""I2C Retry wrapper."""

from time import sleep

from smbus2 import SMBus
from .enumerations import Registers


class RetryingI2C:
    """I2C Helper class that automatically retries."""
    def __init__(
        self,
        address: int,
        interface_id: int,
        retries: int = 5,
        retry_sleep: float = 0.01,
    ):
        self.__i2c = SMBus(interface_id)
        self.__address = address
        self.__retries = retries
        self.__retry_sleep = retry_sleep

    def write(self, register: Registers, data: list[int] | int):
        """Write data to the I2C bu.s"""
        retries = self.__retries
        while True:
            try:
                if isinstance(data, int):
                    self.__i2c.write_byte_data(self.__address, register, data)
                else:
                    self.__i2c.write_i2c_block_data(self.__address, register, data)
                return
            except OSError as e:
                retries -= 1
                if retries < 0:
                    raise e
                sleep(self.__retry_sleep)

    def read(self, register: Registers, size: int):
        """Read data from the I2C bus."""
        retries = self.__retries
        while True:
            try:
                if size == 1:
                    return self.__i2c.read_byte_data(self.__address, register)
                return self.__i2c.read_i2c_block_data(self.__address, register, size)
            except OSError as e:
                retries -= 1
                if retries < 0:
                    raise e
                sleep(self.__retry_sleep)