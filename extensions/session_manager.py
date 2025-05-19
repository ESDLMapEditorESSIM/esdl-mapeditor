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
import glob
import threading
import time
from datetime import datetime
import pickle
import os
from pathlib import Path

from flask import session

import src.log as log
from esdlproject.ProjectManager import ProjectManager
from src.settings import PERSIST_SESSIONS, SESSION_PERSISTENCE_PATH, SESSION_PERSISTENCE_FILE, DEFAULT_PROJECT_PATH

SESSION_MANAGER_LISTENER_ID = "session_manager"

logger = log.get_logger(__name__)
managed_sessions = dict()
ESH_KEY = "esh"
PM_KEY = "pm"
LAST_ACCESSED_KEY = "last-accessed"
SESSION_TIMEOUT = 60 * 60 * 24  # 1 day
CLEANUP_INTERVAL = 60 * 60  # every hour

# Do not persist these keys to disk.
EXCLUDE_PERSISTENCE_SESSION_KEYS = [
    PM_KEY,
    'process_energysystem_lock',
    'shape_dictionary',
    'conn_list',
    'asset_list',
    'building_list',
    'area_bld_list',
    'es_info_list',
    'active_es_id',
]


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


def get_project_manager() -> ProjectManager | None:
    """
    Retrieve the ProjectManager from the session for the currently logged in user, or create a brand new one.
    """
    client_id = session["client_id"]
    return get_project_manager_for_client_id(client_id)


def get_project_manager_for_client_id(client_id: str) -> ProjectManager:
    """
    Retrieve the ProjectManager from the session using the client_id. Call this directly if you are outside the
    request context, otherwise get_project_manager might be more convenient.
    """
    # Import to prevent circular import.
    from src.tno.projects.core import create_new_project_manager
    global managed_sessions
    if client_id in managed_sessions:
        if PM_KEY in managed_sessions[client_id]:
            pm = managed_sessions[client_id][PM_KEY]
        else:
            logger.warning("No Project Manager in session. Returning empty project manager")
            pm = create_new_project_manager(client_id=client_id)
        return pm
    else:
        logger.warning("Session has timed-out, no client_id available. ")
        raise KeyError("Session has timed-out, no client_id available. ")


def set_project_manager(pm: ProjectManager, client_id=None):
    """
    Set the ProjectManager in the session for the provided client_id. If not provided, get it from the session.
    """
    # Import to prevent circular import.
    from src.tno.projects.core import on_change_recorded
    global managed_sessions
    if client_id is None:
        client_id = session["client_id"]
    if not pm.has_change_listener(SESSION_MANAGER_LISTENER_ID):
        pm.add_change_listener(SESSION_MANAGER_LISTENER_ID, on_change_recorded)
        logger.debug("Set PM client_id={} with listener for ESDL changes for LMI".format(client_id))
    else:
        logger.debug("Set PM client_id={}".format(client_id))
    set_session(PM_KEY, pm, client_id=client_id)


def valid_session():
    if "client_id" in session:
        return True
    return False


def set_session(key, value, client_id=None):
    """
    Set memory-based session variable. Also update the last accessed time for this session.
    """
    global managed_sessions
    if client_id is None:
        client_id = session["client_id"]
    if client_id not in managed_sessions:
        managed_sessions[client_id] = dict()
    managed_sessions[client_id][LAST_ACCESSED_KEY] = datetime.now()
    managed_sessions[client_id][key] = value
    save_sessions_to_disk()


def get_session(key=None, client_id=None, default_value=None):
    """
    Return memory-based session variable
    :param key: key to retrieve a value for. If key is None, it will return the whole session for this client
    :param client_id: client_id to use to get session variables, defaults to the client_id in the session, but
        for out of context calls, you can provide a client_id
    :param default_value: default value of the variable if key is not found. This value is stored in the session with
           this key.
    :return: the whole session object if key=None, the value for key if available, default_value if specified, or none
           if key cannot be found
    """
    global managed_sessions
    if not client_id:
        if "client_id" not in session:
            logger.warning("No client id for the session is available, cannot return value for key {}".format(key))
            return None
        client_id = session["client_id"]
    if client_id not in managed_sessions:
        logger.warning("No client id in the managed_sessions is available, cannot return value for key {}".format(key))
        return None
    else:
        # update last access
        managed_sessions[client_id][LAST_ACCESSED_KEY] = datetime.now()
        if key is None:
            return managed_sessions[client_id]
        else:
            try:
                return managed_sessions[client_id][key]
            except KeyError:
                if default_value:
                    managed_sessions[key] = default_value
                    return default_value
                else:
                    return None


