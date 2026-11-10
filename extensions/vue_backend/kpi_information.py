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

from pyecore.ecore import EObject

import esdl
from esdl.units.parser import unit_to_string
from extensions.vue_backend.messages.object_properties_message import KPIInfo


def get_kpi_information(obj: EObject) -> list[KPIInfo]:
    """
    Collect read-only KPI values, including nested KPIs and distributions.
    """
    kpis = getattr(obj, 'KPIs', None)
    if kpis is None:
        return []

    result: list[KPIInfo] = []
    for kpi in kpis.eAllContents():
        if isinstance(kpi, esdl.KPI):
            result.append(serialize_kpi(kpi, len(result)))
    return result


def serialize_kpi(kpi: esdl.KPI, key: int = 0) -> KPIInfo:
    """
    Serialize one KPI, including its unit and distribution items.
    """
    names = [kpi.name or kpi.eClass.name]
    parent = kpi.eContainer()
    while isinstance(parent, esdl.KPI):
        names.insert(0, parent.name or parent.eClass.name)
        parent = parent.eContainer()

    qau = kpi.quantityAndUnit
    if isinstance(qau, esdl.QuantityAndUnitReference):
        qau = qau.reference
    # A quantity-and-unit reference may be empty.
    unit = unit_to_string(qau) if qau is not None else ''
    info: KPIInfo = {
        'key': key,
        'name': ' / '.join(names),
        'description': kpi.description,
        'type': kpi.eClass.name,
        'unit': unit,
    }
    if isinstance(kpi, esdl.DistributionKPI):
        info['items'] = []
        if kpi.distribution is not None:
            for item in kpi.distribution.eContents:
                if isinstance(item, esdl.StringItem):
                    label = item.label
                else:
                    label = f'{item.from_} to {item.to}'
                info['items'].append({'label': label, 'value': item.value, 'unit': unit})
    else:
        info['value'] = kpi.value
    return info
