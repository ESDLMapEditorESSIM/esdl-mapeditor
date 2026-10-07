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

from esdl import esdl
from src.esdl_integration.processing.ESDLEnergySystem import process_area_KPIs_recursive
from extensions.profiles import Profiles


def get_es_visualization_options(es: esdl.EnergySystem) -> dict:
    visualization_options = dict()

    # check for kpi's
    top_area: esdl.Area = es.instance[0].area
    es_area_kpis = process_area_KPIs_recursive(top_area)
    displayed_area_name = top_area.name if top_area.name else es.name
    if len(es_area_kpis) > 0:
        visualization_options["kpis"] = {
            "es_id": es.id,
            "scope": displayed_area_name,
            "kpi_info": es_area_kpis,
            "message": es.name,
        }

    # check for animation data
    animation_fields = Profiles.get_animation_fields(es.id)
    if animation_fields:
        visualization_options["animation_esdl_data"] = {
            "es_id": es.id,
            "fields": animation_fields,
            "message": es.name,
            "filter_tag_name": None,
            "filter_tag_value": None,
        }

    return visualization_options
