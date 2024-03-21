"""Mock ENS160 wrapper."""

from . import Commands, Registers, OpModes, Status, ICommunication


class MockENS160(ICommunication):
    """Limited simulation of the ENS160"""

    def __init__(
        self,
    ):
        self.__op_mode = 0
        self.__status = Status(0)
        self.__status.power_on = True
        self.__registers = {}
        self.__registers[Registers.PART_ID] = 0x60
        self.__registers[Registers.PART_ID + 1] = 0x01
        self.__registers[Registers.DATA_AQI] = 1
        self.__registers[Registers.DATA_ECO2] = 0
        self.__registers[Registers.DATA_ECO2 + 1] = 0
        self.__registers[Registers.DATA_TVOC] = 0
        self.__registers[Registers.DATA_TVOC + 1] = 0
        self.__registers[Registers.GRP_READ4] = 0
        self.__registers[Registers.GRP_READ5] = 0
        self.__registers[Registers.GRP_READ6] = 0
        self.__delay = 5

    def __handle_command(self, command: int):
        if command == Commands.GET_FW_VER:
            self.__registers[Registers.GRP_READ4] = 1
            self.__registers[Registers.GRP_READ5] = 2
            self.__registers[Registers.GRP_READ6] = 3
            self.__status.new_gpr = True
        if command == Commands.CLEAR_GPR_READ:
            self.__status.new_gpr = False

    def __handle_status(self):
        if self.__op_mode == OpModes.STANDARD and not self.__status.new_data:
            self.__delay -= 1
            if self.__delay == 0:
                self.__status.new_data = 1
                self.__registers[Registers.DATA_AQI] = 1
                self.__registers[Registers.DATA_ECO2] = 50
                self.__registers[Registers.DATA_ECO2 + 1] = 0
                self.__registers[Registers.DATA_TVOC] = 100
                self.__registers[Registers.DATA_TVOC + 1] = 0
                self.__delay = 5

        return self.__status.to_status()

    def __handle_opmode(self, mode: int):
        if mode == OpModes.RESET:
            self.__op_mode = OpModes.DEEP_SLEEP
        elif mode in [OpModes.DEEP_SLEEP, OpModes.STANDARD, OpModes.IDLE]:
            self.__op_mode = mode

    def __read_register(self, register: Registers, size: int):
        results = []
        for i in range(size):
            results.append(self.__registers[register + i])

        # clear the flag.
        if register in [Registers.DATA_AQI, Registers.DATA_ECO2, Registers.DATA_TVOC]:
            self.__status.new_data = 0

        return results

    def write(self, register: Registers, data: list[int] | int):
        """Write data to the I2C bus."""
        if isinstance(data, int):
            if self.__op_mode == 1 and register == Registers.COMMAND:
                self.__handle_command(data)
            if register == Registers.OP_MODE:
                self.__handle_opmode(data)

    def read(self, register: Registers, size: int):
        """Read data from the I2C bus."""
        if size == 1:
            if register == Registers.DEVICE_STATUS:
                return self.__handle_status()
            if register == Registers.OP_MODE:
                return self.__op_mode
            return self.__registers[register]

        return self.__read_register(register, size)
