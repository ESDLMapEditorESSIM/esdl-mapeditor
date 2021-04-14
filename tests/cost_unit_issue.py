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

from extensions.vue_backend.cost_information import _change_cost_unit
from esdl.esdl_handler import EnergySystemHandler
from uuid import uuid4
from esdl import esdl
import re

cost_unit_string = "EUR/kWh/yr"
qau = esdl.QuantityAndUnitType(id=str(uuid4()), physicalQuantity=esdl.PhysicalQuantityEnum.COST, description='Cost in '+cost_unit_string)
_change_cost_unit(qau, cost_unit_string)
print(EnergySystemHandler.attr_to_dict(qau))

if re.match(r"\w+/kWh", cost_unit_string):
    print('yes')
else:
    print('no')

if re.match(r".+/yr$", cost_unit_string):
    print("\yr")
    qau.perTimeUnit = esdl.TimeUnitEnum.YEAR
else:
    print('no /yr')

