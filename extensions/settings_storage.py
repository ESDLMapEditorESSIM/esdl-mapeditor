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
from collections import defaultdict
from multiprocessing import Lock, Manager

from pymongo import MongoClient, ReturnDocument
from pymongo.database import Database, Collection

from extensions.session_manager import get_session
import src.log as log
from enum import Enum

from src.tno.locking import NamedLocker

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
    """
    Class to store user settings in a MongoDB database.

    The settings are stored in a collection with the following structure:
    {
        type: [user, project or system]: SettingType enum
        name: <unique user name / project/name>
        setting1: <value>
    }

    The `set` operation is thread-safe, using a NamedLocker to lock on the identifier.

    This class does not provide any transactional guarantees, so it is possible that a setting is overwritten by
    another thread. This can be prevented by using a lock outside this class, around the specific operation that
    requires transactional guarantees.
    """

    SYSTEM_NAME_IDENTIFIER = 'mapeditor'  # only one identifier of system settings for mapeditor

    def __init__(self, named_locker: NamedLocker, database_uri: str = 'mongodb://localhost:27017/', database: str = 'esdl_mapeditor_settings'):
        logger.info("Setting up UserSettings with mongoDB at " + database_uri)
        self.named_locker = named_locker
        self.database = database
        try:
            self.client = MongoClient(database_uri)
            self.db: Database = self.client[database]  # esdl_mapeditor_settings
            self.settings: Collection = self.db.settings
        except Exception as e:
            raise RuntimeError("Can't connect to MongoDB for UserSettings" + str(e)) from e
        self._merge_duplicates()

    def set(self, setting_type: SettingType, identifier: str, setting_name: str, value):
        """
        Set a setting for the given identifier. If the setting does not exist, it will be created.

        This operation is thread-safe, using a NamedLocker to lock on the identifier.

        :param setting_type: The type of setting (user, project or system)
        :param identifier: The unique identifier for the setting. E.g. user name or project name.
        :param setting_name: The name of the setting.
        :param value: The value of the setting.
        :return: The updated setting object.
        """
        if not self.settings:
            raise RuntimeError("No settings collection found in database.")
        if identifier is None:
            raise Exception("No identifier provided for setting.")

        with self.named_locker.lock(identifier):
            mapeditor_settings_obj = self.settings.find_one_and_update(
                {'type': setting_type.value, 'name': identifier},
                {'$set': {setting_name: value}}, upsert=False,
                projection={setting_name: 1},
                return_document=ReturnDocument.AFTER,
            )
            if mapeditor_settings_obj is None:
                # unknown setting and/or identifier: create first
                doc = {'type': setting_type.value, 'name': identifier, setting_name: value}
                self.settings.insert_one(doc)
                return doc
            else:
                return mapeditor_settings_obj

    def delete(self, setting_type: SettingType, identifier: str, setting_name: str):
        """
        Resets the setting_name and removes it from the dict.

        :param setting_type: The type of setting (user, project or system)
        :param identifier: The unique identifier for the setting. E.g. user name or project name.
        :param setting_name: The name of the setting.
        :return:
        """
        with self.named_locker.lock(identifier):
            mapeditor_settings_obj = self.settings.find_one({'type': setting_type.value, 'name': identifier})
            if mapeditor_settings_obj is None:
                return None
            else:
                return self.settings.update_one(
                    {'_id': mapeditor_settings_obj['_id']},
                    {'$unset': {setting_name: ""}}, upsert=False)

    def get(self, setting_type: SettingType, identifier: str, setting_name: str):
        """
        Get a setting for the given identifier.

        :param setting_type: The type of setting (user, project or system)
        :param identifier: The unique identifier for the setting. E.g. user name or project name.
        :param setting_name: The name of the setting.
        :return: The value of the setting.
        """
        if not self.settings:
            return None

        mapeditor_settings_obj = self.settings.find_one({'type': setting_type.value, 'name': identifier},
                                                        {'type': 1, 'name': 1, setting_name: 1})
        if mapeditor_settings_obj is None:
            raise KeyError('No setting object found while searching for setting \'{}\' for {} {}'.format(setting_name,
                                                                                                         setting_type.value,
                                                                                                         identifier))

        if setting_name in mapeditor_settings_obj:
            return mapeditor_settings_obj[setting_name]
        else:
            raise KeyError('No such setting \'{}\' for {} {}'.format(setting_name, setting_type.value, identifier))

    def has(self, setting_type: SettingType, identifier: str, setting_name: str) -> bool:
        """
        Check if a setting exists for the given identifier. Please note that this does not provide any guarantees
        that no other thread will overwrite the setting in the meantime.

        :param setting_type: The type of setting (user, project or system)
        :param identifier: The unique identifier for the setting. E.g. user name or project name.
        :param setting_name: The name of the setting.
        :return:
        """
        doc_count = self.settings.count_documents(
            {'type': setting_type.value, 'name': identifier, setting_name: {"$exists": True}})
        if doc_count > 0:
            return True
        return False

    def set_user(self, user: str, setting_name: str, value):
        """
        Set a setting for the given user.
        """
        return self.set(SettingType.USER, user, setting_name, value)

    def get_user(self, user: str, setting_name: str):
        """
        Get a setting for the given user.
        """
        return self.get(SettingType.USER, user, setting_name)

    def has_user(self, user: str, setting_name: str):
        return self.has(SettingType.USER, user, setting_name)

    def del_user(self, user: str, setting_name: str):
        return self.delete(SettingType.USER, user, setting_name)

    def set_for_current_user(self, setting_name: str, value):
        """
        Set a setting for the currently logged in user.
        """
        user = get_session('user-email')
        return self.set_user(user, setting_name, value)

    def get_for_current_user(self, setting_name: str):
        """
        Get setting for currently logged in user.
        """
        user = get_session('user-email')
        return self.get_user(user, setting_name)

    def del_for_current_user(self, setting_name: str):
        """
        Get setting for currently logged in user.
        """
        user = get_session('user-email')
        return self.del_user(user, setting_name)

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

    def set_project(self, project_name: str, setting_name: str, value):
        return self.set(SettingType.PROJECT, project_name, setting_name, value)

    def get_project(self, project_name: str, setting_name: str):
        return self.get(SettingType.PROJECT, project_name, setting_name)

    def del_project(self, project_name: str, setting_name: str):
        return self.delete(SettingType.PROJECT, project_name, setting_name)

    def has_project(self, project_name: str, setting_name: str):
        return self.has(SettingType.PROJECT, project_name, setting_name)

    def set_system(self, setting_name: str, value):
        return self.set(SettingType.SYSTEM, SettingsStorage.SYSTEM_NAME_IDENTIFIER, setting_name, value)

    def get_system(self, setting_name: str):
        return self.get(SettingType.SYSTEM, SettingsStorage.SYSTEM_NAME_IDENTIFIER, setting_name)

    def del_system(self, setting_name: str):
        return self.delete(SettingType.SYSTEM, SettingsStorage.SYSTEM_NAME_IDENTIFIER, setting_name)

    def has_system(self, setting_name: str):
        return self.has(SettingType.SYSTEM, SettingsStorage.SYSTEM_NAME_IDENTIFIER, setting_name)

    def size(self):
        """
        Get the number of setting instances in the database.
        :return:
        """
        return self.settings.count_documents({})

    def clear(self):
        """
        Clear the settings database. This will remove all settings. Only use this with command line tools!
        """
        self.client.drop_database(self.database)

    def _merge_duplicates(self):
        """
        Find all settings of type 'user' with duplicate names and attempt to merge them together.

        This issue used to happen before adding the NamedLocker, where multiple threads could write to the same
        setting at the same time. This would result in multiple settings for the same user, with different values.

        This should not happen anymore, so after a while this function can be removed.
        """
        duplicates = self.settings.aggregate([
            {"$match": {"type": "user"}},
            {"$group": {"_id": {"name": "$name"}, "uniqueIds": {"$addToSet": "$_id"}, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}}
        ])
        for duplicate in duplicates:
            logger.info(f"Found duplicate user settings", user=duplicate['_id']['name'])
            unique_ids = duplicate['uniqueIds']
            first_id = unique_ids.pop(0)
            for id in unique_ids:
                first = self.settings.find_one({"_id": first_id})
                second = self.settings.find_one({"_id": id})
                for key in second:
                    if key not in first:
                        first[key] = second[key]
                self.settings.update_one({"_id": first_id}, {"$set": first})
                self.settings.delete_one({"_id": id})
                logger.info(f"Merged settings", user=duplicate['_id']['name'])
