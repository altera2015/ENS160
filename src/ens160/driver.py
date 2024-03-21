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

from time import sleep
from .retry_i2c import RetryingI2C
from .enumerations import OpModes, Commands, Registers
from .status import Status

class Driver:
    """ENS160 TOV Sensor driver."""
    PART_ID = 0x160

    def __init__(self, address: int, interface_id: int = 1):
        """Initialize the driver, possible Addresses: 0x52 or 0x53."""
        self.i2c = RetryingI2C(address, interface_id)
        self.address = address

    def set_operating_mode(self, mode: OpModes):
        """Sets the ENS160 operation mode. Returns True on success."""
        self.i2c.write(Registers.OP_MODE, mode)

    def get_operating_mode(self) -> OpModes:
        """Returns one of the ENS160_OP_MODE values."""
        return self.i2c.read(Registers.OP_MODE, 1)

    def get_part_id(self) -> int:
        """ Gets the part id. Expecting 0x0160."""
        byte_values = self.i2c.read(Registers.PART_ID, 2)
        return byte_values[0] + (byte_values[1] << 8)

    def clear_gp_read_flag(self):
        """Clears the General Purpose Read bit."""
        # this command appears to not work.
        # self.i2c.write(Register.COMMAND, Commands.CLEAR_GPR_READ)

        # just read anything to clear the flag.
        self.i2c.read(Registers.GRP_READ4, 3)

    def get_fw_version(self) -> str:
        """Returns firmware version, mine is 5.4.6."""
        self.i2c.write(Registers.COMMAND, Commands.GET_FW_VER)
        while True:
            status = self.get_device_status()
            if status.new_gpr:
                break
            sleep(0.001)
        byte_data = self.i2c.read(Registers.GRP_READ4, 3)
        return f"{byte_data[0]}.{byte_data[1]}.{byte_data[2]}"

    def set_temp_compensation_kelvin(self, t_in_kelvin: float):
        """Set temperature compensation before reading data, otherwise you get zeros."""
        param: int = round(t_in_kelvin * 64)
        params: list[int] = []
        params.append(param & 0x00FF)
        params.append((param & 0xFF00) >> 8)
        self.i2c.write(Registers.TEMP_IN, params)

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
        self.i2c.write(Registers.RH_IN, params)

    def get_device_status(self) -> Status:
        """Get the device status."""
        return Status(self.i2c.read(Registers.DEVICE_STATUS, 1))

    def get_aqi(self) -> int:
        """Get the Air Quality index 1,2,3,4 or 5, with 1 being great and 5 being worst."""
        return self.i2c.read(Registers.DATA_AQI, 1) & 0x07

    def get_tvoc(self) -> int:
        """Get the Total Volatile Organic compounds in the air in ppb."""
        byte_values = self.i2c.read(Registers.DATA_TVOC, 2)
        return byte_values[0] + (byte_values[1] << 8)

    def get_eco2(self) -> int:
        """Get the eCO2 levels in the air in ppm."""
        byte_values = self.i2c.read(Registers.DATA_ECO2, 2)
        return byte_values[0] + (byte_values[1] << 8)

    def reset(self):
        """Reset the unit."""
        self.set_operating_mode(OpModes.RESET)
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
        self.set_operating_mode(OpModes.IDLE)
