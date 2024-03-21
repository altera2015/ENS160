"""ENS160 example."""

# pylint: skip-file

import sys
from time import sleep

from ens160 import Driver
from ens160 import OpModes

if __name__ == "__main__":
    try:
        from smbus2 import SMBus
        from ens160.i2c import SMBusRetryingI2C

        dev = Driver(SMBusRetryingI2C(0x53, 1))
    except ModuleNotFoundError as e:
        print(f"Could not find SMBus, using MOCK interface. Error was: {e}")
        from ens160.mock import MockENS160

        dev = Driver(MockENS160())

    dev.init()
    part_id = dev.get_part_id()
    if part_id != Driver.PART_ID:
        print(f"Part not found, expected {Driver.PART_ID} got {part_id}.")
        sys.exit(-1)

    print(f"Part Id {part_id}")
    print(f"Firmware version {dev.get_fw_version()}")

    dev.set_rh_compensation(55.0)
    dev.set_temp_compensation_fahrenheit(72.5)

    print(dev.get_device_status())

    dev.set_operating_mode(OpModes.STANDARD)
    print("Operating Mode: ", dev.get_operating_mode())

    i = 0
    while i < 10:
        status = dev.get_device_status()
        print(status)
        if status.new_data:
            i += 1
            print(
                f"AQI={dev.get_aqi()}, eCO2={dev.get_eco2()}ppm, TVOC={dev.get_tvoc()}ppb"
            )
        else:
            sleep(0.1)
