"""Cycle Status."""

from typing import Optional


class CycleStatus(object):
    """Status of the cycle mode activity."""

    def __init__(self, active: Optional[bool] = False):
        """Init.

        Args:
            active (bool): True if active, otherwise false.
                Default is False
        """
        super(CycleStatus, self).__init__()
        self.active = active

    def is_active(self) -> bool:
        """Return the active state.

        Returns:
            self.active (bool): True if active, otherwise false.
        """
        return self.active
