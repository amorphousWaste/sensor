"""Sensor Utilities.

Utilities for working with sensor data.

Copyright 2020 Metriful Ltd.
Licensed under the MIT License - for further details see LICENSE.txt

For code examples, datasheet and user guide, visit
https://github.com/metriful/sensor
"""

import csv
import json
import os
import yaml

from sensor import SensorData
from sensor_constants import SensorConstants
from unicode_constants import UnicodeConstants


def write_data(
    data: dict, file_path: str, overwrite: bool = True
) -> None:
    """Write the given data to a file.

    The extension of the file determines whay kind of file to write.

    Args:
        data (dict): Data to write.
        file_path (str): File to write the file to.
        overwrite (bool): Whether to overwrite the file.
            If False, data is appended.
            Default is True.
    """
    ext = os.path.splitext(file_path).lower()
    open_method = 'r' if overwrite else 'rw'

    with open(file_path, open_method) as out_file:
        # Write out the data to a csv file
        if ext == '.csv':
            fieldnames = list(data.keys())
            csv_writer = csv.DictWriter(out_file, fieldnames=fieldnames)
            # If it's a new file, write the header,
            # otherwise assume it's already there
            if open_method != 'r':
                csv_writer.writeheader()
            csv_writer.writerow(data)

        # Write the data to a JSON file
        elif ext == '.json':
            json.dump(data, out_file)

        # Write the data to a YAML file
        elif ext == '.yaml' or ext == '.yml':
            yaml.safe_dump(data, out_file)

        # Write the data as plain text
        else:
            data_to_write = []
            for key in data:
                value = data[key]
                data_to_write.append(f'{key}: {value}')
            out_file.write('\n'.join(data_to_write))


def format_air_data(
    sensor_data: SensorData, file_path: str = None, overwrite: bool = True
) -> None:
    """Write air data.

    Args:
        sensor_data (SensorData): Object containing sensor data.
        file_path (str): File to write the file to.
            If not given, return the data instead of writing it to a file.
            Default is None.
        overwrite (bool): Whether to overwrite the file.
            If False, data is appended.
            Default is True.
    """
    data = dict()
    data['Temperature (Celsius)'] = f'{SensorData.temp_c:.1f} C'
    data['Temperature (Fahrenheit)'] = f'{SensorData.temp_f:.1f} F'
    data['Pressure'] = f'{SensorData.pressure} Pa'
    data['Humidity'] = f'{SensorData.humidity:.1f} %'
    data['Gas Sensor Resistance'] = (
        f'{SensorData.gas_sensor_resistance} {UnicodeConstants.ohm}'
    )

    if file_path:
        write_data(file_path, data, overwrite)
    else:
        return data


def format_air_quality_data(
    sensor_data: SensorData, file_path: str = None, overwrite: bool = True
) -> None:
    """Write air quality data.

    Args:
        sensor_data (SensorData): Object containing sensor data.
        file_path (str): File to write the file to.
            If not given, return the data instead of writing it to a file.
            Default is None.
        overwrite (bool): Whether to overwrite the file.
            If False, data is appended.
            Default is True.
    """
    data = dict()
    if (SensorData.aqi_accuracy > 0):
        data['Air Quality Index'] = (
            f'{SensorData.aqi:.1f} ({SensorData.aqi_accuracy})'
        )
        data[f'Estimated CO{UnicodeConstants.subscript_2}'] = (
            f'{SensorData.co2e:.1f} ppm'
        )
        data['Equivalent Breath VOC'] = f'{SensorData.bvoc:.2f} ppm'

    else:
        data['Air Quality Index'] = 'N/A'
        data[f'Estimated CO{UnicodeConstants.subscript_2}'] = 'N/A'
        data['Equivalent Breath VOC'] = 'N/A'

    data['Air Quality Accuracy'] = SensorData.int_aqi

    if file_path:
        write_data(file_path, data, overwrite)
    else:
        return data


def format_light_data(
    sensor_data: SensorData, file_path: str = None, overwrite: bool = True
) -> None:
    """Write light data.

    Args:
        sensor_data (SensorData): Object containing sensor data.
        file_path (str): File to write the file to.
            If not given, return the data instead of writing it to a file.
            Default is None.
        overwrite (bool): Whether to overwrite the file.
            If False, data is appended.
            Default is True.
    """
    data = dict()
    data['Illuminance'] = f'{SensorData.lux:.2f} lux'
    data['White Light Level'] = f'{SensorData.white}'

    if file_path:
        write_data(file_path, data, overwrite)
    else:
        return data


def format_sound_data(
    sensor_data: SensorData, file_path: str = None, overwrite: bool = True
) -> None:
    """Write sound data.

    Args:
        sensor_data (SensorData): Object containing sensor data.
        file_path (str): File to write the file to.
            If not given, return the data instead of writing it to a file.
            Default is None.
        overwrite (bool): Whether to overwrite the file.
            If False, data is appended.
            Default is True.
    """
    data = dict()
    data['A-weighted Sound Pressure Level'] = f'{SensorData.spl_dba:.1f} dBA'

    for i in range(0, len(SensorData.spl_bands_db)):
        data[
            f'Frequency Band {i + 1} '
            f'({SensorConstants.sound_band_mids_Hz[i]} Hz SPL)'
        ] = f'{SensorData.spl_bands_db[i]:.1f} dB'

    dict['Peak Sound Amplitude'] = f'{SensorData.peak_amp:.2f} mPa'

    if file_path:
        write_data(file_path, data, overwrite)
    else:
        return data


def format_particle_data(
    sensor_data: SensorData, file_path: str = None, overwrite: bool = True
) -> None:
    """Write particle data.

    Args:
        sensor_data (SensorData): Object containing sensor data.
        file_path (str): File to write the file to.
            If not given, return the data instead of writing it to a file.
            Default is None.
        overwrite (bool): Whether to overwrite the file.
            If False, data is appended.
            Default is True.
    """
    data = dict()
    data['Particle Sensor Duty Cycle'] = f'{SensorData.duty_cycle_pc:.2f} %'
    data['Particle Concentration'] = (
        f'{SensorData.concentration:.2f} {SensorData.conc_unit}'
    )

    if SensorData.particle_data_valid == 0:
        data['Particle data valid'] = 'No (Initializing)'
    else:
        data['Particle data valid'] = 'Yes'

    if file_path:
        write_data(file_path, data, overwrite)
    else:
        return data
