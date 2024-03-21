"""Status Parsing class"""

class Status:
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

    def to_status(self):
        """Returns the byte value corresponding to the current value of the flags"""
        return self.new_gpr | self.new_data << 1 | self.flags << 2 | self.error << 6 | self.power_on << 7
