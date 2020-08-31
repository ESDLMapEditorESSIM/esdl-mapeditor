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

from flask import Flask, request
from flask_socketio import SocketIO
from extensions.session_manager import managed_sessions
import src.log as log

logger = log.get_logger(__name__)

incoming_esdls_via_api = dict()


class ESDL_API:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def get_sessions_from_managed_sessions(self):
        socketio_sid_list = dict()
        for client_id in managed_sessions:
            session_info = managed_sessions[client_id]
            if 'user-email' in session_info and 'socketio_sid' in session_info:
                user_email = session_info['user-email']
                socketio_sid = session_info['socketio_sid']

                if user_email in socketio_sid_list:
                    socketio_sid_list[user_email].append(socketio_sid)
                else:
                    socketio_sid_list[user_email] = [socketio_sid]
            else:
                print('user-email or socketio_sid missing in managed session info. Could be the session from the sending application.')

        return socketio_sid_list

    def register(self):
        logger.info("Registering esdl_API extension")

        @self.flask_app.route("/api/esdl", methods=['POST'])
        def receive_esdl_via_api():
            content = request.get_json(silent=True)
            # print(content)
            # print(session)             # bevat info over de sessie van deze API call
            print(managed_sessions)    # bevat de client_id's als keys en alle sessie info als values (van alle browser connecties)

            if content:
                if "sender" not in content or "email" not in content or "esdl" not in content:
                    return "Either sender, email or esdl is missing as a parameter", 400

                sender = content["sender"]
                email = content["email"]
                esdl = content["esdl"]
                if "descr" in content:
                    descr = content["descr"]
                else:
                    descr = ""

                socketio_sid_list = self.get_sessions_from_managed_sessions()
                if socketio_sid_list:
                    exclude_sessions = list()
                    if email in socketio_sid_list:
                        for key in socketio_sid_list:
                            if key != email:
                                exclude_sessions.extend(socketio_sid_list[key])
                    else:
                        return "User not logged in", 400

                    if email in incoming_esdls_via_api:
                        incoming_esdls_via_api[email].append({"sender": sender, "descr": descr, "esdl": esdl})
                    else:
                        incoming_esdls_via_api[email] = [{"sender": sender, "descr": descr, "esdl": esdl}]

                    # TODO: use room=sid to send a message to a specific user, as each user has its own room.
                    # See: https://stackoverflow.com/questions/39423646/flask-socketio-emit-to-specific-user
                    self.socketio.emit('received_esdl', {"sender": sender, "descr": descr}, skip_sid=exclude_sessions, namespace='/esdl')
                    return "Success", 201
                else:
                    return "User not logged in", 400
            else:
                return "No content", 400

    def get_esdl_for_user(self, email):
        if email in incoming_esdls_via_api:
            return incoming_esdls_via_api[email]
        return None

    def remove_esdls_for_user(self, email):
        if email in incoming_esdls_via_api:
            del incoming_esdls_via_api[email]
