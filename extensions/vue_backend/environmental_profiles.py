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

from uuid import uuid4
from pyecore.ecore import EDate
from esdl import esdl
from esdl.processing.ESDLEcore import instantiate_type
from extensions.session_manager import get_handler, get_session
from extensions.profiles import Profiles
from utils.utils import str2float
from utils.datetime_utils import parse_date


def get_environmental_profiles_information(ep):
    """


    :param ep: instance of the esdl.EnvironmentalProfiles class
    :return: information that can be send to the frontend
    """

