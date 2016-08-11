import re

RANGE_REGEX = re.compile('bytes=(.*)-(.*)')


class RangeNotSatisfiableException(Exception):
    code = 416
    message = 'Requested Range Not Satisfiable. '

    def __init__(self, message=''):
        self.message += message


def parse_range(range_str):
    range_dict = {}
    range_match = RANGE_REGEX.search(range_str)
    if not range_match:
        raise RangeNotSatisfiableException('Range must be in format: bytes=start-end')

    start_range = range_match.group(1)
    end_range = range_match.group(2)

    try:
        start_range = int(start_range) if start_range else 0
        end_range = int(end_range) if end_range else None
    except ValueError:
        raise RangeNotSatisfiableException('Invalid start or end interval.')

    if start_range < 0:
        raise RangeNotSatisfiableException('Start of the interval cannot be less than zero.')

    if end_range is not None and start_range >= end_range:
        raise RangeNotSatisfiableException('End interval must be larger that start interval.')

    range_dict['start_range'] = start_range if start_range else 0
    range_dict['end_range'] = end_range if end_range else None

    return range_dict
