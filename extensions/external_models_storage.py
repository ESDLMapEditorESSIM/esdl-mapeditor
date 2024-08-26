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

    def add_model_run(
        self,
        model_name: str,
        model_job_id: str,
        run_name: str,
        input_esdl: str,
        run_input_data: dict,
        user_name: str,
        get_result_config: dict,
    ) -> None:
        """
        Add an external model run to the database, a run ID will be created.

        :param model_name: The name of the external model.
        :param model_job_id: The ID of the model to be added.
        :param run_name: The name model run.
        :param input_esdl: The input ESDL as a string.
        :param run_input_data: Additional input data (next to the input ESDL).
        :param user_name: The name of the user.
        :param get_result_config: Information on how to check the job status and obtain the results.
        """
        doc = get_default_model_run_values() | {
            "user": user_name,
            "model_name": model_name,
            "model_job_id": model_job_id,
            "run_name": run_name,
            "input_esdl": input_esdl,
            "get_result_config": get_result_config,
            "model_specific_input": run_input_data,
            "model_specific_output": None,
        }
        if VALUE_UNSET in doc.keys():
            raise RuntimeError(f"Cannot save model run, unset required values: {doc.keys()}")
        with self.named_locker.lock(model_name):
            self.db[model_name].insert_one(doc)

    def get_model_run(self, model_name: str, run_id: str) -> dict:
        """
        Get all data for a model run.

        :param model_name: The name of the external model.
        :param run_id: The MapEditor run ID of the external model run.
        :return: External model run data
        """
        with self.named_locker.lock(model_name):
            model_run = self.db[model_name].find_one({"run_id": run_id}, projection={"_id": False})
        return model_run

    def delete_model_run(self, model_name: str, run_id: str) -> dict:
        """
        Delete a model run from the database.

        :param model_name: The name of the external model.
        :param run_id: The MapEditor run ID of the external model run.
        :return: Deleted model run data
        """
        with self.named_locker.lock(model_name):
            deleted_model_data = self.db[model_name].find_one_and_delete({"run_id": run_id}, projection={"_id": False})
        return deleted_model_data

    def get_model_runs_for_current_user(self, model_name: str, user_name: str, user_projects: list[str]) -> list:
        """
        Get all model runs for a user, including all runs for the supplied projects.

        :param model_name: The name of the external model.
        :param user_name: The name of the user.
        :param user_projects: List of projects for which run will be extracted as well.
        :return: Deleted model run data
        """
        with self.named_locker.lock(model_name):
            myquery = {"$or": [{"user": user_name}, {"projects": {"$elemMatch": {"$in": user_projects}}}]}
            models_cursor = self.db[model_name].find(myquery, projection={"_id": False})
        return list(models_cursor)

    def update_model_run(self, model_name: str, run_id: str, updated_values: dict):
        """
        Update a model run in the database.

        :param model_name: The name of the external model.
        :param run_id: The MapEditor run ID of the external model run.
        :param updated_values: Key-values which will be updated.
        """
        return self.db[model_name].find_one_and_update(
            {"run_id": run_id},
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
    return dict(
        user=VALUE_UNSET,
        projects=[],
        model_name=VALUE_UNSET,
        model_job_id=VALUE_UNSET,
        run_id=str(uuid.uuid4()),
        run_name=VALUE_UNSET,
        input_esdl=VALUE_UNSET,
        status=RunStatus.SUBMITTED.value,
        progress_fraction=0,
        submitted_to_external_model=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        last_update_from_external_model=None,
    )
