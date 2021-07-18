"""Setup."""

import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s %(asctime)s> %(message)s',
    datefmt='%Y/%m/%d %I:%M:%S%p',
)
LOG = logging.getLogger('Sensor')
