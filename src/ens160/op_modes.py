"""Operation Mode Constants."""

from enum import IntEnum

# pylint: disable-next=missing-class-docstring
class OpModes(IntEnum):
    DEEP_SLEEP = 0x00
    """only responds to Command OP_MODE write"""
    IDLE = 0x01
    """accepting commands."""
    STANDARD = 0x02
    """Gas Sensing."""
    RESET = 0xF0
    """Reset the unit."""