def del_session(key):
    """
    Delete memory-based session variable.
    :param key:
    :return:
    """
    global managed_sessions
    client_id = session["client_id"]
    if client_id not in managed_sessions:
        logger.warning("No client id for the session is available, cannot return value for key {}".format(key))
        return None
    else:
        if key in managed_sessions[client_id]:
            del managed_sessions[client_id][key]


def clean_up_sessions():
    global managed_sessions
    logger.debug("Current Thread %s" % threading.current_thread().name)
    logger.info("Clean up sessions: current number of sessions: {}".format(len(managed_sessions)))
    for key in list(managed_sessions.keys()):  # make a copy of the keys in the list
        last_accessed = managed_sessions[key][LAST_ACCESSED_KEY]
        now = datetime.now()
        difference = (now - last_accessed).total_seconds()
        if difference > SESSION_TIMEOUT:
            logger.info("Cleaning up session with client_id={}".format(key))
            del managed_sessions[key]


def schedule_session_clean_up():
    logger.info("Scheduling session clean-up thread every {} seconds".format(CLEANUP_INTERVAL))
    global managed_sessions
    clean_thread = threading.Thread(target=_clean_up_sessions_every_hour, name="Session-Cleanup-Thread")
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
    print("Cleaning up old sessions on disk...")
    files = glob.glob(path + "/*")
    for f in files:
        os.remove(f)


def save_sessions_to_disk():
    """Save all managed sessions to disk, excluding ProjectManager objects."""
    if not PERSIST_SESSIONS:
        return

    global managed_sessions
    try:
        Path(SESSION_PERSISTENCE_PATH).mkdir(parents=True, exist_ok=True)
        storage_path = os.path.join(SESSION_PERSISTENCE_PATH, SESSION_PERSISTENCE_FILE)

        # Create a serializable version of managed_sessions.
        serializable_sessions = {}

        for client_id, client_session in managed_sessions.items():
            serializable_sessions[client_id] = {}

            # Copy all session data except the ProjectManager and locks.
            for key, value in client_session.items():
                if key not in EXCLUDE_PERSISTENCE_SESSION_KEYS:
                    serializable_sessions[client_id][key] = value

        with open(storage_path, 'wb') as f:
            pickle.dump(serializable_sessions, f)

        logger.debug(f"Successfully saved {len(managed_sessions)} sessions to disk")
    except Exception as e:
        logger.error(f"Error saving sessions to disk: {str(e)}")


def load_sessions_from_disk():
    """
    Load session data from disk. Should be called at startup.
    """
    if not PERSIST_SESSIONS:
        return
    global managed_sessions
    storage_path = os.path.join(SESSION_PERSISTENCE_PATH, SESSION_PERSISTENCE_FILE)

    if os.path.exists(storage_path):
        try:
            with open(storage_path, 'rb') as f:
                loaded_sessions = pickle.load(f)

            # Assign loaded sessions to managed_sessions. Do not overwrite or things break.
            for client_id, client_session in loaded_sessions.items():
                if client_id not in managed_sessions:
                    managed_sessions[client_id] = client_session

            if DEFAULT_PROJECT_PATH:
                for client_id, client_session in managed_sessions.items():
                    pm = get_project_manager_for_client_id(client_id)
                    # Read the project file from the default path
                    try:
                        with open(DEFAULT_PROJECT_PATH, 'r') as f:
                            project = f.read()
                            pm.load_from_string(project)
                    except Exception as e:
                        logger.error(f"Error loading default project for client {client_id}: {str(e)}")

            # Each client will get a new ProjectManager when they reconnect
            logger.info(f"Successfully loaded {len(managed_sessions)} sessions from disk")
        except Exception as e:
            logger.error(f"Error loading sessions from disk: {str(e)}")
    else:
        logger.info("No saved sessions found, starting with empty session store")
