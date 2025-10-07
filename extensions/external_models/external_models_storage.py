#  This work is based on original code developed and copyrighted by TNO 2025.
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

from src.settings import settings_storage_config
from src.tno.mongo.core import mongo_client
from src.tno.locking import NamedLocker

"""
External models database based on MongoDB
"""

logger = log.get_logger(__name__)

VALUE_UNSET = "<<Should be set>>"

# items in an external model run doc
USER = "user"
USER_GROUP_PATHS = "user_group_paths"
MODEL_NAME = "model_name"
MODEL_JOB_ID = "model_job_id"
RUN_ID = "run_id"
RUN_NAME = "run_name"
INPUT_ESDL = "input_esdl"
OUTPUT_ESDL = "output_esdl"
STATUS = "status"
PROGRESS_FRACTION = "progress_fraction"
PROGRESS_MESSAGE = "progress_message"
LOGS = "logs"
ESDL_FEEDBACK = "esdl_feedback"
SUBMITTED_TO_EXTERNAL_MODEL_AT = "submitted_to_external_model_at"
LAST_UPDATED_TO_EXTERNAL_MODEL_AT = "last_updated_from_external_model_at"
MODEL_SPECIFIC_INPUT = "model_specific_input"
MODEL_SPECIFIC_OUTPUT = "model_specific_output"


class RunStatus(Enum):
    """Run status options."""

    SUBMITTED = "SUBMITTED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"
    NEED_INPUT = "NEED_INPUT"


class ExternalModelsStorage:
    """
    Class to store external model results in a MongoDB database.

    The `set` operation is thread-safe, using a NamedLocker to lock on the identifier.

    This class does not provide any transactional guarantees, so it is possible that a setting is overwritten by
    another thread. This can be prevented by using a lock outside this class, around the specific operation that
    requires transactional guarantees.
    """

    def __init__(self, named_locker: NamedLocker, database_uri: str = None) -> None:
        logger.info("Setting up UserSettings with mongoDB")
        self.named_locker = named_locker
        self.database = settings_storage_config["database"]
        self.collection_name = settings_storage_config["external_models_collection"]
        try:
            # Either use the shared client, or create a specific client.
            if database_uri is None:
                logger.info("Using default Mongo client")
                self.client = mongo_client
            else:
                logger.info("Connecting with specified Mongo database", database_uri=database_uri)
                self.client = pymongo.MongoClient(database_uri)
            db: Database = self.client[self.database]  # esdl_mapeditor_settings
            self.collection = db[self.collection_name]
        except Exception as e:
            raise RuntimeError("Can't connect to MongoDB for UserSettings" + str(e)) from e

    def add_model_run(
        self,
        model_name: str,
        model_job_id: str,
        run_name: str,
        input_esdl: str,
        run_input_data: dict,
        user_name: str,
        logs: str = None,
        status: RunStatus = RunStatus.SUBMITTED,
    ) -> dict:
        """
        Add an external model run to the database, a run ID will be created.

        :param model_name: The name of the external model.
        :param model_job_id: The ID of the model to be added.
        :param run_name: The name model run.
        :param input_esdl: The input ESDL as a string.
        :param run_input_data: Additional input data (next to the input ESDL).
        :param user_name: The name of the user.
        :param logs: Optional error logs received while starting the run.
        :param status: Optional run status.
        :return: the inserted new model data.
        """
        doc = get_default_model_run_values() | {
            USER: user_name,
            MODEL_NAME: model_name,
            MODEL_JOB_ID: model_job_id,
            RUN_NAME: run_name,
            INPUT_ESDL: input_esdl,
            MODEL_SPECIFIC_INPUT: run_input_data,
            MODEL_SPECIFIC_OUTPUT: None,
            STATUS: status.value,
        }
        if logs:
            doc[LOGS] = logs

        if VALUE_UNSET in doc.keys():
            raise RuntimeError(f"Cannot save model run, unset required values: {doc.keys()}")
        with self.named_locker.lock(self.collection_name):
            self.collection.insert_one(doc)
        del doc["_id"]
        return doc

    def get_model_run(self, run_id: str) -> dict:
        """
        Get all data for a model run.

        :param run_id: The MapEditor run ID of the external model run.
        :return: External model run data.
        """
        with self.named_locker.lock(self.collection_name):
            model_run = self.collection.find_one({RUN_ID: run_id}, projection={"_id": False})
        return model_run

    def delete_model_run(self, run_id: str) -> dict:
        """
        Delete a model run from the database.

        :param run_id: The MapEditor run ID of the external model run.
        :return: Deleted model run data.
        """
        with self.named_locker.lock(self.collection_name):
            deleted_model_data = self.collection.find_one_and_delete({RUN_ID: run_id}, projection={"_id": False})
        return deleted_model_data

    def get_model_runs_for_current_user(
        self, user_name: str, user_group_paths: list[str], model_name: str = None
    ) -> list:
        """
        Get all model runs for a user, including all runs for the supplied user group paths.

        :param user_name: The name of the user.
        :param user_group_paths: List of user group paths for which runs will be extracted as well.
        :param model_name: The name of the external model.
        :return: list of model run data objects.
        """
        with self.named_locker.lock(self.collection_name):
            if model_name:
                myquery = {
                    "$and": [
                        {MODEL_NAME: model_name},
                        {
                            "$or": [
                                {USER: user_name},
                                {USER_GROUP_PATHS: {"$elemMatch": {"$in": user_group_paths}}},
                            ]
                        },
                    ]
                }
            else:
                myquery = {
                    "$or": [
                        {USER: user_name},
                        {USER_GROUP_PATHS: {"$elemMatch": {"$in": user_group_paths}}},
                    ]
                }
            models_cursor = self.collection.find(myquery, projection={"_id": False})
        return list(models_cursor)

    def update_model_run(self, run_id: str, updated_values: dict) -> dict:
        """
        Update a model run in the database.

        :param run_id: The MapEditor run ID of the external model run.
        :param updated_values: Key-values which will be updated.
        :return: the updated model data.
        """
        return self.collection.find_one_and_update(
            {RUN_ID: run_id},
            {"$set": updated_values},
            projection={"_id": False},
            upsert=False,
            return_document=ReturnDocument.AFTER,
        )

    def clear(self) -> None:
        """
        Clear the settings database. This will remove all settings. Only use this with command line tools!
        """
        self.client.drop_database(self.database)


def get_default_model_run_values() -> dict:
    """
    Default values for a new run.

    Any `VALUE_UNSET` values have to be updated before saving to the database.

    :return: Default new run values.
    """
    return {
        USER: VALUE_UNSET,
        USER_GROUP_PATHS: [],
        MODEL_NAME: VALUE_UNSET,
        MODEL_JOB_ID: VALUE_UNSET,
        RUN_ID: str(uuid.uuid4()),
        RUN_NAME: VALUE_UNSET,
        INPUT_ESDL: VALUE_UNSET,
        PROGRESS_FRACTION: 0,
        SUBMITTED_TO_EXTERNAL_MODEL_AT: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        LAST_UPDATED_TO_EXTERNAL_MODEL_AT: None,
    }
