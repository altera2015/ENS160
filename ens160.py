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

from smbus2 import SMBus
from time import sleep
from enum import IntEnum

class ENS160Status:
    def __init__(self, d):
        self.flags = (d&0x0c) >> 2
        self.warm_up = self.flags == 1          # During first 3 minutes after power-on
        self.inital_startup = self.flags == 2   # During first full hour of operation after initial power-on24. Only once in the sensor’s lifetime
        self.normal_operation = self.flags == 0 # Standard operating mode.
        self.invalid_data = self.flags == 3     # Signals give unexpected values (very high or very low). Multiple sensors out of range.
        self.power_on = (d&0x80)==0x80
        self.error = (d&0x40)==0x40
        self.new_data = (d&0x02) == 0x02
        self.new_gpr = (d&0x01)==0x01

    def __str__(self):
        return f"flags={self.flags}, warm_up={self.warm_up}, inital_startup={self.inital_startup} power on={self.power_on}, error={self.error}, new data={self.new_data}, new gpr={self.new_gpr}"

class Register(IntEnum):
    PART_ID = 0x00       # Device Identity 0x01, 0x60
    OP_MODE = 0x10       # Operating Mode
    CONFIG = 0x11        # Interrupt Pin Configuration
    COMMAND = 0x12       # Additional System Commands, only in idle mode
    TEMP_IN = 0x13       # Host Ambient Temperature Information
    RH_IN = 0x15         # Host Relative Humidity Information
    DEVICE_STATUS = 0x20 # Operating Mode

    DATA_AQI = 0x21      # Air Quality Index
    DATA_TVOC = 0x22     # TVOC Concentration (ppb)
    DATA_ECO2 = 0x24     # Equivalent CO2 Concentration (ppm)

    DATA_T = 0x30        # Temperature used in calculations
    DATA_RH = 0x32       # Relative Humidity used in calculations

    DATA_MISR = 0x38     # Data Integrity Field (optional)

    GPR_WRITE = 0x40     # 8 bytes of General Purpose Write Registers
    GRP_READ0 = 0x48     # 1 byte s of General Purpose Read Registers
    GRP_READ1 = 0x49     # 1 byte s of General Purpose Read Registers
    GRP_READ2 = 0x4a     # 1 byte s of General Purpose Read Registers
    GRP_READ3 = 0x4b     # 1 byte s of General Purpose Read Registers
    GRP_READ4 = 0x4c     # 1 byte s of General Purpose Read Registers
    GRP_READ5 = 0x4d     # 1 byte s of General Purpose Read Registers
    GRP_READ6 = 0x4e     # 1 byte s of General Purpose Read Registers
    GRP_READ7 = 0x4f     # 1 byte s of General Purpose Read Registers

class OpMode(IntEnum):
    DEEP_SLEEP = 0x00    # only responds to OP_MODE write
    IDLE = 0x01          # accepting commands
    STANDARD = 0x02      # Gas Sensing
    RESET = 0xf0         # Reset the unit.

class Commands(IntEnum):
    NOP = 0x00           # nop
    GET_FW_VER = 0x0e    # Get firmware version
    CLEAR_GPR_READ = 0xcc # Clear

class RetryingI2C:

    def __init__(self, address:int, interface_id:int, retries:int = 5, retry_sleep:float=0.01):
        self.__i2c = SMBus(interface_id)
        self.__address = address
        self.__retries = retries
        self.__retry_sleep = retry_sleep

    def write(self, register: Register, data: list[int] | int):
        retries = self.__retries
        while (True):
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
                else:
                    sleep(self.__retry_sleep)

    def read(self, register: Register, size: int):
        retries = self.__retries
        while (True):
            try:
                if size == 1:
                    return self.__i2c.read_byte_data(self.__address, register)
                else:
                    return self.__i2c.read_i2c_block_data(self.__address, register, size)
                return
            except OSError as e:
                retries -= 1
                if retries < 0:
                    raise e
                else:
                    sleep(self.__retry_sleep)

