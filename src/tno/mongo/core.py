from pymongo import MongoClient
import src.settings as settings


database_uri = f"mongodb://{settings.settings_storage_config['host']}:{settings.settings_storage_config['port']}"
"""The default database URI, based on environment variables."""

mongo_client = MongoClient(database_uri)
"""This is the main client instance for the MongoDB connection, to be used throughout the code."""


def get_database(database_name: str = None):
    """
    Get the database instance on the shared mongo client.

    :param database_name:
    :return:
    """
    if database_name is None:
        database_name = settings.settings_storage_config["database"]
    return mongo_client[database_name]
