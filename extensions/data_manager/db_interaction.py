import enum
import os

from sqlalchemy import make_url, URL, text
from sqlalchemy_utils import create_database, database_exists, drop_database

from extensions.data_manager import db
from src.log import get_logger

logger = get_logger(__name__)

class DriverType(enum.Enum):
    """All supported driver types."""

    POSTGRES = "postgresql"
    SQLITE = "sqlite"

def create_db(db_url: str):
    """Destroys and creates the database + tables."""

    # Need to import models to create tables.
    import extensions.data_manager.db_model  # noqa

    try:
        if not database_exists(db_url):
            logger.info("Creating database.")
            create_database(db_url)
    except Exception:
        pass

    create_db_tables()

def create_db_tables():
    """
    Creates the database tables. Please note that this function does not modify existing tables.
    """
    logger.info("DataManager: Creating tables.")
    db.create_all()
    db.session.commit()
    logger.info("DataManager: Tables created.")


def drop_db_tables():
    """
    Drops all database tables while keeping the database itself.
    This is useful for completely resetting the data without recreating the database.
    """
    logger.info("DataManager: Dropping all tables.")
    try:
        with db.engine.connect() as conn:
            with conn.begin():
                inspector = db.inspect(db.engine)
                table_names = inspector.get_table_names()

                for table in table_names:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))

        logger.info("DataManager: All tables dropped successfully.")
    except Exception as e:
        logger.error(f"DataManager: Error dropping tables: {str(e)}")
        raise


def drop_db(db_url: str, app_instance_path: str):
    """Destroys and creates the database + tables."""

    # Need to import models to create tables.
    import extensions.data_manager.db_model  # noqa

    if database_exists(db_url):
        logger.info(f"DataManager: Dropping database {db_url}: bye bye data!")
        driver_type = get_db_driver_type(db_url)
        if driver_type == DriverType.SQLITE:
            # in flask, 'instance' path is used to store the database file
            # which is not supported by sqlalchemy_utils
            db_path = os.path.join(app_instance_path, url.database)
            try:
                os.remove(db_path)
            except:
                logger.error(f"Error removing database at {db_path}")
        else:
            drop_database(db_url)


def get_db_driver_type(db_url: str | None = None) -> DriverType:
    """
    Returns the drivername of the database url.
    """
    if db_url:
        url = make_url(db_url)
        drivername = url.drivername
    else:
        drivername = db.engine.url.drivername
    if drivername.startswith('postgresql'):
        return DriverType.POSTGRES
    elif drivername == 'sqlite':
        return DriverType.SQLITE
    raise NotImplementedError(f"Driver {drivername} not supported.")