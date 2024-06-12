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
from flask import session
from datetime import datetime
import threading
import time

import src.log as log
import os, glob

from esdl.resources.json import JsonResource, JsonOptions
from esdlproject import AbstractChange, HighLevelChange
from esdlproject.ProjectManager import ProjectManager, eobject_to_string, ESDLFormat
from src.tno.live_model_interface.message_types import HighLevelChangeMessage
from src.tno.live_model_interface.publisher import send_rabbitmq_message

logger = log.get_logger(__name__)
managed_sessions = dict()
ESH_KEY = 'esh'
PM_KEY = 'pm'
LAST_ACCESSED_KEY = 'last-accessed'
SESSION_TIMEOUT = 60*60*24  # 1 day
CLEANUP_INTERVAL = 60*60  # every hour


# def get_handler() -> EnergySystemHandler:
#     global managed_sessions
#     client_id = session['client_id']
#     if client_id in managed_sessions:
#         if ESH_KEY in managed_sessions[client_id]:
#             esh = managed_sessions[client_id][ESH_KEY]
#             logger.debug('Retrieve ESH client_id={}'.format(client_id))
#         else:
#             logger.warning('No EnergySystemHandler in session. Returning empty energy system')
#             esh = EnergySystemHandler()
#             set_handler(esh)
#         return esh
#     else:
#         logger.warning('Session has timed-out. Returning empty energy system')
#         esh = EnergySystemHandler()
#         from app import esdl_doc
#         esh.create_empty_energy_system('Untitled EnergySystem', '', 'Untitled Instance', 'Untitled Area', esdlVersion=esdl_doc.esdlVersion)
#         set_handler(esh)
#         return esh
#
#
# def set_handler(esh):
#     global managed_sessions
#     client_id = session['client_id']
#     logger.debug('Set ESH client_id={}'.format(client_id))
#     set_session(ESH_KEY, esh)

def on_change_recorded(change: HighLevelChange):
    """
    This function is called when a change is recorded on the UndoRedoCommandStack by adding this function
    as call back function to the ProjectManager's change listeners (see get_project_manager()).
    It will serialize a high level change (see ESDLProject ecore model) to send to interested live models.

    Parameters
    ----------
    change A HighLevelChange to be send away

    Returns
    -------

    """
    pm = get_project_manager()
    pm.rset.resource_factory['json'] = lambda uri: JsonResource(uri, indent=2)

    #options = {'encoder': DateTimeEncoder, 'indent': 2}
    options = {JsonOptions.INDENT: 2}
    hlc_string = eobject_to_string(change, ESDLFormat.JSON, options=options)
    logger.debug(f"Sending HighLevelChange: {hlc_string}")

    # uri = StringURI("high_level_change.json")
    # resource = pm.rset.create_resource(uri)
    # resource.append(hlc)
    # options = dict()
    # options['encoder'] = DateTimeEncoder
    # resource.save(options=options)
    # hlc_string = uri.getvalue()

    user_email = get_session('user-email')
    client_id = session['client_id']
    message = HighLevelChangeMessage(
        user_email=user_email,
        client_id=client_id,
        high_level_change=hlc_string
    )
    # logger.debug("Sending high level change on topic events.esdl.high_level_change")
    send_rabbitmq_message(message, "events.esdl.high_level_change")


def get_project_manager() -> ProjectManager:
    """
    Retrieve the ProjectManager from the session for the currently logged in user, or create a brand new one.
    """
    global managed_sessions
    client_id = session['client_id']
    if client_id in managed_sessions:
        if PM_KEY in managed_sessions[client_id]:
            pm = managed_sessions[client_id][PM_KEY]
            logger.debug('Retrieve pm client_id={}'.format(client_id))
        else:
            logger.warning('No Project Manager in session. Returning empty project manager')
            #pm = ProjectManager(on_change_recorded=on_change_recorded)
            pm = ProjectManager()
            pm.add_change_listener("session_manager", on_change_recorded)
            set_project_manager(pm)
        return pm
    else:
        logger.warning('Session has timed-out. Returning empty project manager')
        pm = ProjectManager()
        pm.add_change_listener("session_manager", on_change_recorded)
        set_project_manager(pm)
        return pm


