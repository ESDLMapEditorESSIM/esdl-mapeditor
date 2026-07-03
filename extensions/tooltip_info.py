#  This work is based on original code developed and copyrighted by TNO 2023.
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

from flask import Flask
from flask_socketio import SocketIO

import esdl
from extensions.session_manager import get_session, get_project_manager
import src.log as log


logger = log.get_logger(__name__)


class TooltipInfo:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self):
        logger.info('Registering TooltipInfo extension')

        @self.flask_app.route('/tooltip_info/<es_id>/<object_id>')
        def get_tooltip_info(es_id, object_id):
            if es_id is None:
                es_id = get_session('active_es_id')
            pm = get_project_manager()
            es_edit = pm.get_energy_system_by_id(es_id)
            active_es_id = es_edit.id

            results = {
                "costInformation": False,
                "hasConstraints": False,
                "profiles": False,
            }
            try:
                object = pm.get_by_id(active_es_id, object_id)
            except KeyError:
                # if object_id cannot be found, we return 'empty' results
                return results

            if isinstance(object, esdl.Asset):
                # Check for costInformation
                if object.costInformation:
                    for ci in object.costInformation.eAllContents():
                        if isinstance(ci, esdl.GenericProfile):
                            results["costInformation"] = True
                            break

                # Check for constraints
                if hasattr(object, 'constraint') and len(object.constraint) > 0:
                    results["hasConstraints"] = True

            if isinstance(object, esdl.ConnectableAsset):
                # check for port profiles
                results["profiles"] = dict()

                for p in object.port:
                    # for now take the first port that contains profile information
                    port_profile_info = {
                        "port_id": p.id,
                        "port_type": p.eClass.name,
                        "port_name": p.name,
                        "profs_info": []
                    }
                    profs_info = list()
                    for prof in p.profile:
                        prof_info = {
                            "profile_id": prof.id,
                            "name": prof.name if prof.name else "",
                        }

                        if isinstance(prof, esdl.SingleValue):
                            prof_info["attr_name"] = "value"
                            prof_info["value"] = prof.value
                        elif isinstance(prof, esdl.InfluxDBProfile):
                            prof_info["attr_name"] = "multiplier"
                            prof_info ["value"] = prof.multiplier

                        profs_info.append(prof_info)

                    port_profile_info["profs_info"] = profs_info
                    results["profiles"][p.id] = port_profile_info

            return results
