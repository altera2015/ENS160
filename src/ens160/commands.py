"""Commands Constants"""

from enum import IntEnum

# pylint: disable-next=missing-class-docstring
class Commands(IntEnum):
    NOP = 0x00
    """No Op."""
    GET_FW_VER = 0x0E
    """Get firmware version."""
    CLEAR_GPR_READ = 0xCC
    """Clear GPR flag."""
