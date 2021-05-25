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

from dataclasses import dataclass


@dataclass
class CarrierMessage:
    """
    Message for carrier information
    """
    id: str = None
    name: str = None
    type: str = None

    emission: float = None
    energy_content: float = None
    energy_content_unit: str = None
    state_of_matter: str = None
    renewable_type: str = None
    voltage: float = None
    pressure: float = None
    supply_temperature: float = None
    return_temperature: float = None
