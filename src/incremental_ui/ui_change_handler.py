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
from flask import session, request
from flask_socketio import emit
from pyecore.ecore import EObject

from esdl import esdl
from esdl.resources.xmlresource import XMLResource
from esdl.undo import ChangeSource, ChangeContext
from esdlproject import HighLevelChange, DetailedChange, Set, Add, Remove
from extensions.session_manager import managed_sessions, get_session
from src.incremental_ui.connections import create_connection, remove_connection_from_conn_list
from src.log import get_logger
from src.process_es_area_bld import find_and_send_KPI_information_in_ESDL, call_process_energy_system

INCREMENTAL_UI_LISTENER_ID = "incremental_ui_updates"

logger = get_logger(__name__)


class ResolveException(Exception):
    pass


def safe_resolve(resource: XMLResource, fragment: str) -> EObject:
    try:
        eobject = resource.resolve(fragment)
        return eobject
    except Exception:
        raise ResolveException(f"Can't resolve {fragment} in {resource}")


def change_handler(high_level_change: HighLevelChange, context: ChangeContext):
    """
    Handles changes emited from EMF / UndoRedoCommandStack
    Parameters
    ----------
    high_level_change: HighLevelChange to handle
    context: context of the change

    Returns
    -------
    Nothing
    """

    if context.source == ChangeSource.INTERNAL:
        # don't act on internal changes
        return

    if not context.client_id and not context.flask_app and not context.resource:
        logger.debug("No client_id/app/resource in change context, can't do updates to GUI")
        return

    es = context.resource.contents[0]
    #pm = get_project_manager_with_client_id(context.client_id)

    with context.flask_app.test_request_context():
        session['client_id'] = context.client_id
        # todo replace managed_sessions with get_session(client_id=xx, 'socketio_sid')
        request.sid = managed_sessions[context.client_id]['socketio_sid']
        request.namespace = '/esdl'
        ui_update_handled = False
        if context.source == ChangeSource.EXTERNAL:
            main_area = None  # for finding out if KPIs need to be updated
            # Handle changes from live model
            for change in high_level_change.change:
                try:
                    change: DetailedChange
                    if change.feature == "connectedTo":
                        # connectedTo changed, update gui accordingly
                        if isinstance(change, Add):
                            # add a connection, as this code is running after adding this change to the es, this must work
                            logger.info("incremental_ui: adding connection")
                            owner = safe_resolve(context.resource, change.ownerFragment)
                            target = safe_resolve(context.resource, change.objectFragment)

                            if isinstance(owner, esdl.Port) and isinstance(target, esdl.Port):
                                connection = create_connection(from_port=owner, to_port=target)
                                conn_list_all = get_session(key='conn_list', client_id=context.client_id)
                                conn_list = conn_list_all[es.id]  # get conn_list for es_id
                                conn_list.append(connection)
                                emit('clear_connections')  # clear current active layer connections
                                emit('add_connections', {'es_id': es.id, 'conn_list': conn_list})
                                ui_update_handled = True

                        if isinstance(change, Remove):
                            # add a connection, as this code is running after adding this remove has already happened.
                            # but references should still work, so we can update the UI
                            logger.debug("incremental_ui: removing connection")
                            owner = safe_resolve(context.resource, change.ownerFragment)
                            target = safe_resolve(context.resource, change.objectFragment)
                            if isinstance(owner, esdl.Port) and isinstance(target, esdl.Port):
                                conn_list_all = get_session(key='conn_list', client_id=context.client_id)
                                conn_list = conn_list_all[es.id]  # get conn_list for es_id
                                emit('remove_single_connection',
                                 {'from-port-id': owner.id, 'to-port-id': target.id, 'es_id': es.id})
                                remove_connection_from_conn_list(owner, target, conn_list)
                                ui_update_handled = True
                    elif change.feature == "KPIs" and isinstance(change, Set):  # high level KPI section has changed
                        owner = safe_resolve(context.resource, change.ownerFragment)
                        if isinstance(owner, esdl.Area):
                            logger.info(f"incremental_ui: update for KPIs of {owner} (postponed)")
                            parent = owner.eContainer()
                            prev_parent = owner
                            while isinstance(parent, esdl.Area):
                                prev_parent = parent
                                parent = parent.eContainer()

                            main_area = prev_parent

                            # do update area KPIs
                            # find_and_send_KPI_information_in_ESDL(owner)

                except ResolveException as e:
                    logger.warning("Resolve failure:", e)
                    continue



        elif context.source == ChangeSource.FRONT_END:
            logger.debug("Not yet implemented: changes from Front-end")
            pass

        if main_area:  # for KPI calculation
            logger.debug(f"incremental_ui: KPI update for: {main_area}")
            find_and_send_KPI_information_in_ESDL(main_area)
            ui_update_handled = True

        if not ui_update_handled:
            logger.debug("Could not determine incremental UI update, doing a full process energy system")
            # re-process whole energy system
            #es = pm.get_active_energy_system()
            call_process_energy_system.submit(force_update_es_id=es.id, zoom=False)  # run in seperate thread



