from flask import Flask
from flask_socketio import SocketIO
from flask_executor import Executor
from extensions.user_settings import UserSettings
from extensions.session_manager import get_handler


def send_alert(message):
    print(message)
    # emit('alert', message, namespace='/esdl')


class AppSettings:
    def __init__(self, flask_app: Flask, socket: SocketIO, executor: Executor, user_settings: UserSettings):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings = user_settings
        self.executor = executor

        self.register()

    def register(self):
        print("Registering AppSettings extension")

        @self.socketio.on('app_settings', namespace='/esdl')
        def app_settings(prmtr):
            with self.flask_app.app_context():
                esh = get_handler()
                print(prmtr)