def get_project_manager_with_client_id(client_id: str) -> ProjectManager:
    """
    Retrieve the ProjectManager from the session using the client_id but outside the request context.
    """
    global managed_sessions
    if client_id in managed_sessions:
        if PM_KEY in managed_sessions[client_id]:
            pm = managed_sessions[client_id][PM_KEY]
            logger.debug('Retrieve pm client_id={}'.format(client_id))
        else:
            logger.warning('No Project Manager in session. Returning empty project manager')
            pm = ProjectManager()
            pm.add_change_listener("session_manager", on_change_recorded)
            set_project_manager(pm)
        return pm
    else:
        logger.warning('Session has timed-out, no client_id available. ')
        raise KeyError("Session has timed-out, no client_id available. ")
        #pm = ProjectManager()
        #pm.add_change_listener("session_manager", on_change_recorded)
        #set_project_manager(pm)
        #return pm


def set_project_manager(pm: ProjectManager):
    global managed_sessions
    client_id = session['client_id']
    logger.debug('Set PM client_id={}'.format(client_id))
    set_session(PM_KEY, pm)


def valid_session():
    if 'client_id' in session:
        return True
    return False


def set_session(key, value):
    global managed_sessions
    #logger.debug('Current Thread %s' % threading.currentThread().getName())
    if 'client_id' not in session:
        logger.warning('No client_id for the session is available, cannot set value for key {}'.format(key))
        return
    client_id = session['client_id']
    if client_id not in managed_sessions:
        managed_sessions[client_id] = dict()
    managed_sessions[client_id][LAST_ACCESSED_KEY] = datetime.now()
    managed_sessions[client_id][key] = value
    #logger.debug(managed_sessions)


def get_session(key=None):
    """
    Return memory-bases session variable
    :param key: key to retrieve a value for. If key is None, it will return the whole session for this client
    :return:
    """
    global managed_sessions
    if 'client_id' not in session:
        logger.warning('No client id for the session is available, cannot return value for key {}'.format(key))
        return None
    client_id = session['client_id']
    if client_id not in managed_sessions:
        logger.warning('No client id in the managed_sessions is available, cannot return value for key {}'.format(key))
        return None
    else:
        if key is None:
            return managed_sessions[client_id]
        else:
            try:
                return managed_sessions[client_id][key]
            except:
                return None


def del_session(key):
    global managed_sessions
    client_id = session['client_id']
    if client_id not in managed_sessions:
        logger.warning('No client id for the session is available, cannot return value for key {}'.format(key))
        return None
    else:
        if key in managed_sessions[client_id]:
            del managed_sessions[client_id][key]


def clean_up_sessions():
    global managed_sessions
    logger.debug('Current Thread %s' % threading.currentThread().getName())
    logger.info('Clean up sessions: current number of sessions: {}'.format(len(managed_sessions)))
    for key in list(managed_sessions.keys()):  # make a copy of the keys in the list
        last_accessed = managed_sessions[key][LAST_ACCESSED_KEY]
        now = datetime.now()
        difference = (now - last_accessed).total_seconds()
        if difference > SESSION_TIMEOUT:
            logger.info('Cleaning up session with client_id={}'.format(key))
            del managed_sessions[key]


def schedule_session_clean_up():
    logger.info("Scheduling session clean-up thread every {} seconds".format(CLEANUP_INTERVAL))
    global managed_sessions
    clean_thread = threading.Thread(target=_clean_up_sessions_every_hour, name='Session-Cleanup-Thread')
    clean_thread.start()


def _clean_up_sessions_every_hour():
    while True:
        time.sleep(CLEANUP_INTERVAL)
        clean_up_sessions()


def get_session_for_esid(es_id, key):
    res = get_session(key)
    if res is not None:
        if es_id in res:
            return res[es_id]
    return None


def set_session_for_esid(es_id, key, value):
    res = get_session(key)
    if res is not None:
        res[es_id] = value
        set_session(key, res)
    else:
        new_dict = {}
        new_dict[es_id] = value
        set_session(key, new_dict)


def delete_sessions_on_disk(path: str):
    print('Cleaning up old sessions on disk...')
    files = glob.glob(path + '/*')
    for f in files:
        os.remove(f)
