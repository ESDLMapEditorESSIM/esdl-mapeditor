from datetime import datetime
from contextlib import suppress


def parse_date(str_date):
    try:
        return datetime.fromisoformat(str_date)
    except Exception:
        formats = ('%Y-%m-%dT%H:%M:%S.%f%z',
                   '%Y-%m-%dT%H:%M:%S.%f%Z',
                   '%Y-%m-%dT%H:%M:%S.%f',
                   '%Y-%m-%dT%H:%M:%S%z',
                   '%Y-%m-%dT%H:%M:%S%Z',
                   '%Y-%m-%dT%H:%M:%S',
                   '%Y-%m-%dT%H:%M',
                   '%Y-%m-%d %H:%M:%S.%f%z',
                   '%Y-%m-%d %H:%M:%S.%f%Z',
                   '%Y-%m-%d %H:%M:%S.%f',
                   '%Y-%m-%d %H:%M:%S%z',
                   '%Y-%m-%d %H:%M:%S%Z',
                   '%Y-%m-%d %H:%M:%S',
                   '%Y-%m-%d %H:%M',
                   '%Y-%m-%d',)
        for fmt in formats:
            with suppress(ValueError):
                return datetime.strptime(str_date, fmt)
        raise ValueError('Date format is unknown')
