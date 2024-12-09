import os

from sqlalchemy import make_url, URL
from sqlalchemy_utils import create_database, database_exists, drop_database

from extensions.data_manager import db
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


def drop_db(db_url: str, app_instance_path: str):
    """Destroys and creates the database + tables."""

    # Need to import models to create tables.
    import extensions.data_manager.db_model  # noqa

    if database_exists(db_url):
        logger.info(f"DataManager: Dropping database {db_url}: bye bye data!")
        url: URL = make_url(db_url)
        if url.drivername == 'sqlite':
            # in flask, 'instance' path is used to store the database file
            # which is not supported by sqlalchemy_utils
            db_path = os.path.join(app_instance_path, url.database)
            try:
                os.remove(db_path)
            except:
                logger.error(f"Error removing database at {db_path}")
        else:
            drop_database(db_url)