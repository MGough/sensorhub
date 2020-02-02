from pytest import fixture, raises, mark
from unittest.mock import patch, call

from sensorhub.hub import SensorHub, SensorRegister

@fixture
def device_bus():
    return 1


@fixture
def device_address():
    return 0x17


@fixture
def sensor_hub():
    with patch("sensorhub.hub.SMBus", autospec=True):
        return SensorHub()


def test_correct_bus_is_created(device_bus):
    with patch("sensorhub.hub.SMBus", autospec=True) as bus:
        sensor_hub = SensorHub()

        bus.assert_called_once_with(device_bus)
        assert sensor_hub.bus == bus()


@mark.parametrize("error_code", [
    0b0001,
    0b0101,
    0b1001,
    0b1101
])
def test_off_board_temperature_out_of_range_returns_minus_1(error_code, sensor_hub, device_address):
    sensor_hub.bus.read_byte_data.return_value = 1

    temperature = sensor_hub.get_off_board_temperature()

    sensor_hub.bus.read_byte_data.assert_called_once_with(device_address, SensorRegister.STATUS.value)
    assert temperature == -1


@mark.parametrize("error_code", [
    0b0010,
    0b0110,
    0b1110,
    0b1010
])
def test_off_board_temperature_sensor_io_error(error_code, sensor_hub, device_address):
    sensor_hub.bus.read_byte_data.return_value = error_code

    with raises(IOError, match="Sensor Missing"):
        sensor_hub.get_off_board_temperature()

    sensor_hub.bus.read_byte_data.assert_called_once_with(device_address, SensorRegister.STATUS.value)


@mark.parametrize("error_code", [
    0b0000,      # no errors
    0b0100,      # brightness out of range
    0b1000,      # brightness sensor error
    0b1100       # brightness out of range AND sensor error (just in case...)
])
def test_off_board_temperature_sensor_returns_temperature(error_code, sensor_hub, device_address):
    expected_temperature = 9001
    sensor_hub.bus.read_byte_data.side_effect = [error_code, 9001]

    temperature = sensor_hub.get_off_board_temperature()

    assert temperature == expected_temperature
    sensor_hub.bus.read_byte_data.assert_has_calls([
        call(device_address, SensorRegister.STATUS.value),
        call(device_address, SensorRegister.OFF_BOARD_TEMPERATURE.value)
    ])


def test_humidity_is_not_up_to_date(sensor_hub, device_address):
    sensor_hub.bus.read_byte_data.return_value = 1

    humidity = sensor_hub.get_humidity()

    assert humidity == -1
    sensor_hub.bus.read_byte_data.assert_called_once_with(device_address, SensorRegister.ON_BOARD_SENSOR_OUT_OF_DATE.value)


def test_humidity_returned_when_it_is_up_to_date(sensor_hub, device_address):
    expected_humidity = 33
    sensor_hub.bus.read_byte_data.side_effect = [0, expected_humidity]

    humidity = sensor_hub.get_humidity()

    assert humidity == expected_humidity
    sensor_hub.bus.read_byte_data.assert_has_calls([call(device_address, SensorRegister.ON_BOARD_SENSOR_OUT_OF_DATE.value),
                                                      call(device_address, SensorRegister.ON_BOARD_HUMIDITY.value)])


def test_on_board_temperature_is_not_up_to_date(sensor_hub, device_address):
    sensor_hub.bus.read_byte_data.return_value = 1

    temperature = sensor_hub.get_temperature()

    assert temperature == -1
    sensor_hub.bus.read_byte_data.assert_called_once_with(device_address, SensorRegister.ON_BOARD_SENSOR_OUT_OF_DATE.value)


def test_on_board_temperature_returned_when_it_is_up_to_date(sensor_hub, device_address):
    expected_temperature = 33
    sensor_hub.bus.read_byte_data.side_effect = [0, expected_temperature]

    temperature = sensor_hub.get_temperature()

    assert temperature == expected_temperature
    sensor_hub.bus.read_byte_data.assert_has_calls(
        [call(device_address, SensorRegister.ON_BOARD_SENSOR_OUT_OF_DATE.value),
         call(device_address, SensorRegister.ON_BOARD_TEMPERATURE.value)])


