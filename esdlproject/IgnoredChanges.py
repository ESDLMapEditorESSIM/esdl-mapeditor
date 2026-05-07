#  This work is based on original code developed and copyrighted by TNO 2026.
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
from esdlproject import DetailedChange

'''
Defines which attributes/references are ignored from parent variants for which classes
Format: change.ownerFragment + '/' + change.feature, e.g. //@instance.0/date ignores the date feature from instance.0
Implemented as a dictionary to have O(1) lookups as this is checked for every change when applied. 
This setup only works for the root ESDL features, more complex one require a different algorithm.
'''
_ignored_changes = {
    '//@instance.0/date': True
}


def ignored_change(change: DetailedChange):
    """
    Checks if a change can be ignored, because it is in the ignored changes list defined in this file.
    :param change: DetailedChange change to check
    :return: True when change can be ignored, False otherwise
    """
    key = change.ownerFragment + '/' + change.feature
    if _ignored_changes.get(key):
        return True
    return False
