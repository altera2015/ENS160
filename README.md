# ENS160
ENS160 Python library, tested on Raspberry Pi 5 with Python 3.12.

# Example

See [example.py](https://github.com/altera2015/ENS160/blob/main/src/example.py)

```python
import sys
from time import sleep

from ens160.driver import Driver
from ens160.enumerations import OpModes

from ens160.retry_i2c import SMBusRetryingI2C
dev = Driver(SMBusRetryingI2C(0x53, 1))

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

while True:
    status = dev.get_device_status()
    print(status)
    if status.new_data:
        print(
            f"AQI={dev.get_aqi()}, eCO2={dev.get_eco2()}ppm, TVOC={dev.get_tvoc()}ppb"
        )
    else:
        sleep(0.1)

```
