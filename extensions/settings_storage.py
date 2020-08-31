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

from pymongo import MongoClient
from pymongo.database import Database, Collection
import src.log as log
from enum import Enum

"""
UserSettings database based on MongoDB

Settings object:
{
    type: [user, project or system]: SettingType enum
    name: <unique user name / project/name>
    setting1: <value>
}


Example for WMS layers":

{
    type: [user, project or system]: SettingType enum
    name: <unique user name / project name / 'mapeditor'>
    layers: { <dict with layers}}
}
"""

logger = log.get_logger(__name__)


# different types of settings
class SettingType(Enum):
    USER = 'user'
    PROJECT = 'project'
    SYSTEM = 'system'


class SettingsStorage:

    SYSTEM_NAME_IDENTIFIER = 'mapeditor' # only one identifier of system settings for mapeditor

    def __init__(self, database_uri: str = 'mongodb://localhost:27017/', database: str = 'esdl_mapeditor_settings'):
        logger.info("Setting up UserSettings with mongoDB at " + database_uri)
        self.database = database
        try:
            self.client = MongoClient(database_uri)
            self.db: Database = self.client[database] # esdl_mapeditor_settings
            self.settings: Collection = self.db.settings
        except Exception as e:
            logger.error('Can\'t connect to MongoDB for UserSettings' + str(e))

    def set(self, setting_type: SettingType, identifier: str, setting_name: str, value):
        if not self.settings: return None
        mapeditor_settings_obj = self.settings.find_one({'type': setting_type.value, 'name': identifier}, {setting_name: 1})
        if mapeditor_settings_obj is None:
            # unknown identifier, create first
            doc = {'type': setting_type.value, 'name': identifier, setting_name: value}
            self.settings.insert_one(doc)
        else:
            return self.settings.update_one(
                {'_id': mapeditor_settings_obj['_id']},
                {'$set': {setting_name: value}}, upsert=False)

    def delete(self, setting_type: SettingType, identifier: str, setting_name: str):
        """
        Resets the setting_name and removes it from the dict
        :param setting_type:
        :param identifier:
        :param setting_name:
        :return:
        """
        mapeditor_settings_obj = self.settings.find_one({'type': setting_type.value, 'name': identifier})
        if mapeditor_settings_obj is None:
            return None
        else:
            return self.settings.update_one(
                {'_id': mapeditor_settings_obj['_id']},
                {'$unset': {setting_name: ""}}, upsert=False)

    def get(self, setting_type: SettingType, identifier: str, setting_name: str):
        if not self.settings: return None
        mapeditor_settings_obj = self.settings.find_one({'type': setting_type.value, 'name': identifier}, {'type':1, 'name': 1, setting_name: 1})
        if mapeditor_settings_obj is None:
            raise KeyError('No such setting \'{}\' for {} {}'.format(setting_name, setting_type.value, identifier))
            return None
        if setting_name in mapeditor_settings_obj:
            return mapeditor_settings_obj[setting_name]
        else:
            raise KeyError('No such setting \'{}\' for {} {}'.format(setting_name, setting_type.value, identifier))

    def has(self, setting_type: SettingType, identifier: str, setting_name: str):
        doc_count = self.settings.count_documents({'type': setting_type.value, 'name': identifier, setting_name: { "$exists": True }})
        if doc_count > 0:
            return True
        return False

    def set_user(self, user:str, setting_name:str, value):
        return self.set(SettingType.USER, user, setting_name, value)

    def get_user(self, user:str, setting_name:str):
        return self.get(SettingType.USER, user, setting_name)

    def has_user(self, user: str, setting_name: str):
        return self.has(SettingType.USER, user, setting_name)

    def del_user(self, user:str, setting_name:str):
        return self.delete(SettingType.USER, user, setting_name)

    def get_all_settings_for_type(self, type_name: SettingType):
        return list(self.settings.find({"type": type_name.value}))

    def get_all_settings_for_identifier(self, type_name: SettingType, identifier: str):
        """
        E.g. get all settings for project X
        or get all settings for user Y
        :param type_name:
        :param identifier:
        :return:
        """
        return list(self.settings.find({"type": type_name.value, 'name': identifier}, {'type': 0, 'name': 0, '_id': 0}))


    def set_project(self, project_name:str, setting_name:str, value):
        return self.set(SettingType.PROJECT, project_name, setting_name, value)

    def get_project(self, project_name:str, setting_name:str):
        return self.get(SettingType.PROJECT, project_name, setting_name)

    def del_project(self, project_name:str, setting_name:str):
        return self.delete(SettingType.PROJECT, project_name, setting_name)

    def has_project(self, project_name: str, setting_name: str):
        return self.has(SettingType.PROJECT, project_name, setting_name)

    def set_system(self, setting_name:str, value):
        return self.set(SettingType.SYSTEM, SettingsStorage.SYSTEM_NAME_IDENTIFIER, setting_name, value)

    def get_system(self, setting_name:str):
        return self.get(SettingType.SYSTEM, SettingsStorage.SYSTEM_NAME_IDENTIFIER, setting_name)

    def del_system(self, setting_name:str):
        return self.delete(SettingType.SYSTEM, SettingsStorage.SYSTEM_NAME_IDENTIFIER, setting_name)

    def has_system(self, setting_name: str):
        return self.has(SettingType.SYSTEM, SettingsStorage.SYSTEM_NAME_IDENTIFIER, setting_name)

    def size(self):
        return self.settings.count_documents({})

    """
    Clears database!
    """
    def clear(self):
        self.client.drop_database(self.database)



