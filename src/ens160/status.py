"""Data Status Structure."""

# pylint: disable-next=missing-class-docstring
class Status:
    def __init__(self, d):
        """Initializes structure from byte value."""
        self.__flags = (d & 0x0C) >> 2
        self.warm_up = self.__flags == 1
        """Set during first 3 minutes after power-on"""
        self.inital_startup = self.__flags == 2
        """Set during first full hour of operation after initial power-on24."""
        self.normal_operation = self.__flags == 0
        """Set if in standard operating mode."""
        self.invalid_data = self.__flags == 3
        """Set if signals give unexpected values (very high or very low). Multiple sensors out of range."""
        self.power_on = (d & 0x80) == 0x80
        """Set if the unit is not in deep_sleep."""
        self.error = (d & 0x40) == 0x40
        """Set if an error has occurred."""
        self.new_data = (d & 0x02) == 0x02
        """Set if data is available to read, automatically cleared after a read."""
        self.new_gpr = (d & 0x01) == 0x01
        """Set if new general purpose data is available, automatically cleared after a read."""

    def __str__(self):
        # pylint: disable=line-too-long
        return f"warm_up={self.warm_up}, inital_startup={self.inital_startup} power on={self.power_on}, error={self.error}, new data={self.new_data}, new gpr={self.new_gpr}"

    def to_status(self):
        """Returns the byte value corresponding to the current value of the flags"""
        self.__flags = (
            self.warm_up * 1 | self.inital_startup * 2 | self.invalid_data * 3
        )
        return (
            self.new_gpr
            | self.new_data << 1
            | self.__flags << 2
            | self.error << 6
            | self.power_on << 7
        )
