"""ENS160 I2C driver"""

# SPDX-FileCopyrightText: Copyright (c) 2024 Ron Bessems
#
# SPDX-License-Identifier: MIT

# #####################
# ENS160 Python Library
# #####################
#
# datasheet:
# https://www.sciosense.com/wp-content/uploads/2023/12/ENS160-Datasheet.pdf
#
# Tested on RPI 5 with I2C speed 100kHz.
# or example https://www.sparkfun.com/products/20844
#

from enum import IntEnum
import sys
from time import sleep
from smbus2 import SMBus

class ENS160Status:
    """Data Status Structure."""
    def __init__(self, d):
        self.flags = (d & 0x0C) >> 2
        # During first 3 minutes after power-on
        self.warm_up = self.flags == 1
        # During first full hour of operation after initial power-on24.
        self.inital_startup = self.flags == 2
        # Standard operating mode.
        self.normal_operation = self.flags == 0
        # Signals give unexpected values (very high or very low). Multiple sensors out of range.
        self.invalid_data = self.flags == 3
        self.power_on = (d & 0x80) == 0x80
        self.error = (d & 0x40) == 0x40
        self.new_data = (d & 0x02) == 0x02
        self.new_gpr = (d & 0x01) == 0x01

    def __str__(self):
        # pylint: disable=line-too-long
        return f"flags={self.flags}, warm_up={self.warm_up}, inital_startup={self.inital_startup} power on={self.power_on}, error={self.error}, new data={self.new_data}, new gpr={self.new_gpr}"

class Register(IntEnum):
    """ENS160 Register Constants."""
    PART_ID = 0x00  # Device Identity 0x01, 0x60
    OP_MODE = 0x10  # Operating Mode
    CONFIG = 0x11  # Interrupt Pin Configuration
    COMMAND = 0x12  # Additional System Commands, only in idle mode
    TEMP_IN = 0x13  # Host Ambient Temperature Information
    RH_IN = 0x15  # Host Relative Humidity Information
    DEVICE_STATUS = 0x20  # Operating Mode

    DATA_AQI = 0x21  # Air Quality Index
    DATA_TVOC = 0x22  # TVOC Concentration (ppb)
    DATA_ECO2 = 0x24  # Equivalent CO2 Concentration (ppm)

    DATA_T = 0x30  # Temperature used in calculations
    DATA_RH = 0x32  # Relative Humidity used in calculations

    DATA_MISR = 0x38  # Data Integrity Field (optional)

    GPR_WRITE = 0x40  # 8 bytes of General Purpose Write Registers
    GRP_READ0 = 0x48  # 1 byte s of General Purpose Read Registers
    GRP_READ1 = 0x49  # 1 byte s of General Purpose Read Registers
    GRP_READ2 = 0x4A  # 1 byte s of General Purpose Read Registers
    GRP_READ3 = 0x4B  # 1 byte s of General Purpose Read Registers
    GRP_READ4 = 0x4C  # 1 byte s of General Purpose Read Registers
    GRP_READ5 = 0x4D  # 1 byte s of General Purpose Read Registers
    GRP_READ6 = 0x4E  # 1 byte s of General Purpose Read Registers
    GRP_READ7 = 0x4F  # 1 byte s of General Purpose Read Registers


class OpMode(IntEnum):
    """Operation Mode Constants."""
    DEEP_SLEEP = 0x00  # only responds to OP_MODE write
    IDLE = 0x01  # accepting commands
    STANDARD = 0x02  # Gas Sensing
    RESET = 0xF0  # Reset the unit.


class Commands(IntEnum):
    """Command Constants."""
    NOP = 0x00  # nop
    GET_FW_VER = 0x0E  # Get firmware version
    CLEAR_GPR_READ = 0xCC  # Clear


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

    def write(self, register: Register, data: list[int] | int):
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

    def read(self, register: Register, size: int):
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


