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

"""
Only import this folder when starting the app (e.g. not when testing, otherwise circular imports)
"""
from typing import cast

from flask import Flask
from flask_executor import Executor
from flask_session import Session
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix

from extensions.session_manager import delete_sessions_on_disk, load_sessions_from_disk
from src import settings
from src.log import get_logger
from src.settings import PERSIST_SESSIONS
from utils.utils import ThreadSafeCounter

logger = get_logger(__name__)

socketio = SocketIO()
executor = Executor()

class EDSLMapEditorApp(Flask):
    request_counter: ThreadSafeCounter


def create_app(name) ->  EDSLMapEditorApp:
    app = cast(EDSLMapEditorApp, Flask(name))
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    app.config['SECRET_KEY'] = b'\xc3g\x19\xbf\x8e\xa0\xe7\xc8\x9a/\xae%\x04g\xbe\x9f\xaex\xb5\x8c\x81f\xaf`' #os.urandom(24)   #'secret!'
    app.config['SESSION_COOKIE_NAME'] = 'ESDL-WebEditor-session'
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    # app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = 60*60*24 # 1 day in seconds
    app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
    app.config['EXECUTOR_PROPAGATE_EXCEPTIONS'] = True # make sure errors are logged for tasks run in threads
    # Set this to true to make sqlalchemy output all queries to the console.
    app.config["SQLALCHEMY_ECHO"] = False

    socketio.init_app(
        app,
        async_mode=settings.ASYNC_MODE,
        manage_session=False,
        path='/socketio.io',
        logger=settings.FLASK_DEBUG,
        engineio_logger=settings.FLASK_DEBUG,
        cors_allowed_origins=settings.ALLOWED_ORIGINS,
    )

    if PERSIST_SESSIONS:
        load_sessions_from_disk()
    else:
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

    from src.tno.live_model_interface.lmi_listener import start_live_model_interface_thread
    start_live_model_interface_thread(app)

    app.request_counter = ThreadSafeCounter()

    return app
