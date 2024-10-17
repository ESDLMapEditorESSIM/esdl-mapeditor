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
        file_path = func.__code__.co_filename
        logger.debug(
            f"{func.__name__} ran in {runtime}s (path: {file_path})",
            function=func.__name__,
            runtime=runtime,
            path=file_path,
        )
        return result

    return wrapper


# def display_mem_usage(snapshot, key_type = 'lineno', limit = 10):
#    """ show memory stats, requires tracemalloc, but that seems to slow down everything. """
#     # from https://stackoverflow.com/questions/552744/how-do-i-profile-memory-usage-in-python
#     print("Creating memory stats...")
#     snapshot = snapshot.filter_traces((
#         tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
#         tracemalloc.Filter(False, "<unknown>"),
#     ))
#     print("Create statistics")
#     top_stats = snapshot.statistics(key_type)
#
#     print("Memory stats: Top %s lines" % limit)
#     for index, stat in enumerate(top_stats[:limit], 1):
#         frame = stat.traceback[0]
#         # replace "/path/to/module/file.py" with "module/file.py"
#         filename = os.sep.join(frame.filename.split(os.sep)[-2:])
#         print("#%s: %s:%s: %.1f KiB"
#         %(index, filename, frame.lineno, stat.size / 1024))
#         line = linecache.getline(frame.filename, frame.lineno).strip()
#         if line:
#             print('    %s' % line)
#
#     other = top_stats[limit:]
#     if other:
#         size = sum(stat.size for stat in other)
#     print("%s other: %.1f KiB" % (len(other), size / 1024))
#     total = sum(stat.size for stat in top_stats)
#     print("Total allocated size: %.1f KiB" % (total / 1024))