class ENS160:
    """ENS160 TOV Sensor driver."""

    PART_ID = 0x160

    # Possible Addresses [0x52, 0x53]
    def __init__(self, address: int, interface_id: int = 1):
        self.i2c = RetryingI2C(address, interface_id)
        self.address = address

    def set_operating_mode(self, mode: OpMode):
        """Sets the ENS160 operation mode. Returns True on success."""
        self.i2c.write(Register.OP_MODE, mode)

    def get_operating_mode(self) -> OpMode:
        """Returns one of the ENS160_OP_MODE values."""
        return self.i2c.read(Register.OP_MODE, 1)

    def get_part_id(self) -> int:
        """ Gets the part id. Expecting 0x0160."""
        byte_values = self.i2c.read(Register.PART_ID, 2)
        return byte_values[0] + (byte_values[1] << 8)

    def clear_gp_read_flag(self):
        """Clears the General Purpose Read bit."""
        # this command appears to not work.
        # self.i2c.write(Register.COMMAND, Commands.CLEAR_GPR_READ)

        # just read anything to clear the flag.
        self.i2c.read(Register.GRP_READ4, 3)

    def get_fw_version(self) -> str:
        """Returns firmware version, mine is 5.4.6."""
        self.i2c.write(Register.COMMAND, Commands.GET_FW_VER)
        while True:
            status = self.get_device_status()
            if status.new_gpr:
                break
            sleep(0.001)
        byte_data = self.i2c.read(Register.GRP_READ4, 3)
        return f"{byte_data[0]}.{byte_data[1]}.{byte_data[2]}"

    def set_temp_compensation_kelvin(self, t_in_kelvin: float):
        """Set temperature compensation before reading data, otherwise you get zeros."""
        param: int = round(t_in_kelvin * 64)
        params: list[int] = []
        params.append(param & 0x00FF)
        params.append((param & 0xFF00) >> 8)
        self.i2c.write(Register.TEMP_IN, params)

    def set_temp_compensation_celcius(self, t_in_celcius: float):
        """Set temperature compensation before reading data, otherwise you get zeros."""
        self.set_temp_compensation_kelvin(t_in_celcius + 273.15)

    def set_temp_compensation_fahrenheit(self, t_in_fahrenheit: float):
        """Set temperature compensation before reading data, otherwise you get zeros."""
        self.set_temp_compensation_celcius((t_in_fahrenheit - 32.0) * 5.0 / 9.0)

    def set_rh_compensation(self, relative_humidity: float):
        """Set humidity compensation before reading data, otherwise you get zeros."""
        param: int = round(relative_humidity * 512)
        params: list[int] = []
        params.append(param & 0x00FF)
        params.append((param & 0xFF00) >> 8)
        self.i2c.write(Register.RH_IN, params)

    def get_device_status(self) -> ENS160Status:
        """Get the device status."""
        return ENS160Status(self.i2c.read(Register.DEVICE_STATUS, 1))

    def get_aqi(self) -> int:
        """Get the Air Quality index 1,2,3,4 or 5, with 1 being great and 5 being worst."""
        return self.i2c.read(Register.DATA_AQI, 1) & 0x07

    def get_tvoc(self) -> int:
        """Get the Total Volatile Organic compounds in the air in ppb."""
        byte_values = self.i2c.read(Register.DATA_TVOC, 2)
        return byte_values[0] + (byte_values[1] << 8)

    def get_eco2(self) -> int:
        """Get the eCO2 levels in the air in ppm."""
        byte_values = self.i2c.read(Register.DATA_ECO2, 2)
        return byte_values[0] + (byte_values[1] << 8)

    def reset(self):
        """Reset the unit."""
        self.set_operating_mode(OpMode.RESET)
        i = 25
        while i > 0:
            m = self.get_operating_mode()
            if m == 0:
                self.clear_gp_read_flag()
                return True
            sleep(0.01)
        return False

    def init(self):
        """Reset and set operating mode to IDLE."""
        self.reset()
        self.set_operating_mode(OpMode.IDLE)


def __example_run():
    """Code usage sample."""
    dev = ENS160(0x53)
    dev.init()
    part_id = dev.get_part_id()
    if part_id != ENS160.PART_ID:
        print(f"Part not found, expected {ENS160.PART_ID} got {part_id}.")
        sys.exit(-1)

    print(f"Part Id {part_id}")
    print(f"Firmware version {dev.get_fw_version()}")

    dev.set_rh_compensation(55.0)
    dev.set_temp_compensation_fahrenheit(72.5)

    print(dev.get_device_status())

    dev.set_operating_mode(OpMode.STANDARD)
    print(dev.get_operating_mode())

    while True:
        status = dev.get_device_status()
        print(status)
        if status.new_data:
            print(
                f"AQI={dev.get_aqi()}, eCO2={dev.get_eco2()}ppm, TVOC={dev.get_tvoc()}ppb"
            )
        else:
            sleep(1)

if __name__ == "__main__":
    __example_run()
