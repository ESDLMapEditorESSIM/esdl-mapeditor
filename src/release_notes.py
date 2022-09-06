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

from flask import Flask
from flask_socketio import SocketIO

from extensions.mapeditor_settings import MapEditorSettings
from extensions.session_manager import get_session, set_session
from extensions.settings_storage import SettingsStorage
import src.log as log
from src.version import __version__

logger = log.get_logger(__name__)

# Add new release notes at the beginning of this list
release_notes = [
    # {
    #     "version": "22.8.0",
    #     "date": "2022-08-02T22:15:00Z",
    #     "general_message": "On August 2nd 2022, we've released the new ESDL MapEditor version 22.8.0. " +
    #                        "See below for a list of new features and bug fixes",
    #     "categories": [
    #         {
    #             "name": "New features",
    #             "items": [
    #             ]
    #         },
    #         {
    #             "name": "Bug fixes",
    #             "items": [
    #                 "Fixed frontend error during editing asset properties",
    #                 "Fixed showing connection lines in correct map",
    #                 "Fixed lots of functionality in building editor",
    #                 "Refresh ESDL when ESDL browser is closed",
    #             ]
    #         },
    #     ]
    # },
    {
        "version": "22.7.0",
        "date": "2022-07-02T22:15:00Z",
        "general_message": "On July 2nd 2022, we've released the new ESDL MapEditor version 22.7.0. " +
                           "See below for a list of new features and bug fixes",
        "categories": [
            {
                "name": "New features",
                "items": [
                    "Implement delete building",
                    "Update ESDL version to v2207"
                ]
            },
            {
                "name": "Bug fixes",
                "items": [
                    "Fixed loading ESDL file with same name",
                    "Fixed deleting assets that are represented as a polygon on the map",
                    "Fixed alignment of editing cells in the table editor",
                ]
            },
        ]
    },
    {
        "version": "22.4.2",
        "date": "2022-04-30T18:00:00Z",
        "general_message": "On April 30th 2022, we've released the new ESDL MapEditor version 22.4.2. " +
                           "See below for a list of new features and bug fixes",
        "categories": [
            {
                "name": "New features",
                "items": [
                    "Release notes will be shown as soon as the user logs in after a new release has been deployed. "
                    "The release notes can also be found via Help --> Release notes",
                    "First version of ESDL shapefile export (with basic attributes of assets only for now): "
                    "this option can be found via File --> Export as shapefiles",
                ]
            },
            {
                "name": "Bug fixes",
                "items": [
                    "Fixed issue with objects with empty names in ESDL browser",
                    "Fixed issue with drawing assets when multiple ESDLs are loaded",
                    "Don't hide sidebar when ESDL service returns a message as a result",
                    "Deselect all assets when user clicks edit or delete button",
                    "Fixed issue handling instances without a name",
                    "Fixed issue with handling port markers",
                    "Fixed issue with removing connections"
                ]
            },
        ]
    },
    {
        "version": "",
        "date": "2022-04-21T00:00:00Z",
        "general_message": "Release notes from versions earlier than 22.4.2 are not available",
        "categories": []
    },
]

LATEST_SEEN_VERSION_SETTINGS = "latest_seen_version"


class ReleaseNotes:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.register()

        self.mapeditor_settings = MapEditorSettings.get_instance()

    def register(self):
        logger.info("Registering ViewModes")

        @self.flask_app.route('/get_release_notes')
        def get_release_notes():
            user = get_session('user-email')
            return {
                "latest_seen": self.get_seen_release_notes(user),
                "release_notes": release_notes
            }

    def get_seen_release_notes(self, user):
        last_seen_version_settings = self.mapeditor_settings.get_user_setting(user, LATEST_SEEN_VERSION_SETTINGS)

        if not last_seen_version_settings:
            self.mapeditor_settings.set_user_setting(user, LATEST_SEEN_VERSION_SETTINGS, {
                "version": __version__
            })
            return ""
        else:
            if last_seen_version_settings["version"] != __version__:
                self.mapeditor_settings.set_user_setting(user, LATEST_SEEN_VERSION_SETTINGS, {
                    "version": __version__
                })
            return last_seen_version_settings["version"]
