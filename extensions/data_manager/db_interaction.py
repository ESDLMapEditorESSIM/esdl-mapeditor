import os
from datetime import datetime

from flask import Flask
from sqlalchemy import make_url, URL
from sqlalchemy.orm import Session
from sqlalchemy_utils import create_database, database_exists, drop_database

from extensions.data_manager import db
from extensions.data_manager.contextmanager import with_session
from extensions.data_manager.db_model import DataSet
from src.log import get_logger

logger = get_logger(__name__)

def create_db(db_url: str):
    """Destroys and creates the database + tables."""

    # Need to import models to create tables.
    import extensions.data_manager.db_model  # noqa

    try:
        if not database_exists(db_url):
            print("Creating database.")
            create_database(db_url)
    except Exception:
        pass

    logger.info("DataManager: Creating tables.")
    db.create_all()
    db.session.commit()
    logger.info("DataManager: Tables created.")


def drop_db(db_url: str):
    """Destroys and creates the database + tables."""

    # Need to import models to create tables.
    import extensions.data_manager.db_model  # noqa

    if database_exists(db_url):
        logger.info(f"DataManager: Dropping database {db_url}: bye bye data!")
        url:URL = make_url(db_url)
        if url.get_dialect().name == 'sqlite':
            # in flask, 'instance' path is used to store the database file
            # which is not supported by sqlalchemy_utils
            os.remove(os.path.join('instance', url.database))
        else:
            drop_database(db_url)


@with_session
def create_test_data(session: Session):
    print("Add dummy data")
    ds = DataSet(name="Test1", created_by = "ewoud.werkman@tno.nl")
    ds.name = "Test1"
    ds.scenario = "ADAPT 2022"
    ds.run_timestamp = datetime.now()
    ds.description = "Nice description"
    ds.software_version = "v2"
    ds.created_by = "ewoud.werkman@tno.nl"
    ds.model = "OMOTES Optimization"
    ds.public = True

    session.add(ds)
    session.commit()