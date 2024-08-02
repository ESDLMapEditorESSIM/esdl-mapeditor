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
import uuid
from datetime import datetime

import pymongo
from pymongo import ReturnDocument
from pymongo.database import Database

import src.log as log
from enum import Enum

from src.tno.mongo.core import mongo_client
from src.tno.locking import NamedLocker

"""
External models database based on MongoDB
"""

logger = log.get_logger(__name__)

VALUE_UNSET = "<<Should be set>>"


class RunStatus(Enum):
    """Possible Run status."""

    SUBMITTED = "SUBMITTED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"


class ExternalModelsStorage:
    """
    Class to store external model results in a MongoDB database.

    The `set` operation is thread-safe, using a NamedLocker to lock on the identifier.

    This class does not provide any transactional guarantees, so it is possible that a setting is overwritten by
    another thread. This can be prevented by using a lock outside this class, around the specific operation that
    requires transactional guarantees.
    """

    def __init__(self, named_locker: NamedLocker, database_uri: str = None, database: str = "esdl_external_models"):
        logger.info("Setting up UserSettings with mongoDB")
        self.named_locker = named_locker
        self.database = database
        try:
            # Either use the shared client, or create a specific client.
            if database_uri is None:
                logger.info("Using default Mongo client")
                self.client = mongo_client
            else:
                logger.info("Connecting with specified Mongo database", database_uri=database_uri)
                self.client = pymongo.MongoClient(database_uri)
            self.db: Database = self.client[database]  # esdl_mapeditor_settings
        except Exception as e:
            raise RuntimeError("Can't connect to MongoDB for UserSettings" + str(e)) from e

    def add_model_run(self, model_name: str, input_esdl: str, run_data: dict, user):
        """
        Set a setting for the given identifier. If the setting does not exist, it will be created.

        This operation is thread-safe, using a NamedLocker to lock on the identifier.

        :param setting_type: The type of setting (user, project or system)
        :param identifier: The unique identifier for the setting. E.g. user name or project name.
        :param setting_name: The name of the setting.
        :param value: The value of the setting.
        :return: The updated setting object.
        """
        doc = (
            get_default_model_run_values()
            | {"user": user, "model_name": model_name, "input_esdl": input_esdl}
            | run_data
        )
        if VALUE_UNSET in doc.keys():
            raise RuntimeError(f"Cannot save model run, unset required values: {doc.keys()}")
        with self.named_locker.lock(model_name):
            self.db[model_name].insert_one(doc)

    def get_model_run(self, model_name: str, run_id: str):
        """
        Resets the setting_name and removes it from the dict.

        :param setting_type: The type of setting (user, project or system)
        :param identifier: The unique identifier for the setting. E.g. user name or project name.
        :param setting_name: The name of the setting.
        :return:
        """
        with self.named_locker.lock(model_name):
            model_run = self.db[model_name].find_one({"run_id": run_id}, projection={"_id": False})
        return model_run

    def delete_model_run(self, model_name: str, run_id: str):
        """
        Resets the setting_name and removes it from the dict.

        :param setting_type: The type of setting (user, project or system)
        :param identifier: The unique identifier for the setting. E.g. user name or project name.
        :param setting_name: The name of the setting.
        :return:
        """
        with self.named_locker.lock(model_name):
            deleted_model_data = self.db[model_name].find_one_and_delete({"run_id": run_id}, projection={"_id": False})
        return deleted_model_data

    def get_model_runs_for_current_user(self, model_name: str, user: str, user_projects: list[str]) -> list:
        with self.named_locker.lock(model_name):
            myquery = {"$or": [{"user": user}, {"projects": {"$elemMatch": {"$in": user_projects}}}]}
            models_cursor = self.db[model_name].find(myquery, projection={"_id": False})
        return list(models_cursor)

    def update_model_run(self, model_name: str, run_id: str, updated_values: dict):
        return self.db[model_name].find_one_and_update(
            {"run_id": run_id},
            {"$set": updated_values},
            projection={"_id": False},
            upsert=False,
            return_document=ReturnDocument.AFTER,
        )

    def clear(self):
        """
        Clear the settings database. This will remove all settings. Only use this with command line tools!
        """
        self.client.drop_database(self.database)


def get_default_model_run_values() -> dict:
    return dict(
        user=VALUE_UNSET,
        projects=[],
        model_name=VALUE_UNSET,
        run_id=str(uuid.uuid4()),
        run_name=VALUE_UNSET,
        input_esdl=VALUE_UNSET,
        status=RunStatus.SUBMITTED.value,
        progress_fraction=0,
        submitted_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
