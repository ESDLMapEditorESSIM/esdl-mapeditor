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

from extensions.session_manager import get_session, get_project_manager


# todo: move to EnergySystemHandler
def remove_object_from_energysystem(es, object_id):
    pm = get_project_manager()
    active_es_id = get_session("active_es_id")
    obj = pm.get_by_id(active_es_id, object_id)
    obj.delete(recursive=True)


def remove_profile_from_port(port, profile_id):
    pm = get_project_manager()
    active_es_id = get_session("active_es_id")

    profile_list = port.profile

    for profile in set(profile_list):
        if profile.id == profile_id:
            profile_list.remove(profile)
            pm.remove_object_from_dict(active_es_id, profile, True)
