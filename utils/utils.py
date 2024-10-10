#  This work is based on original code developed and copyrighted by TNO 2020.
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

import re
import time
from functools import wraps

from src.log import get_logger

logger = get_logger(__name__)

def str2float(string):
    try:
        f = float(string)
        return f
    except:
        return 0.0


def _unCamelCase(match):
    s = match.group()
    return s[0].upper() + s[1:].lower()


def camelCaseToWords(s):
    # if no lowercase characters found, just use the word as given, e.g. COP
    if re.match(r"^[A-Z]+$", s):
        return s
    return ' '.join(list(map(_unCamelCase, re.finditer(r"([a-z]+)|([A-Z][a-z]*)", s))))


def timed(func):
    """This decorator prints the execution time for the decorated function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        runtime = round(end - start, 2)
        logger.debug(
            "{} ran in {}s".format(func.__name__, runtime),
            function=func.__name__,
            runtime=runtime,
        )
        return result

    return wrapper