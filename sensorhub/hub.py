from smbus2 import SMBus
from enum import Enum

DEVICE_BUS = 1
DEVICE_ADDR = 0x17


class SensorRegister(Enum):
    OFF_BOARD_TEMPERATURE = 1
    LIGHT_LOW = 2
    LIGHT_HIGH = 3
    STATUS = 4
    ON_BOARD_TEMPERATURE = 5
    ON_BOARD_HUMIDITY = 6
    ON_BOARD_SENSOR_OUT_OF_DATE = 7
    BAROMETRIC_TEMPERATURE = 8
    BAROMETRIC_PRESSURE_LOW = 9
    BAROMETRIC_PRESSURE_MIDDLE = 10
    BAROMETRIC_PRESSURE_HIGH = 11
    BAROMETRIC_SENSOR_STATUS = 12
    MOTION = 13


class StatusRegisterErrorCode(Enum):
    TEMPERATURE_OUT_OF_RANGE = 0b0001
    TEMPERATURE_SENSOR_MISSING = 0b0010
    BRIGHTNESS_OUT_OF_RANGE = 0b0100
    BRIGHTNESS_SENSOR_HARDWARE_FAILURE = 0b1000


class SensorHub:
    _bus: SMBus

    def __init__(self, system_management_bus: SMBus = None):
        self._bus = system_management_bus or SMBus(DEVICE_BUS)

    def _read_sensor_board_register(self, buffer: SensorRegister) -> int:
        return self._bus.read_byte_data(DEVICE_ADDR, buffer.value)

    def _get_error_codes(self) -> int:
        """
        checks the status register for off board temperature errors or brightness sensor errors
        :return: an int representing a byte (so 0000 is just 0), made up of the following (may be combined)
        0000: no errors
        0001: temperature out of range
        0010: temperature sensor missing
        0100: brightness out of range
        1000: brightness sensor error
        """
        return self._read_sensor_board_register(SensorRegister.STATUS)

    def _is_off_board_temperature_out_of_range(self) -> bool:
        error_codes = self._get_error_codes()

        if error_codes & StatusRegisterErrorCode.TEMPERATURE_OUT_OF_RANGE.value:
            return True
        elif error_codes & StatusRegisterErrorCode.TEMPERATURE_SENSOR_MISSING.value:
            raise IOError("Sensor Missing")
        return False

    def get_off_board_temperature(self) -> int:
        """
        Returns the temperature in degrees celcius.
        :return: Temperature in degrees celcius, or -1 if it's out of range
        :raises IOError: Raised if the sensor is not connected
        """
        if self._is_off_board_temperature_out_of_range():
            return -1
        return self._read_sensor_board_register(SensorRegister.OFF_BOARD_TEMPERATURE)

    def _is_temperature_and_humidity_data_up_to_date(self) -> bool:
        """
        Unlike other errors, this often happens so we handle it more gracefully than throwin an exception
        :return: boolean representing whether or not the data is up to date
        """
        return self._read_sensor_board_register(SensorRegister.ON_BOARD_SENSOR_OUT_OF_DATE) == 0

    def get_humidity(self) -> int:
        """
        Get the humidity sensor reading
        :return: Humidity as a percentage, or -1 if the data is not up to date
        """
        if self._is_temperature_and_humidity_data_up_to_date():
            return self._read_sensor_board_register(SensorRegister.ON_BOARD_HUMIDITY)
        return -1

    def get_temperature(self) -> int:
        """
        Get the on board temperature
        :return: Temperature in celcius, or -1 if the data is not up to date
        """
        if self._is_temperature_and_humidity_data_up_to_date():
            return self._read_sensor_board_register(SensorRegister.ON_BOARD_TEMPERATURE)
        return -1

    def is_motion_detected(self) -> bool:
        """
        Find out if any motion was detected recently
        :return: true if motion was recently detected
        """
        return self._read_sensor_board_register(SensorRegister.MOTION) == 1

    def _is_brightness_out_of_range(self) -> bool:
        error_codes = self._get_error_codes()

        if error_codes & StatusRegisterErrorCode.BRIGHTNESS_OUT_OF_RANGE.value:
            return True
        elif error_codes & StatusRegisterErrorCode.BRIGHTNESS_SENSOR_HARDWARE_FAILURE.value:
            raise IOError("Error accessing light sensor")
        return False

    def get_brightness(self) -> int:
        """
        get brightness sensor reading in Lux
        :return: brightness in Lux, -1 if the reading is out of range
        :raises IOError: raised if there's a hardware issue with the light sensor (i.e. shoudn't happen)
        """
        if self._is_brightness_out_of_range():
            return -1
        else:
            high = self._read_sensor_board_register(SensorRegister.LIGHT_HIGH)
            low = self._read_sensor_board_register(SensorRegister.LIGHT_LOW)
            lux_reading = (high << 8 | low)
            return lux_reading

    def _is_barometer_working(self) -> bool:
        if self._read_sensor_board_register(SensorRegister.BAROMETRIC_SENSOR_STATUS) == 0:
            return True
        raise IOError("Barometric Sensor Error")

    def get_barometer_temperature(self) -> int:
        """
        get barometer temperature sensor reading in celcius
        :return: temperature in celcius
        :raises IOError: raised if there's a hardware issue with the barometer (i.e. shouldn't happen)
        """
        if self._is_barometer_working():
            return self._read_sensor_board_register(SensorRegister.BAROMETRIC_TEMPERATURE)

    def get_barometer_pressure(self) -> float:
        """
        get barometer pressure sensor reading in celcius
        :return: pressure in hPa (hectopascals)
        :raises IOError: raised if there's a hardware issue with the barometer (i.e. shouldn't happen)
        """
        if self._is_barometer_working():
            pascals = self._read_sensor_board_register(SensorRegister.BAROMETRIC_PRESSURE_LOW) \
                      | self._read_sensor_board_register(SensorRegister.BAROMETRIC_PRESSURE_MIDDLE) << 8 \
                      | self._read_sensor_board_register(SensorRegister.BAROMETRIC_PRESSURE_HIGH) << 16

            # convert to hPa
            return round(pascals * 0.01, ndigits=2)
