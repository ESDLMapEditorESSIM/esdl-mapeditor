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
SESSION_TIMEOUT = 60*60*24 # 1 day
CLEANUP_INTERVAL = 60*60 # every hour

def get_handler():
    global managed_sessions
    client_id = session['client_id']
    if client_id in managed_sessions:
        if ESH_KEY in managed_sessions[client_id]:
            esh = managed_sessions[client_id][ESH_KEY]
            print('Retrieve ESH client_id={}, es.name={}'.format(client_id, esh.get_energy_system().name))
        else:
            print('No esh in session. Returning empty energy system')
            esh = EnergySystemHandler()
            esh.create_empty_energy_system('Untitled EnergySystem', '', 'Untitled Instance', 'Untitled Area')
            set_handler(esh)
        return esh
    else:
        print('Session has timed-out. Returning empty energy system')
        esh = EnergySystemHandler()
        esh.create_empty_energy_system('Untitled EnergySystem', '', 'Untitled Instance', 'Untitled Area')
        set_handler(esh)
        return esh


def set_handler(esh):
    global managed_sessions
    client_id = session['client_id']
    print('Set ESH client_id={}, es.name={}'.format(client_id, esh.get_energy_system().name))
    set_session(ESH_KEY, esh)


def valid_session():
    if 'client_id' in session:
        return True
    return False

def set_session(key, value):
    global managed_sessions
    #print('Current Thread %s' % threading.currentThread().getName())
    if 'client_id' not in session:
        warn('No client_id for the session is available, cannot set value for key %s' % key)
    client_id = session['client_id']
    if client_id not in managed_sessions:
        managed_sessions[client_id] = dict()
    managed_sessions[client_id][LAST_ACCESSED_KEY] = datetime.now()
    managed_sessions[client_id][key] = value
    #print(managed_sessions)


def get_session(key=None):
    """
    Return memory-bases session variable
    :param key: key to retrieve a value for. If key is None, it will return the whole session for this client
    :return:
    """
    global managed_sessions
    if 'client_id' not in session:
        warn('No client id for the session is available, cannot return value for key %s' % key)
        return None
    client_id = session['client_id']
    if client_id not in managed_sessions:
        warn('No client id in the managed_sessions is available, cannot return value for key %s' % key)
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
        warn('No client id for the session is available, cannot return value for key %s' % key)
        return None
    else:
        del managed_sessions[client_id][key]


# does not work
def clean_up_sessions():
    global managed_sessions
    print('Current Thread %s' % threading.currentThread().getName())
    print('Clean up sessions: current number of sessions: {}'.format(len(managed_sessions)))
    for key in list(managed_sessions.keys()): # make a copy of the keys in the list
        last_accessed = managed_sessions[key][LAST_ACCESSED_KEY]
        now = datetime.now()
        difference = (now - last_accessed).total_seconds()
        if difference > SESSION_TIMEOUT:
            print('Cleaning up session with client_id=%s' % key)
            del managed_sessions[key]


def schedule_session_clean_up():
    print("Scheduling session clean-up thread every %d seconds" % CLEANUP_INTERVAL)
    global managed_sessions
    clean_thread = threading.Thread(target=_clean_up_sessions_every_hour, name='Session-Cleanup-Thread')
    clean_thread.start()


def _clean_up_sessions_every_hour():
    while True:
        time.sleep(CLEANUP_INTERVAL)
        clean_up_sessions()