@mark.parametrize("motion_detected, register_reading", [(True, 1), (False, 0)])
def test_motion_detection(motion_detected, register_reading, sensor_hub, device_address):
    sensor_hub.bus.read_byte_data.return_value = register_reading

    assert sensor_hub.is_motion_detected() is motion_detected

    sensor_hub.bus.read_byte_data.assert_called_once_with(device_address, SensorRegister.MOTION.value)


@mark.parametrize("error_code", [
    0b1000,
    0b1010,
    0b1001,
    0b1011
])
def test_brightness_sensor_error(error_code, sensor_hub, device_address):
    sensor_hub.bus.read_byte_data.return_value = 1000

    with raises(IOError, match="Error accessing light sensor"):
        sensor_hub.get_brightness()

    sensor_hub.bus.read_byte_data.assert_called_once_with(device_address, SensorRegister.STATUS.value)


@mark.parametrize("error_code", [
    0b0100,
    0b0110,
    0b0111,
    0b0101
])
def test_brightness_out_of_range_returns_minus_1(error_code, sensor_hub, device_address):
    sensor_hub.bus.read_byte_data.return_value = 100

    brightness = sensor_hub.get_brightness()

    sensor_hub.bus.read_byte_data.assert_called_once_with(device_address, SensorRegister.STATUS.value)
    assert brightness == -1


@mark.parametrize("error_code", [
    0b0000,     # no errors
    0b0001,     # temperature out of range
    0b0010,     # temperature sensor error
    0b0011      # temperature out of range AND sensor error (just in case...)
])
def test_brightness_is_returned(error_code, sensor_hub, device_address):
    sensor_hub.bus.read_byte_data.side_effect = [error_code, 1, 39]

    brightness = sensor_hub.get_brightness()

    assert brightness == 295
    sensor_hub.bus.read_byte_data.assert_has_calls([
        call(device_address, SensorRegister.LIGHT_HIGH.value),
        call(device_address, SensorRegister.LIGHT_LOW.value)
    ])


def test_barometer_temperature_hardware_error(sensor_hub, device_address):
    sensor_hub.bus.read_byte_data.return_value = 1

    with raises(IOError, match="Barometric Sensor Error"):
        sensor_hub.get_barometer_temperature()

    sensor_hub.bus.read_byte_data.assert_called_once_with(device_address, SensorRegister.BAROMETRIC_SENSOR_STATUS.value)


def test_barometer_temperature_returns_correct_reading(sensor_hub, device_address):
    expected_temperature = 36
    sensor_hub.bus.read_byte_data.side_effect = [0, expected_temperature]

    temperature = sensor_hub.get_barometer_temperature()

    assert temperature == expected_temperature
    sensor_hub.bus.read_byte_data.assert_has_calls([
        call(device_address, SensorRegister.BAROMETRIC_SENSOR_STATUS.value),
        call(device_address, SensorRegister.BAROMETRIC_TEMPERATURE.value)
    ])


def test_barometer_pressure_hardware_error(sensor_hub, device_address):
    sensor_hub.bus.read_byte_data.return_value = 1

    with raises(IOError, match="Barometric Sensor Error"):
        sensor_hub.get_barometer_pressure()

    sensor_hub.bus.read_byte_data.assert_called_once_with(device_address, SensorRegister.BAROMETRIC_SENSOR_STATUS.value)


def test_barometer_pressure_returns_expected_reading(sensor_hub, device_address):
    sensor_hub.bus.read_byte_data.side_effect = [0, 3, 5, 45]

    pressure = sensor_hub.get_barometer_pressure()

    assert pressure == 29504.03
    sensor_hub.bus.read_byte_data.assert_has_calls([
        call(device_address, SensorRegister.BAROMETRIC_SENSOR_STATUS.value),
        call(device_address, SensorRegister.BAROMETRIC_PRESSURE_LOW.value),
        call(device_address, SensorRegister.BAROMETRIC_PRESSURE_MIDDLE.value),
        call(device_address, SensorRegister.BAROMETRIC_PRESSURE_HIGH.value)
    ])
