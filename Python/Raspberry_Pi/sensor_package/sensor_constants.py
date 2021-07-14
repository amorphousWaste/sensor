"""Sensor Constants.

This file defines constant values which are used in the control
of the Metriful MS430 board and the interpretation of its output data.
All values have been taken from the MS430 datasheet.

Copyright 2020 Metriful Ltd.
Licensed under the MIT License - for further details see LICENSE.txt

For code examples, datasheet and user guide, visit
https://github.com/metriful/sensor
"""


class SensorConstants(object):
    """Constants."""

    def __init__(self):
        """Init."""
        super(SensorConstants, self).__init__()

        # Settings registers
        self.particle_sensor_select_reg = 0x07
        self.light_interrupt_enable_reg = 0x81
        self.light_interrupt_threshold_reg = 0x82
        self.light_interrupt_type_reg = 0x83
        self.light_interrupt_polarity_reg = 0x84
        self.sound_interrupt_enable_reg = 0x85
        self.sound_interrupt_threshold_reg = 0x86
        self.sound_interrupt_type_reg = 0x87
        self.cycle_time_period_reg = 0x89

        # Executable commands
        self.on_demand_measure_cmd = 0xE1
        self.reset_cmd = 0xE2
        self.cycle_mode_cmd = 0xE4
        self.standby_mode_cmd = 0xE5
        self.light_interrupt_clr_cmd = 0xE6
        self.sound_interrupt_clr_cmd = 0xE7

        # Read the operational mode
        self.op_mode_read = 0x8A

        # Read data for whole categories
        self.air_data_read = 0x10
        self.air_quality_data_read = 0x11
        self.light_data_read = 0x12
        self.sound_data_read = 0x13
        self.particle_data_read = 0x14

        # Read individual data quantities
        self.t_read = 0x21
        self.p_read = 0x22
        self.h_read = 0x23
        self.g_read = 0x24
        self.aqi_read = 0x25
        self.co2e_read = 0x26
        self.bvoc_read = 0x27
        self.aqi_accuracy_read = 0x28
        self.illuminance_read = 0x31
        self.white_light_read = 0x32
        self.spl_read = 0x41
        self.spl_bands_read = 0x42
        self.sound_peak_read = 0x43
        self.sound_stable_read = 0x44
        self.duty_cycle_read = 0x51
        self.concentration_read = 0x52
        self.particle_valid_read = 0x53

        # I2C address of sensor board: can select using solder bridge
        # If solder bridge is left open
        self.i2c_addr_7bit_sb_open = 0x71
        # If solder bridge is soldered closed
        self.i2c_addr_7bit_sb_closed = 0x70
        # NOTE: I don't know what the point of this value being duplicated is
        self.i2c_7bit_address = self.i2c_addr_7bit_sb_open

        # Values for enabling/disabling of sensor functions
        self.enabled = 1
        self.disabled = 0

        # Device modes
        self.standby_mode = 0
        self.cycle_mode = 1
        self.on_demand = 2

        self.light_interrupt_threshold_bytes = 3
        self.sound_interrupt_threshold_bytes = 2

        # Frequency bands for sound level measurement
        self.sound_freq_bands = 6
        self.sound_band_mids_hz = [125, 250, 500, 1000, 2000, 4000]
        self.sound_band_edges_hz = [88, 177, 354, 707, 1414, 2828, 5657]

        # Sound interrupt type
        self.sound_int_type_latch = 0
        self.sound_int_type_comp = 1

        # Maximum for illuminance measurement and threshold setting
        self.max_lux_value = 3774

        # Light interrupt type
        self.light_int_type_latch = 0
        self.light_int_type_comp = 1

        # Light interrupt polarity
        self.light_int_pol_positive = 0
        self.light_int_pol_negative = 1

        # Decoding the temperature integer.fraction value format
        self.temperature_value_mask = 0x7F
        self.temperature_sign_mask = 0x80

        # Particle sensor module selection
        self.particle_sensor_off = 0
        self.particle_sensor_ppd42 = 1
        self.particle_sensor_sds011 = 2

        # Byte lengths for each readable data quantity and data category
        self.t_bytes = 2
        self.p_bytes = 4
        self.h_bytes = 2
        self.g_bytes = 4
        self.air_data_bytes = 12

        self.aqi_bytes = 3
        self.co2e_bytes = 3
        self.bvoc_bytes = 3
        self.aqi_accuracy_bytes = 1
        self.air_quality_data_bytes = 10

        self.illuminance_bytes = 3
        self.white_bytes = 2
        self.light_data_bytes = 5

        self.spl_bytes = 2
        self.spl_bands_bytes = (2 * self.sound_freq_bands)
        self.sound_peak_bytes = 3
        self.sound_stable_bytes = 1
        self.sound_data_bytes = 18

        self.duty_cycle_bytes = 2
        self.concentration_bytes = 3
        self.particle_valid_bytes = 1
        self.particle_data_bytes = 6

        # GPIO (input/output) header pin numbers.
        # These must match the hardware wiring.
        self.light_int_pin = 7  # Raspberry Pi pin 7 connects to LIT
        self.sound_int_pin = 8  # Raspberry Pi pin 8 connects to SIT
        self.ready_pin = 11  # Raspberry Pi pin 11 connects to RDY
