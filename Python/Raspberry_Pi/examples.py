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

import argparse
import time

from typing import Optional

from sensor_package.sensor import Sensor

from sensor_package.sensor_constants import SensorConstants
from sensor_package.unicode_constants import UnicodeConstants


def get_args():
    """Get the args from argparse.

    Returns:
        args (dict): Arguments from argparse.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-t',
        '--temp',
        action='store_true',
        help='Get the temperature data.',
    )
    parser.add_argument(
        '-s',
        '--sound',
        action='store_true',
        help='Get the sound data.',
    )
    parser.add_argument(
        '-c',
        '--cycle',
        type=int,
        help='Run in a loop every n seconds.',
    )
    parser.add_argument(
        '-w',
        '--write',
        type=str,
        help='Write the data to a file.',
    )

    args = parser.parse_args()

    return vars(args)


def read_temp(write_data: Optional[str] = ''):
    """Simple example of reading the temperature and humidity."""
    sensor = Sensor()
    sensor.measure()
    print(
        f'The temperature is: {sensor.temp_c:.1f}'
        f'{UnicodeConstants().celsius} '
        f'/ {sensor.temp_f}{UnicodeConstants().fahrenheit}'
    )
    print(f'The humidity is: {sensor.humidity:.1f} %')

    sensor.cleanup_gpio()


def read_sound(write_data: Optional[str] = ''):
    """Simple example of reading the sound level."""
    sensor = Sensor()
    sensor.measure()
    print(f'The sound pressure level is: {sensor.spl_dba} dBA')

    sensor.cleanup_gpio()


def cycle_reads(cycle_time: [int], write_data: Optional[str] = ''):
    """Simple example of cyclicaly reading data."""
    sensor = Sensor(
        cycle_mode=SensorConstants().cycle_mode, cycle_time=cycle_time
    )
    sensor.cycle()
    x = 1
    # while True:
    while x <= 10:
        print(
            f'The temperature is: {sensor.temp_c:.1f}'
            f'{UnicodeConstants().celsius} '
            f'/ {sensor.temp_f}{UnicodeConstants().fahrenheit}'
        )
        print(f'The humidity is: {sensor.humidity:.1f} %')
        print(f'The sound pressure level is: {sensor.spl_dba} dBA')
        print('-' * 50)
        x += 1
        time.sleep(cycle_time)

    sensor.standby()


if __name__ == '__main__':
    args = get_args()

    write_data = args.get('write', '')

    if args.get('cycle', False):
        try:
            cycle_reads(write_data)
        except KeyboardInterrupt:
            print('Stopping')

    else:
        if args.get('temp', False):
            read_temp(write_data)

        if args.get('sound', False):
            read_sound(write_data)
