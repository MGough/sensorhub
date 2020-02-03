# SensorHub

This is a simple library for use with the [DockerPi/52Pi SensorHub (EP-0106)](https://wiki.52pi.com/index.php/DockerPi_Sensor_Hub_Development_Board_SKU:_EP-0106).
You may still need to set up the board as documented on the 52pi wiki (configuring/enabling I2C).

This library allows you to read from each sensor individually. It does not require the external temperature sensor to be connected,
however an exception will be thrown if you try to read from it while it is disconnected.

## How to use it
Interacting with the SensorHub is easy. First create an instance of the SensorHub, which will open communication with it:
```python
from sensorhub.hub import SensorHub
hub = SensorHub()
```

Then it's just a case of calling the method for the value that you're after:

```python
temperature = hub.get_temperature()
```

Other available methods are:
```
hub.get_off_board_temperature()
hub.get_humidity()
hub.get_temperature()
hub.is_motion_detected()
hub.get_brightness()
hub.get_barometer_temperature()
hub.get_barometer_pressure()
```

See the docstrings for more information on return types and exceptions that may be raised.