class ENS160:

    PART_ID = 0x160

    # Possible Addresses [0x52, 0x53]
    def __init__(self, address: int, interface_id:int=1):
        self.i2c = RetryingI2C(address, interface_id)
        self.address = address

    '''returns True on success'''
    def set_operating_mode(self, mode: OpMode):
        self.i2c.write(Register.OP_MODE, mode)

    '''returns one of the ENS160_OP_MODE values'''
    def get_operating_mode(self) -> OpMode:
        return self.i2c.read(Register.OP_MODE, 1)

    ''' expecting 0x0160'''
    def get_part_id(self) -> int:
        byte_values = self.i2c.read(Register.PART_ID, 2)
        return byte_values[0] + (byte_values[1] << 8)

    '''Clears the General Purpose Read bit'''
    def clear_gp_read_flag(self):
        # this command appears to not work.
        # self.i2c.write(Register.COMMAND, Commands.CLEAR_GPR_READ)

        # just read anything to clear the flag.
        self.i2c.read(Register.GRP_READ4, 3)

    '''Returns firmware version, mine is 5.4.6'''
    def get_fw_version(self) -> str:
        self.i2c.write(Register.COMMAND, Commands.GET_FW_VER)
        while(True):
            status = self.get_device_status()
            if status.new_gpr:
                break
            sleep(0.001)
        bytes = self.i2c.read(Register.GRP_READ4, 3)
        return f"{bytes[0]}.{bytes[1]}.{bytes[2]}"

    '''Set temperature compensation before reading data, otherwise you get zeros'''
    def set_temp_compensation_kelvin(self, t_in_kelvin: float):
        param:int = round(t_in_kelvin * 64)
        params:list[int] = []
        params.append(param & 0x00FF)
        params.append((param & 0xFF00) >> 8)
        self.i2c.write(Register.TEMP_IN, params)

    '''Set temperature compensation before reading data, otherwise you get zeros'''
    def set_temp_compensation_celcius(self, t_in_celcius: float):
        self.set_temp_compensation_kelvin(t_in_celcius + 273.15)

    '''Set temperature compensation before reading data, otherwise you get zeros'''
    def set_temp_compensation_fahrenheit(self, t_in_fahrenheit: float):
        self.set_temp_compensation_celcius( (t_in_fahrenheit-32.0) * 5.0 / 9.0 )

    '''Set humidity compensation before reading data, otherwise you get zeros'''
    def set_rh_compensation(self, relative_humidity:float):
        param:int = round(relative_humidity * 512)
        params:list[int] = []
        params.append(param & 0x00FF)
        params.append((param & 0xFF00) >> 8)
        self.i2c.write(Register.RH_IN, params)

    '''Get the device status'''
    def get_device_status(self) -> ENS160Status:
        return ENS160Status(self.i2c.read(Register.DEVICE_STATUS, 1))

    '''Get the Air Quality index 1,2,3,4 or 5, with 1 being great and 5 being worst.'''
    def get_aqi(self) -> int:
        return self.i2c.read(Register.DATA_AQI, 1) & 0x07

    '''Get the Total Volatile Organic compounds in the air in ppb'''
    def get_tvoc(self) -> int:
        byte_values = self.i2c.read(Register.DATA_TVOC, 2)
        return byte_values[0] + (byte_values[1] << 8)

    '''Get the eCO2 levels in the air in ppm'''
    def get_eco2(self) -> int:
        byte_values = self.i2c.read(Register.DATA_ECO2, 2)
        return byte_values[0] + (byte_values[1] << 8)

    '''Reset the unit'''
    def reset(self):
        self.set_operating_mode(OpMode.RESET)
        i=25
        while(i>0):
            m = self.get_operating_mode()
            if m == 0:
                self.clear_gp_read_flag()
                return True
            sleep(0.01)
        return False

    '''Reset and set operating mode to IDLE'''
    def init(self):
        self.reset()
        self.set_operating_mode(OpMode.IDLE)

if __name__ == "__main__":
    dev = ENS160(0x53)
    dev.init()
    part_id = dev.get_part_id()
    if part_id != ENS160.PART_ID:
        print(f"Part not found, expected {ENS160.PART_ID} got {part_id}.")
        exit(-1)

    print(f"Part Id {part_id}")
    print(f"Firmware version {dev.get_fw_version()}")

    dev.set_rh_compensation(55.0)
    dev.set_temp_compensation_fahrenheit(72.5)

    print(dev.get_device_status())

    dev.set_operating_mode(OpMode.STANDARD)
    print(dev.get_operating_mode())

    while(True):
        status = dev.get_device_status()
        print(status)
        if status.new_data:
            print(f"AQI={dev.get_aqi()}, eCO2={dev.get_eco2()}ppm, TVOC={dev.get_tvoc()}ppb")
        else:
            sleep(1)
