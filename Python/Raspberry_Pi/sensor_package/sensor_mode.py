"""Sensor Mode."""

from typing import Optional

from .sensor_constants import SensorConstants


class SensorMode(object):
    """Sensor mode used to operate the sensor."""

    def __init__(
        self, mode: Optional[int] = None, cycle_time: Optional[int] = None
    ):
        """Init.

        The possibilities for the cycle mode are:
            SensorConstants().standby_mode: Do nothing (0)
            SensorConstants().cycle_mode: Take continuous measurements (1)
            SensorConstants().on_demand: Take a measurement when requested (2)

        Args:
            mode (int): Mode value.
                Default is None which will become: SensorConstants().on_demand
            cycle_time (int): Time between reads on cycle mode.
                Default is None which will become: 5
        """
        super(SensorMode, self).__init__()

        mode = mode or SensorConstants().on_demand
        self.cycle_time = cycle_time or 5

        self.set_mode(mode, cycle_time)

    def validate_mode(self, mode: int) -> bool:
        """Validate the mode value is valid.

        Args:
            mode (int): Mode value.

        Returns:
            (bool): True if the mode is valid, otherwise False.
        """
        if mode in [
            SensorConstants().standby_mode,
            SensorConstants().cycle_mode,
            SensorConstants().on_demand,
        ]:
            return True

        else:
            return False

    def set_mode(self, mode: int):
        """Set the mode.

        The mode is validated first, and if invalid, a ValueError is thrown.

        Args:
            mode (int): Mode value.
        """
        if not self.validate_mode(mode):
            raise ValueError(f'The given mode value {mode} is not supported.')

        if mode == SensorConstants().standby_mode:
            self.mode_name = 'standby'
            self.mode_value = mode
            self.trigger_byte = self.SensorConstants().standby_mode_cmd

        elif mode == SensorConstants().cycle_mode:
            self.mode_name = 'cycle'
            self.mode_value = mode
            self.trigger_byte = self.SensorConstants().cycle_mode_cmd

        elif mode == SensorConstants().on_demand:
            self.mode_name = 'on_demand'
            self.mode_value = mode
            self.trigger_byte = self.SensorConstants().on_demand_measure_cmd

    def __str__(self):
        """String magic method."""
        output = [
            f'Mode name: {self.mode_name}',
            f'Cycle time: {self.cycle_time}',
            f'Mode value: {self.mode_value}',
            f'Trigger byte: {self.trigger_byte}',
        ]
        return '\n'.join(output)

    def __dict__(self):
        """Dictionary magic method."""
        return {
            'mode_name': self.mode_name,
            'cycle_time': self.cycle_time,
            'mode_value': self.mode_value,
            'trigger_byte': self.trigger_byte,
        }
