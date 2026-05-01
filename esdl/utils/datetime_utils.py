#  This work is based on original code developed and copyrighted by TNO 2023.
#  Subsequent contributions are licensed to you by the developers of such code and are
#  made available to the Project under one or several contributor license agreements.
#
#  This work is licensed to you under the Apache License, Version 2.0.
#  You may obtain a copy of the license at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Contributors:
#      TNO         - Initial implementation
#  Manager:
#      TNO

from datetime import datetime
from contextlib import suppress


def parse_date(str_date: str):
    """
    Function to parse a date or datetime string to a datetime object. Tries many different formats to see
    if it can make sense out of the string. Both dates and times seperated by a 'T' and a space are supported.
    Both datetimes with and without timezone specification are supported

    :param str_date: input string representing a date or a datetime
    :return: datetime object based on the information in the input string
    """
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
                   '%Y-%m-%d',

                   # As a last resort, also try Dutch formatting of dates DD-MM-YYYY
                   '%d-%m-%YT%H:%M:%S.%f%z',
                   '%d-%m-%YT%H:%M:%S.%f%Z',
                   '%d-%m-%YT%H:%M:%S.%f',
                   '%d-%m-%YT%H:%M:%S%z',
                   '%d-%m-%YT%H:%M:%S%Z',
                   '%d-%m-%YT%H:%M:%S',
                   '%d-%m-%YT%H:%M',
                   '%d-%m-%Y %H:%M:%S.%f%z',
                   '%d-%m-%Y %H:%M:%S.%f%Z',
                   '%d-%m-%Y %H:%M:%S.%f',
                   '%d-%m-%Y %H:%M:%S%z',
                   '%d-%m-%Y %H:%M:%S%Z',
                   '%d-%m-%Y %H:%M:%S',
                   '%d-%m-%Y %H:%M',
                   '%d-%m-%Y',
                   )
        for fmt in formats:
            with suppress(ValueError):
                return datetime.strptime(str_date, fmt)
        raise ValueError('Date format is unknown')
