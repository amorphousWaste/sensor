#  simple_read_T_H.py

#  Example code for using the Metriful MS430 to measure humidity and
#  temperature.
#  This example is designed to run with Python 3 on a Raspberry Pi.

#  Demonstrates multiple ways of reading and displaying the temperature
#  and humidity data. View the output in the terminal. The other data
#  can be measured and displayed in a similar way.

#  Copyright 2020 Metriful Ltd.
#  Licensed under the MIT License - for further details see LICENSE.txt

#  For code examples, datasheet and user guide, visit
#  https://github.com/metriful/sensor

from sensor import SensorData

from unicode_constants import UnicodeConstants


def read_temp():
    """Simple example of reading the temperature and humidity."""
    sensor_data = SensorData()
    print(
        f'The temperature is: {sensor_data.temp_c:.1f}'
        f'{UnicodeConstants.celsius} '
        f'/ {sensor_data.temp_f}{UnicodeConstants.fahrenheit}'
    )
    print(f'The humidity is: {sensor_data.humidity:.1f} %')

    sensor_data.cleanup_gpio()


def read_sound():
    """Simple example of reading the sound level."""
    sensor_data = SensorData()
    print(f'The sound pressure level is: {sensor_data.spl_dba} dBA')

    sensor_data.cleanup_gpio()


if __name__ == '__main__':
    read_temp()
    read_sound()
