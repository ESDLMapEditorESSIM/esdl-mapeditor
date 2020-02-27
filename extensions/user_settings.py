from pymongo import MongoClient
from pprint import pprint
import logging

"""
UserSettings database based on MongoDB
"""
# - MONGO_HOST=mongo_test
#      - MONGO_DATABASE=esdl_mapeditor
#      - MONGO_PORT=27017

"""
Settings object:
{
    type: [user, project or system]
    name: <unique user name>
    settings: 
    {
        "setting1": <value>,
        "setting2": { "dict": {"key": value"} }
    } 
}

"""


log = logging.getLogger(__name__)

# different types of settings
USER_TYPE = 'user'
PROJECT_TYPE = 'project'
SYSTEM_TYPE = 'system'
SYSTEM_NAME = 'mapeditor'

class UserSettings:
    def __init__(self, database_uri: str = 'mongodb://localhost:27017/', database: str = 'esdl_mapeditor_settings'):
        log.info("Setting up UserSettings with mongoDB at " + database_uri)
        self.database = database
        try:
            self.client = MongoClient(database_uri)
            self.db = self.client[database] # esdl_mapeditor_settings
            self.settings = self.db.settings
        except Exception:
            log.error('Can\'t connect to MongoDB for UserSettings')

    def _set(self, type_name: str, identifier: str, setting_name: str, value):
        mapeditor_settings_obj = self.settings.find_one({'type': type_name, 'name': identifier})
        if mapeditor_settings_obj is None:
            # unknown user, create first
            doc = {'type': type_name, 'name': identifier, 'settings': {setting_name: value}}
            self.settings.insert_one(doc)
        else:
            pprint(mapeditor_settings_obj)
            self.settings.update_one(
                {'_id': mapeditor_settings_obj['_id']},
                {'$set': {'settings.'+setting_name: value}}, upsert=False)

    def _get(self, type_name: str, identifier: str, setting_name: str):
        mapeditor_settings_obj = self.settings.find_one({'type': type_name, 'name': identifier})
        if mapeditor_settings_obj is None:
            raise KeyError('No such '+ type_name + ': ' + identifier)
        pprint(mapeditor_settings_obj)
        settings = mapeditor_settings_obj['settings']
        #if not hasattr(settings, key):
        #    raise KeyError('User ' + user + ' has no key defined for \'' + key + '\'')
        #else:
        return settings[setting_name]

    def set_user(self, user:str, setting_name:str, value):
        return self._set(USER_TYPE, user, setting_name, value)

    def get_user(self, user:str, setting_name:str):
        return self._get(USER_TYPE, user, setting_name)

    def get_all_settings(self, type_name):
        for setting in self.settings.find({"type": type_name}):
            # todo return list
            pprint(setting)


    def set_project(self, project_name:str, setting_name:str, value):
        return self._set(PROJECT_TYPE, project_name, setting_name, value)

    def get_project(self, project_name:str, setting_name:str):
        return self._get(PROJECT_TYPE, project_name, setting_name)

    def set_system(self, setting_name:str, value):
        return self.set(SYSTEM_TYPE, SYSTEM_NAME, setting_name, value)

    def get_system(self, system_name:str, setting_name:str):
        return self.get(SYSTEM_TYPE, SYSTEM_NAME, setting_name)




    def size(self):
        return self.settings.count_documents({})

    """
    Clears database!
    """
    def clear(self):
        self.client.drop_database(self.database)



