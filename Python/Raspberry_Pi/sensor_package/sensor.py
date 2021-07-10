"""Sensor data.

When instantiated, this object will initialize the hardware sensor and collect
an initial round of data. Each piece of data is available individually and
can be refreshed by calling the 'refresh()' method.
"""

import smbus
from time import sleep
from typing import Optional

import RPi.GPIO as gpio

from sensor_constants import SensorConstants
from unicode_constants import UnicodeConstants


class SensorData(object):
    """SensorData class."""

    def __init__(self, particle_sensor: Optional[int] = None):
        """Init.

        The possibilities for the particle sensor are:
            SensorConstants().particle_sensor_off: if no sensor is connected
            SensorConstants().particle_sensor_ppd42: for the Shinyei PPD42
            SensorConstants().particle_sensor_sds011: for the Nova SDS011

        Args:
            particle_sensor (int): The type of particle sensor attached,
                if any.
                Default is None which will become:
                    SensorConstants.particle_sensor_off (0)
        """
        super(SensorData, self).__init__()

        self.sensor_constants = SensorConstants()
        self.unicode_constants = UnicodeConstants()

        self.particle_sensor = particle_sensor
        if not self.particle_sensor:
            self.particle_sensor = self.sensor_constants.particle_sensor_off

        self._init_hardware()
        self.refresh()

    def _init_hardware(self):
        """Set up the Raspberry Pi GPIO."""
        gpio.setwarnings(False)
        gpio.setmode(gpio.BOARD)
        gpio.setup(self.sensor_constants.ready_pin, gpio.IN)
        gpio.setup(self.sensor_constants.light_int_pin, gpio.IN)
        gpio.setup(self.sensor_constants.sound_int_pin, gpio.IN)

        # Initialize the I2C communications bus object
        # Port 1 is the default for I2C on Raspberry Pi
        self.i2c_bus = smbus.SMBus(1)

        # Wait for the MS430 to finish power-on initialization:
        while (gpio.input(self.sensor_constants.ready_pin) == 1):
            sleep(0.05)

        # Tell the Pi to monitor READY for a falling edge event
        # (high-to-low voltage change)
        gpio.add_event_detect(self.sensor_constants.ready_pin, gpio.FALLING)

    def get_gpio(self) -> gpio:
        """Return the initialized gpio module."""
        return gpio

    def cleanup_gpio(self):
        """Cleanup the gpio after execution."""
        gpio.cleanup()

    def refresh(self):
        """Refresh the sensor data."""
        # Reset MS430 to clear any previous state:
        self.i2c_bus.write_byte(
            self.sensor_constants.i2c_addr_7bit_sb_open,
            self.sensor_constants.reset_cmd
        )
        sleep(0.005)

        # Wait for reset completion and entry to standby mode
        while (gpio.input(self.sensor_constants.ready_pin) == 1):
            sleep(0.05)

        # Initiate an on-demand data measurement
        self.i2c_bus.write_byte(
            self.sensor_constants.i2c_7bit_address,
            self.sensor_constants.on_demand_measure_cmd
        )

        # Wait for the ready signal (falling edge) before continuing
        while (not gpio.event_detected(self.sensor_constants.ready_pin)):
            sleep(0.05)

        # Brief final sleep to stabalize sensors
        sleep(1.5)

        self.get_air_data()
        self.get_air_quality_data()
        self.get_light_data()
        self.get_sound_data()
        self.get_particle_data()

    def get_air_data(self):
        """Get air data."""
        self.raw_air_data = self.i2c_bus.read_i2c_block_data(
            self.sensor_constants.i2c_addr_7bit_sb_open,
            self.sensor_constants.air_data_read,
            self.sensor_constants.air_data_bytes
        )
        self._extract_air_data()

    def get_air_quality_data(self):
        """Get air quality data."""
        self.raw_air_quality_data = self.i2c_bus.read_i2c_block_data(
            self.sensor_constants.i2c_addr_7bit_sb_open,
            self.sensor_constants.air_quality_data_read,
            self.sensor_constants.air_quality_data_bytes
        )
        self._extract_air_quality_data()

    def get_light_data(self):
        """Get light data."""
        self.raw_light_data = self.i2c_bus.read_i2c_block_data(
            self.sensor_constants.i2c_addr_7bit_sb_open,
            self.sensor_constants.light_data_read,
            self.sensor_constants.light_data_bytes
        )
        self._extract_light_data()

    def get_sound_data(self):
        """Get sound data."""
        self.raw_sound_data = self.i2c_bus.read_i2c_block_data(
            self.sensor_constants.i2c_addr_7bit_sb_open,
            self.sensor_constants.sound_data_read,
            self.sensor_constants.sound_data_bytes
        )
        self._extract_sound_data()

    def get_particle_data(self):
        """Get particle data."""
        self.raw_particle_data = self.i2c_bus.read_i2c_block_data(
            self.sensor_constants.i2c_addr_7bit_sb_open,
            self.sensor_constants.particle_data_read,
            self.sensor_constants.particle_data_bytes
        )
        self._extract_particle_data()

    def _extract_air_data(self):
        """Extract air data."""
        if (len(self.raw_air_data) != self.sensor_constants.air_data_bytes):
            raise Exception('Incorrect number of Air Data bytes')

        self.temp_c = (
            (
                self.raw_air_data[0]
                & self.sensor_constants.temperature_value_mask
            ) + (float(self.raw_air_data[1]) / 10.0)
        )
        if (
            (
                self.raw_air_data[0]
                & self.sensor_constants.temperature_sign_mask
            ) != 0
        ):
            # If the most-significant bit is set, the temperature is negative
            self.temp_c = -self.temp_c

        self.temp_f = (self.temp_c * 1.8) + 32.0

        self.pressure = (
            (self.raw_air_data[5] << 24)
            + (self.raw_air_data[4] << 16)
            + (self.raw_air_data[3] << 8)
            + self.raw_air_data[2]
        )

        self.humidity = (
            self.raw_air_data[6] + (float(self.raw_air_data[7]) / 10.0)
        )

        self.gas_sensor_resistance = (
            (self.raw_air_data[11] << 24)
            + (self.raw_air_data[10] << 16)
            + (self.raw_air_data[9] << 8)
            + self.raw_air_data[8]
        )

    def _extract_air_quality_data(self):
        """Extract air quality data."""
        if (
            len(self.raw_air_quality_data)
            != self.sensor_constants.air_quality_data_bytes
        ):
            raise Exception('Incorrect number of Air Quality Data bytes')

        self.aqi = (
            self.raw_air_quality_data[0]
            + (self.raw_air_quality_data[1] << 8)
            + (float(self.raw_air_quality_data[2]) / 10.0)
        )
        self.co2e = (
            self.raw_air_quality_data[3]
            + (self.raw_air_quality_data[4] << 8)
            + (float(self.raw_air_quality_data[5]) / 10.0)
        )
        self.bvoc = (
            self.raw_air_quality_data[6]
            + (self.raw_air_quality_data[7] << 8)
            + (float(self.raw_air_quality_data[8]) / 100.0)
        )
        self.aqi_accuracy = self.raw_air_quality_data[9]

        self.interpret_aqi_value()
        self.interpret_aqi_accuracy()

    def _extract_light_data(self):
        """Extract light data."""
        if (
            len(self.raw_light_data) != self.sensor_constants.light_data_bytes
        ):
            raise Exception(
                'Incorrect number of Light Data bytes supplied to function'
            )
        self.lux = (
            self.raw_light_data[0]
            + (self.raw_light_data[1] << 8)
            + (float(self.raw_light_data[2]) / 100.0)
        )

        self.white = (
            self.raw_light_data[3] + (self.raw_light_data[4] << 8)
        )

    def _extract_sound_data(self):
        """Extract sound data."""
        if (
            len(self.raw_sound_data) != self.sensor_constants.sound_data_bytes
        ):
            raise Exception(
                'Incorrect number of Sound Data bytes supplied to function'
            )

        self.spl_dba = (
            self.raw_sound_data[0] + (float(self.raw_sound_data[1]) / 10.0)
        )
        j = 2
        self.spl_bands_db = dict()
        for i in range(0, self.sensor_constants.sound_freq_bands):
            self.spl_bands_db[i] = (
                self.raw_sound_data[j]
                + (float(self.raw_sound_data[
                    j + self.sensor_constants.sound_freq_bands
                ]) / 10.0)
            )
            j += 1
        j += self.sensor_constants.sound_freq_bands

        self.peak_amp = (
            self.raw_sound_data[j]
            + (self.raw_sound_data[j + 1] << 8)
            + (float(self.raw_sound_data[j + 2]) / 100.0)
        )

        self.stable = self.raw_sound_data[j + 3]

    def _extract_particle_data(self):
        """Extract particle data."""
        if (self.particle_sensor == self.sensor_constants.particle_sensor_off):
            self.duty_cycle_pc = None
            self.concentration = None
            self.conc_unit = None
            self.particle_data_valid = False
            return

        if (
            len(self.raw_particle_data)
            != self.sensor_constants.particle_data_bytes
        ):
            raise Exception(
                'Incorrect number of Particle Data bytes supplied to function'
            )

        self.duty_cycle_pc = (
            self.raw_particle_data[0]
            + (float(self.raw_particle_data[1]) / 100.0)
        )

        self.concentration = (
            self.raw_particle_data[2]
            + (self.raw_particle_data[3] << 8)
            + (float(self.raw_particle_data[4]) / 100.0)
        )

        if (self.raw_particle_data[5] > 0):
            self.particle_data_valid = True
        else:
            self.particle_data_valid = False

        if (
            self.particle_sensor == self.sensor_constants.particle_sensor_ppd42
        ):
            self.conc_unit = "ppL"

        elif (
            self.particle_sensor
            == self.sensor_constants.particle_sensor_sds011
        ):
            self.conc_unit = self.unicode_constants.sds011_conc

    def interpret_aqi_value(self):
        """Provide a readable interpretation of the AQI (air quality index)."""
        if (self.aqi < 50):
            self.int_aqi = "Good"
        elif (self.aqi < 100):
            self.int_aqi = "Acceptable"
        elif (self.aqi < 150):
            self.int_aqi = "Substandard"
        elif (self.aqi < 200):
            self.int_aqi = "Poor"
        elif (self.aqi < 300):
            self.int_aqi = "Bad"
        else:
            self.int_aqi = "Very bad"

    def interpret_aqi_accuracy(self):
        """Interpret AQI accuracy.

        Provide a readable interpretation of the accuracy code for
        the air quality measurements (applies to all air quality data).
        """
        if (self.aqi_accuracy == 1):
            self.int_aqi_accuracy = "Low accuracy, self-calibration ongoing"
        elif (self.aqi_accuracy == 2):
            self.int_aqi_accuracy = "Medium accuracy, self-calibration ongoing"
        elif (self.aqi_accuracy == 3):
            self.int_aqi_accuracy = "High accuracy"
        else:
            self.int_aqi_accuracy = (
                "Not yet valid, self-calibration incomplete"
            )

    def set_sound_interrupt_threshold(self, peak: int):
        """Set the threshold for triggering a sound interrupt.

        Args:
            peak (int): Peak sound amplitude threshold in milliPascals,
                This can be any 16-bit integer.
        """
        # The 16-bit threshold value is split and sent as two 8-bit values:
        # [LSB, MSB]
        data_to_send = [(peak & 0x00FF), (peak >> 8)]
        self.i2c_bus.write_i2c_block_data(
            self.sensor_constants.i2c_addr_7bit_sb_open,
            self.sensor_constants.sound_interrupt_threshold_reg,
            data_to_send
        )

    def set_light_interrupt_threshold(
        self, light_thres_lux_i: int, light_thres_lux_f2dp: int
    ):
        """Set the threshold for triggering a light interrupt.

        The threshold value in lux units can be fractional and is formed as:
            threshold = light_thres_lux_i + (light_thres_lux_f2dp/100)

        Threshold values exceeding MAX_LUX_VALUE
        will be limited to MAX_LUX_VALUE.

        Args:
            light_thres_lux_i (int): Light threshold.
            light_thres_lux_f2dp (int): Light threshold.
        """
        # The 16-bit integer part of the threshold value is split
        # and sent as two 8-bit values,
        # while the fractional part is sent as an 8-bit value:
        data_to_send = [
            (light_thres_lux_i & 0x00FF),
            (light_thres_lux_i >> 8),
            light_thres_lux_f2dp
        ]
        self.i2c_bus.write_i2c_block_data(
            self.sensor_constants.i2c_addr_7bit_sb_open,
            self.sensor_constants.light_interrupt_threshold_reg,
            data_to_send
        )

    def __str__(self):
        """String magic method."""
        output = [
            f'Temperature: {self.temp_c:.1f}{self.unicode_constants.celsius} /'
            f' {self.temp_f:.1f}{self.unicode_constants.fahrenheit}',
            f'Air Pressure: {self.pressure}Pa',
            f'Humidity: {self.humidity}%',
            'Gas Sensor Resistance: '
            f'{self.gas_sensor_resistance}{self.unicode_constants.ohm}',
            f'Air Quality: {self.aqi}',
            f'Air Quality Interpreted: {self.int_aqi}',
            f'Air Quality CO2e: {self.co2e}',
            f'Air Quality bVOC: {self.bvoc}',
            f'Air Quality Accuracy: {self.aqi_accuracy}',
            f'Interpreted Air Quality Accuracy: {self.int_aqi_accuracy}',
            f'Light Lux: {self.lux}',
            f'Light White: {self.white}',
            f'Audio Decibels: {self.spl_dba}',
            f'Audio Bands: {self.spl_bands_db}',
            f'Audio Peak Amplitude: {self.peak_amp}',
            f'Audio Stable: {self.stable}',
            f'Particle Sensor: {self.particle_sensor}',
            f'Particle Sensor Duty Cycle: {self.duty_cycle_pc}',
            f'Particle Concentration: {self.concentration}',
            f'Particle Concentration Unit: {self.conc_unit}',
            f'Particle Data Valid: {self.particle_data_valid}',
        ]
        return '\n'.join(output)

    def __dict__(self):
        """Dictionary magic method."""
        return {
            'temp_c': self.temp_c,
            'temp_f': self.temp_f,
            'pressure': self.pressure,
            'humidity': self.humidity,
            'gas_sensor_resistance': self.gas_sensor_resistance,
            'air_quality': self.aqi,
            'int_aqi': self.int_aqi,
            'co2e': self.co2e,
            'bvoc': self.bvoc,
            'air_quality_accuracy': self.aqi_accuracy,
            'int_aqi_accuracy': self.int_aqi_accuracy,
            'lux': self.lux,
            'white': self.white,
            'spl_dba': self.spl_dba,
            'spl_bands_db': self.spl_bands_db,
            'peak_amp': self.peak_amp,
            'stable': self.stable,
            'particle_sensor': self.particle_sensor,
            'duty_cycle_pc': self.duty_cycle_pc,
            'concentration': self.concentration,
            'conc_unit': self.conc_unit,
            'particle_data_valid': self.particle_data_valid,
        }

    def __iter__(self):
        """Iter magic method."""
        return iter(self.__dict__().items())
