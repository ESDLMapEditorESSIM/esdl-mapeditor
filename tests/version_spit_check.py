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

#version = ''
#import re
#m = re.match(r"\D??(\d{1,2}+)\.?(\d{1,2}+)\.?(\d+)?.*", version)
# splitted = version.split('.')
# major = splitted[0] if splitted[0] is not None and splitted[0] is not '' else 1
# minor = splitted[1] if len(splitted) > 1 and splitted[1] is not None else '0'
# rest = ''.join(splitted[2:]) if len(splitted) > 2 else ''
# # increment
# try:
#     import re
#     minor = re.split(r"\D", minor)[0]
#     if len(splitted) > 1 and splitted[1] is not None:
#         minor = int(minor) + 1
#     else
# except ValueError:
#     minor = 1
# # store
# version_updated = "{}.{}".format(major, minor)
# if rest is not '':
#     version_updated = "{}.{}".format(version_updated, rest)
# print(version_updated)

version = 2
version = '' if version is None else str(version)
try:
    import re
    splitted = re.split(r"\D", version)
    print(splitted)
    major = splitted[0]
    major = int(major) + 1
except ValueError:
    major = 1
print(str(major))
