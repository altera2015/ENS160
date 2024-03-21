"""Register values"""

from enum import IntEnum

# pylint: disable-next=missing-class-docstring
class Registers(IntEnum):

    PART_ID = 0x00
    """Device Identity 0x01, 0x60."""
    OP_MODE = 0x10
    """Operating Mode."""
    CONFIG = 0x11
    """Interrupt Pin Configuration."""
    COMMAND = 0x12
    """Additional System Commands, only in idle mode."""
    TEMP_IN = 0x13
    """Host Ambient Temperature Information."""
    RH_IN = 0x15
    """Host Relative Humidity Information."""
    DEVICE_STATUS = 0x20
    """perating Mode."""

    DATA_AQI = 0x21
    """Air Quality Index."""
    DATA_TVOC = 0x22
    """TVOC Concentration (ppb)."""
    DATA_ECO2 = 0x24
    """Equivalent CO2 Concentration (ppm)."""

    DATA_T = 0x30
    """Temperature used in calculations."""
    DATA_RH = 0x32
    """Relative Humidity used in calculations."""

    DATA_MISR = 0x38
    """Data Integrity Field (optional)."""

    GPR_WRITE = 0x40
    """8 bytes of General Purpose Write Registers."""
    GRP_READ0 = 0x48
    """1 byte s of General Purpose Read Registers."""
    GRP_READ1 = 0x49
    """1 byte s of General Purpose Read Registers."""
    GRP_READ2 = 0x4A
    """1 byte s of General Purpose Read Registers."""
    GRP_READ3 = 0x4B
    """1 byte s of General Purpose Read Registers."""
    GRP_READ4 = 0x4C
    """1 byte s of General Purpose Read Registers."""
    GRP_READ5 = 0x4D
    """1 byte s of General Purpose Read Registers."""
    GRP_READ6 = 0x4E
    """1 byte s of General Purpose Read Registers."""
    GRP_READ7 = 0x4F
    """1 byte s of General Purpose Read Registers."""
