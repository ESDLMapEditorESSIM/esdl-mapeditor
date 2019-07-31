from flask import session
from esdl.esdl_handler import EnergySystemHandler
from warnings import warn
from datetime import datetime
import threading
import time
# module that handles the ESDL
# TODO: remove old sessions

managed_sessions = dict()
ESH_KEY = 'esh'
LAST_ACCESSED_KEY = 'last-accessed'
SESSION_TIMEOUT = 60 #*60*24 # 1 day
CLEANUP_INTERVAL = 60 # every hour

def get_handler():
    id = session['client_id']
    if id in managed_sessions:
        esh = managed_sessions[id][ESH_KEY]
        print('Retrieve ESH client_id={}, es.name={}'.format(id, esh.get_energy_system().name))
        return esh
    else:
        print('Session has timed-out. Returning empty energy system')
        esh = EnergySystemHandler()
        esh.create_empty_energy_system('Untitled EnergySystem', '', 'Untitled Instance', 'Untitled Area')
        set_handler(esh)
        return esh


def set_handler(esh):
    id = session['client_id']
    print('Set ESH client_id={}, es.name={}'.format(id, esh.get_energy_system().name))
    set_session(ESH_KEY, esh)


def valid_session():
    if 'client_id' in session:
        return True
    return False

def set_session(key, value):
    id = session['client_id']
    if id not in managed_sessions:
        managed_sessions[id] = dict()
    managed_sessions[id][LAST_ACCESSED_KEY] = datetime.now()
    managed_sessions[id][key] = value

def get_session(key=None):
    """
    Return memory-bases session variable
    :param key: key to retrieve a value for. If key is None, it will return the whole session for this client
    :return:
    """
    id = session['client_id']
    if id not in managed_sessions:
        warn('No client id for the session is available, cannot return value for key %s' % key)
        return None
    else:
        if key is None:
            return managed_sessions[id]
        else:
            return managed_sessions[id][key]

def del_session(key):
    id = session['client_id']
    if id not in managed_sessions:
        warn('No client id for the session is available, cannot return value for key %s' % key)
        return None
    else:
        del managed_sessions[id][key]


def clean_up_sessions():
    global managed_sessions
    print('Clean up sessions: number of sessions: {}'.format( managed_sessions))
    for key,value in managed_sessions.items():
        last_accessed = value[LAST_ACCESSED_KEY]
        now = datetime.now()
        difference = (now - last_accessed).total_seconds()
        if difference > SESSION_TIMEOUT:
            print('Cleaning up session with client_id=%s' % key)
            del managed_sessions[key]


def schedule_session_clean_up():
    clean_thread = threading.Thread(target=_clean_up_sessions_every_hour, name='Session Cleanup Thread')
    clean_thread.start()


def _clean_up_sessions_every_hour():
    while True:
        time.sleep(CLEANUP_INTERVAL)
        clean_up_sessions()
