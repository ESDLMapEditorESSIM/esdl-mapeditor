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

from extensions.session_manager import get_session, set_session
import src.log as log

logger = log.get_logger(__name__)


def get_object_properties_info(obj):
    """
    Builds up a dictionary with information about the object, with categorized parameters such that the frontend
    can visualize these in a proper way

    :param EObject obj: the object for which the information must be collected
    :return dict: the dictionary with all required information
    """

