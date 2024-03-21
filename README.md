# ENS160
ENS160 Python library, tested on Raspberry Pi 5 with Python 3.12.

# Example

```python
dev = ENS160(0x53)
dev.init()
part_id = dev.get_part_id()
if part_id != ENS160.PART_ID:
    print(f"Part not found, expected {ENS160.PART_ID} got {part_id}.")
    exit(-1)

print(f"Part Id {part_id}")
print(f"Firmware version {dev.get_fw_version()}")

dev.set_rh_compensation(55.0)
dev.set_temp_compensation_fahrenheit(72.5)

print(dev.get_device_status())

dev.set_operating_mode(OpMode.STANDARD)
print(dev.get_operating_mode())

while(True):
    status = dev.get_device_status()
    print(status)
    if status.new_data:
        print(f"AQI={dev.get_aqi()}, eCO2={dev.get_eco2()}ppm, TVOC={dev.get_tvoc()}ppb")
    else:
        sleep(1)
```
