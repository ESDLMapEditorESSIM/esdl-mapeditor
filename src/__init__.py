from flask_socketio import SocketIO

from flask_executor import Executor
from flask_session import Session
from socketio.kombu_manager import KombuManager

from extensions.session_manager import delete_sessions_on_disk
from src import settings
from src.log import get_logger
from flask import Flask

from src.tno.envsettings import EnvSettings
from src.tno.events.config import AMQP_URL

logger = get_logger(__name__)

socketio = SocketIO()
executor = Executor()


def create_app(name):
    app = Flask(name)
    app.config['SECRET_KEY'] = b'\xc3g\x19\xbf\x8e\xa0\xe7\xc8\x9a/\xae%\x04g\xbe\x9f\xaex\xb5\x8c\x81f\xaf`' #os.urandom(24)   #'secret!'
    app.config['SESSION_COOKIE_NAME'] = 'ESDL-WebEditor-session'
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    # app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = 60*60*24 # 1 day in seconds
    app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
    app.config['EXECUTOR_PROPAGATE_EXCEPTIONS'] = True # make sure errors are logged for tasks run in threads

    socketio.init_app(app, async_mode=settings.ASYNC_MODE, manage_session=False, path='/socketio.io', logger=settings.FLASK_DEBUG)

    # logging.getLogger('engineio').setLevel(logging.WARNING)  # don't print all the messages

    # remove existing sessions when restarting, existing sessions will give errors
    # as associated ESDLs are not stored in the session and the OpenId connect info is wrong
    delete_sessions_on_disk(app.config['SESSION_FILE_DIR'])

    # fix sessions with socketio.io. see: https://blog.miguelgrinberg.com/post/flask-socketio-and-the-user-session
    Session(app)
    executor.init_app(app)

    # Initialize blueprints.
    from extensions.projects import projects as projects_blueprint
    import extensions.undoredo  # noqa
    app.register_blueprint(projects_blueprint)

    return app
