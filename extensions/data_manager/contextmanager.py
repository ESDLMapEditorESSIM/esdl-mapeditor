from contextlib import contextmanager
from functools import wraps

from sqlalchemy import orm

from extensions.data_manager import db
from src.log import get_logger

logger = get_logger(__name__)
session_factory = orm.sessionmaker()
Session = orm.scoped_session(session_factory)


@contextmanager
def session_scope(bind=None):
    """Provide a transactional scope around a series of operations. Ensures that the session is
    commited and closed. Exceptions raised within the 'with' block using this contextmanager
    should be handled in the with block itself. They will not be caught by the 'except' here."""
    try:
        if bind:
            yield Session(bind=bind)
        else:
            yield Session(bind=db.engine)
        Session.commit()
    except Exception:
        # Only the exceptions raised by session.commit above are caught here
        Session.rollback()
        raise
    finally:
        Session.remove()


def with_session(func):
    """
    Wraps the function in a transaction, any errors thrown in the function
    are intercepted so the tx can be rolled back.
    """

    @wraps(func)
    def wrapped(**kwargs):
        with session_scope() as session:
            try:
                result = func(session=session, **kwargs)
                session.commit()
                return result
            except Exception as exception:
                logger.exception(exception)
                session.rollback()
                raise

    return wrapped
