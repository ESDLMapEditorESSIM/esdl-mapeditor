from flask import Flask
from flask_socketio import SocketIO, emit
from extensions.session_manager import get_handler, get_session
from xmldiff import main

class ESDLCompare:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self):
        print('Registering ESDL Compare extension')

        @self.socketio.on('esdl_compare', namespace='/esdl')
        def compare(esdls):
            with self.flask_app.app_context():
                esh = get_handler()

                es_id1 = esdls['esdl1']
                es_id2 = esdls['esdl2']

                es1_str = esh.to_string(es_id1).encode()    # convert string to bytes
                es2_str = esh.to_string(es_id2).encode()    # convert string to bytes

                print("Comparing EnergySystems with id {} and {}".format(es_id1, es_id2))
                results = main.diff_texts(es1_str, es2_str)

                emit('esdl_compare_window', results, namespace='/esdl')
