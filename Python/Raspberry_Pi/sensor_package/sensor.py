"""Sensor.

When instantiated, this object will initialize the hardware sensor.
To have the sensor perform a measurement, call the 'measure()' method. If using
cycle mode, you can wrap the 'measure()' call in a loop that will trigger
each cycle time.
"""

import smbus
import threading
import time
import traceback
from typing import Optional

import RPi.GPIO as gpio

from .setup import LOG

from .cycle_status import CycleStatus
from .sensor_mode import SensorMode
from .sensor_constants import SensorConstants
from .unicode_constants import UnicodeConstants


class Sensor(object):
    """Sensor class."""

    # Timeout in seconds for waiting on the ready pin.
    TIMEOUT = 5

    def __init__(
        self,
        mode: Optional[int] = None,
        cycle_time: Optional[int] = None,
        particle_sensor: Optional[int] = None,
    ):
        """Init.

        The possibilities for the mode are:
            SensorConstants().standby_mode: Do nothing (0)
            SensorConstants().cycle_mode: Take continuous measurements (1)
            SensorConstants().on_demand: Take a measurement when requested (2)

        The possibilities for the particle sensor are:
            SensorConstants().particle_sensor_off: No sensor is connected
            SensorConstants().particle_sensor_ppd42: For the Shinyei PPD42
            SensorConstants().particle_sensor_sds011: For the Nova SDS011

        Args:
            mode (int): Mode to start the sensor in.
                Default is None which will become:
                    SensorConstants().on_demand (2)
            cycle_time (int): Time between reads on cycle mode.
                Default is None which will become: 5
                If not using cycle mode, this value is irrelevant.
            particle_sensor (int): The type of particle sensor attached,
                if any.
                Default is None which will become:
                    SensorConstants.particle_sensor_off (0)
        """
        super(Sensor, self).__init__()

        self.sensor_constants = SensorConstants()
        self.unicode_constants = UnicodeConstants()

        self.mode = SensorMode(mode, cycle_time)
        self.cycle_status = CycleStatus()

        self.particle_sensor = (
            particle_sensor or self.sensor_constants.particle_sensor_off
        )

        self._init_hardware()

    def _init_hardware(self):
        """Set up the Raspberry Pi GPIO."""
        self.cleanup_gpio()

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
            time.sleep(0.05)

        # Reset MS430 to clear any previous state:
        self.i2c_bus.write_byte(
            self.sensor_constants.i2c_addr_7bit_sb_open,
            self.sensor_constants.reset_cmd
        )
        time.sleep(0.005)

        # Wait for reset completion and entry to standby mode
        while (gpio.input(self.sensor_constants.ready_pin) == 1):
            time.sleep(0.05)

        # Tell the Pi to monitor READY for a falling edge event
        # (high-to-low voltage change)
        gpio.add_event_detect(self.sensor_constants.ready_pin, gpio.FALLING)

    def get_gpio(self) -> gpio:
        """Return the initialized gpio module."""
        return gpio

    def change_sensor_mode(
        self, mode: Optional[int] = None, cycle_time: Optional[int] = None
    ):
        """Change the sensor cycle mode.

        The possibilities for the cycle mode are:
            SensorConstants().on_demand: Take a measurement when requested
            SensorConstants().cycle_mode: Take continuous measurements
            SensorConstants().standby_mode: Do nothing

        cycle_mode (int): Mode to start the sensor in.
            Default is None which will become:
                SensorConstants().on_demand (2)
        cycle_time (int): Time between reads on cycle mode.
            Default is None which will become: 5
        """
        self.mode = SensorMode(mode, cycle_time)

    def is_ready(self) -> bool:
        """Return True when ready.

        This means the device is ready for the next event.

        Returns:
            (bool): True when ready.
        """
        start = time.perf_counter()
        # Wait for the ready signal (falling edge) before continuing
        while (not gpio.event_detected(self.sensor_constants.ready_pin)):
            time.sleep(0.05)
            current = time.perf_counter()

            if current - start > self.TIMEOUT:
                raise IOError(
                    f'Ready pin not triggered within {self.TIMEOUT} second.'
                    'Please check the setup and try again.'
                )

        return True

    def cleanup_gpio(self):
        """Cleanup the gpio after execution."""
        gpio.cleanup()

    def standby(self):
        """Put the sensor into standby mode."""
        LOG.debug('Going into standby mode.')
        # Trigger the sensor into standby mode
        self.i2c_bus.write_byte(
            self.sensor_constants.i2c_7bit_address, self.mode.trigger_byte
        )

    def measure(self):
        """Take an on demand measurement."""
        LOG.debug('Taking an on demand measurement.')
        # Trigger an on demand measurement
        self.i2c_bus.write_byte(
            self.sensor_constants.i2c_7bit_address, self.mode.trigger_byte
        )

        try:
            if self.is_ready():
                self._get_all_data()

        except IOError as e:
            print(e)

        except Exception as e:
            print(e)
            traceback.print_exc()

    def cycle(self):
        """Take measurements on a cycle.

        This process runs in a seperate thread so it can be interrupted at
        any point.

        This will repeat until a keyboard interrupt is given.
        """
        LOG.debug('Taking cyclical measurements.')
        # Trigger a cyclical measurement
        self.i2c_bus.write_i2c_block_data(
            self.sensor_constants.i2c_7bit_address,
            self.sensor_constants.cycle_time_period_reg,
            [self.cycle_time],
        )

        self.cycle_status.active = True
        threading.Thread(target=self._run_cycle).start()

    def _run_cycle(self):
        """The actual cycle function.

        This is seperated out so that it can run in its own thread.
        """
        count = 1
        while self.cycle_status.is_active or count <= 20:
            # If the main thread is no longer alive, terminate the loop
            if not threading.main_thread().is_alive():
                break

            try:
                if self.is_ready():
                    self._get_all_data()

            except KeyboardInterrupt:
                print('Stopping')
                break

            except IOError as e:
                print(e)
                break

            except Exception as e:
                print(e)
                traceback.print_exc()
                break

            finally:
                count += 1

    def stop_cycle(self):
        """Stop the cycle measurements.

        This will terminate the loop in _run_cycle.
        """
        self.cycle_status.active = False

    def _get_all_data(self):
        """Get all the available data."""
        # Brief final sleep to stabalize sensors
        time.sleep(1.5)

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
            LOG.warning(self.int_aqi_accuracy)

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
