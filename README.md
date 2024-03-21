# ENS160
ENS160 Python library.

[Datasheet](https://www.sciosense.com/wp-content/uploads/2023/12/ENS160-Datasheet.pdf)

This code was tested on a Raspberry Pi 5 at 100kHz I2C clock.

The I2C code is abstracted from the sensor handling and
other communication methods could be added.

Tested with Python 3.12

# Documentation

The detailed API documentation can be [found here](https://altera2015.github.io/ENS160/ens160.html).

# Install

```sh
pip install https://github.com/altera2015/ENS160/archive/refs/heads/main.zip
```

# Example

See [example.py](https://github.com/altera2015/ENS160/blob/main/tests/example.py)

```python
import sys
from time import sleep

from ens160 import Driver, OpModes

from ens160.i2c import SMBusRetryingI2C
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


# Build Packages

```sh
python -m build
```

# Build Documentation

```sh
cd src
python -m pdoc ens160 --no-show-source -o ../docs
```
