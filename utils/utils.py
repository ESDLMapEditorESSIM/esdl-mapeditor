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
