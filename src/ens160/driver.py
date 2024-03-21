"""
ENS160 I2C driver
"""

from time import sleep

from .commands import Commands
from .icommunication import ICommunication
from .op_modes import OpModes
from .registers import Registers
from .status import Status

class Driver:
    """ENS160 Sensor class."""

    PART_ID = 0x160
    """The PART_ID as of the ENS160."""

    def __init__(self, communication: ICommunication):
        """Constructor for the class which takes an `ens160.ICommunication` object
        to provide the communications.

        This project provides two retry_i2c.SMBusRetryingI2C and ens160.mock.MockENS160. The
        first can be used to communicate with a real ENS160 via an I2C link.

        The ENS160 can be configured to use I2C addresses 0x52 or 0x53.
        """
        self.__i2c = communication

    def set_operating_mode(self, mode: OpModes):
        """Sets the ENS160 operation mode. Returns True on success.

        Note that get_part_id and get_fw_version will only work in
        OpModes.IDLE.
        """
        self.__i2c.write(Registers.OP_MODE, mode)

    def get_operating_mode(self) -> OpModes:
        """Returns one of the ENS160_OP_MODE values."""
        return self.__i2c.read(Registers.OP_MODE, 1)

    def get_part_id(self) -> int:
        """Gets the part id.

        Expecting 0x0160. Note that this only works in OpModes.IDLE."""
        byte_values = self.__i2c.read(Registers.PART_ID, 2)
        return byte_values[0] + (byte_values[1] << 8)

    def clear_gp_read_flag(self):
        """Clears the General Purpose Read bit of the device status."""
        # this command appears to not work.
        # self.__i2c.write(Register.COMMAND, Commands.CLEAR_GPR_READ)
        # just read anything to clear the flag.
        self.__i2c.read(Registers.GRP_READ4, 3)

    def get_fw_version(self) -> str:
        """Returns a string of firmware version in Major.Minor.Release format.

        For example: 5.4.6."""
        self.__i2c.write(Registers.COMMAND, Commands.GET_FW_VER)
        while True:
            status = self.get_device_status()
            if status.new_gpr:
                break
            sleep(0.001)
        byte_data = self.__i2c.read(Registers.GRP_READ4, 3)
        return f"{byte_data[0]}.{byte_data[1]}.{byte_data[2]}"

    def set_temp_compensation_kelvin(self, t_in_kelvin: float):
        """Sets the compensation temperature. The sensor will adjust the
        measurement outputs based on these values.

        Note: set temperature and humidity compensation values before reading data,
        otherwise you get zeros."""
        param: int = round(t_in_kelvin * 64)
        params: list[int] = []
        params.append(param & 0x00FF)
        params.append((param & 0xFF00) >> 8)
        self.__i2c.write(Registers.TEMP_IN, params)

    def set_temp_compensation_celcius(self, t_in_celcius: float):
        """Sets the compensation temperature. The sensor will adjust the
        measurement outputs based on these values.

        Note: set temperature and humidity compensation values before reading data,
        otherwise you get zeros."""

        self.set_temp_compensation_kelvin(t_in_celcius + 273.15)

    def set_temp_compensation_fahrenheit(self, t_in_fahrenheit: float):
        """Sets the compensation temperature. The sensor will adjust the
        measurement outputs based on these values.

        Note: set temperature and humidity compensation values before reading data,
        otherwise you get zeros."""

        self.set_temp_compensation_celcius((t_in_fahrenheit - 32.0) * 5.0 / 9.0)

    def set_rh_compensation(self, relative_humidity: float):
        """Sets the compensation humidity. The sensor will adjust the
        measurement outputs based on these values.

        Note: set temperature and humidity compensation values before reading data,
        otherwise you get zeros."""

        param: int = round(relative_humidity * 512)
        params: list[int] = []
        params.append(param & 0x00FF)
        params.append((param & 0xFF00) >> 8)
        self.__i2c.write(Registers.RH_IN, params)

    def get_device_status(self) -> Status:
        """Get the device status."""
        return Status(self.__i2c.read(Registers.DEVICE_STATUS, 1))

    def get_aqi(self) -> int:
        """Get the Air Quality index.

        Possible value are 1,2,3,4 or 5. With 1 being great and 5 being worst."""
        return self.__i2c.read(Registers.DATA_AQI, 1) & 0x07

    def get_tvoc(self) -> int:
        """Get the Total Volatile Organic compounds in the air in ppb. Lower is
        better air quality.
        """
        byte_values = self.__i2c.read(Registers.DATA_TVOC, 2)
        return byte_values[0] + (byte_values[1] << 8)

    def get_eco2(self) -> int:
        """Get the eCO2 levels in the air in ppm.

        | Range      | Unit | Quality   | Description
        |------------|------|-----------|------------
        |0 - 600     | ppm  | Excellent | Target
        |600 - 800   | ppm  | Good      | Average
        |800 - 1000  | ppm  | Fair      | Optional Ventilation
        |1000 - 1500 | ppm  | Poor      | Contaminated indoor air, ventilation recommend.
        |1500 +      | ppm  | Bad       | Heavily contaminated indoor air, ventilation required.

        """
        byte_values = self.__i2c.read(Registers.DATA_ECO2, 2)
        return byte_values[0] + (byte_values[1] << 8)

    def reset(self):
        """Reset the unit.

        Sets the operating mode to OpModes.RESET and then waits for OpModes.DEEP_SLEEP.
        """
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
