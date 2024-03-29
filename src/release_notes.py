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
    {
        "version": "24.2.0",
        "date": "2024-02-13T13:08:00Z",
        "general_message": "On February 13th 2024, we've released the new ESDL MapEditor version 24.2.0. " +
                           "See below for a list of new features and bug fixes",
        "categories": [
            {
                "name": "New features",
                "items": [
                    "Support for external services that result in a profile",
                    "Make handling assets without a location user configurable",
                    "Support for boundary service with DSO service areas",
                    "Implement option to query ETM to build ESDL"
                ]
            },
            {
                "name": "Bug fixes",
                "items": [
                    "Fix non-disappearing tooltips",
                    "Fix for moving zoomed in area when area popup is displayed",
                    "Fix parameter handling for external service calls"
                ]
            },
        ]
    },
    {
        "version": "24.1.2",
        "date": "2024-01-18T16:08:00Z",
        "general_message": "On January 18th 2024, we've released the new ESDL MapEditor version 24.1.2. " +
                           "See below for a list of new features and bug fixes",
        "categories": [
            {
                "name": "New features",
                "items": [
                    "Support for logical area groups and being able to show/hide whole group in UI",
                    "Automatic determination of profile aggregation method for the port profile viewer",
                    "Added user feedback menu option"
                ]
            },
            {
                "name": "Bug fixes",
                "items": [
                    "Fix error when sending ESDL on asset context menu service call",
                    "Fix calling panel service when using filters"
                ]
            },
        ]
    },
    {
        "version": "24.1.1",
        "date": "2024-01-10T14:58:00Z",
        "general_message": "On January 10th 2024, we've released the new ESDL MapEditor version 24.1.1. " +
                           "See below for a list of new features and bug fixes",
        "categories": [
            {
                "name": "New features",
                "items": [
                    "Support for ESDL update v2401",
                ]
            },
            {
                "name": "Bug fixes",
                "items": [
                    "Fix error with 'empty' area DistributionKPIs",
                    "Fix building proper legend for KPIs when not all areas have same labels"
                ]
            },
        ]
    },
    {
        "version": "23.12.0",
        "date": "2023-12-13T07:00:00Z",
        "general_message": "On December 13th 2023, we've released the new ESDL MapEditor version 23.12.0. " +
                           "See below for a list of new features and bug fixes",
        "categories": [
            {
                "name": "New features",
                "items": [
                    "First version of interactive tooltips when hovering over an EnergyAsset on the map",
                    "Support for ESDL update v2311",
                    "Support for profiles, sectors and carriers from the EDR",
                    "Add more assets to the AssetDrawToolbar default list",
                    "Add kWh, MWh and GWh to the list of predefined quantity and units",
                    "Areas now have a context menu for actions"
                ]
            },
            {
                "name": "Bug fixes",
                "items": [
                    "Fix double scroll bars in the TableEditor",
                    "Fix updating asset state when changing multiple items in the TableEditor (issue NWN#14)",
                    "Fix for specifying cost information without a unit",
                    "Fix and enable delete area option",
                    "Fix issue with pipe duplicate and reverse not working",
                    "Work around EMF behavior with split_conductor() having ports that are not removed correctly",
                    "Fix bugs in port profile viewer",
                    "Fix loading of esdl.Potential",
                    "Fix error with 'empty' area KPIs"
                ]
            },
        ]
    },
    {
        "version": "23.9.0",
        "date": "2023-9-25T22:52:00Z",
        "general_message": "On September 25th 2023, we've released the new ESDL MapEditor version 23.9.0. " +
                           "See below for a list of new features and bug fixes",
        "categories": [
            {
                "name": "New features",
                "items": [
                    "Improved the processing of CSV based profile information.",
                    "Implement automatic placement of assets in right area based on location.",
                ]
            },
            {
                "name": "Bug fixes",
                "items": [
                    "Fix error with splitting pipe in sub area"
                ]
            },
        ]
    },
    {
        "version": "23.5.0",
        "date": "2023-5-25T13:32:00Z",
        "general_message": "On May 25th 2023, we've released the new ESDL MapEditor version 23.5.0. " +
                           "See below for a list of new features and bug fixes",
        "categories": [
            {
                "name": "New features",
                "items": [
                    "Implement export of ESSIM results to Excel",
                ]
            }
        ]
    },
    {
        "version": "23.3.0",
        "date": "2023-4-5T17:02:00Z",
        "general_message": "On April 5th 2023, we've released the new ESDL MapEditor version 23.3.0. " +
                           "See below for a list of new features and bug fixes",
        "categories": [
            {
                "name": "New features",
                "items": [
                    "Update ESDL version to v2303",
                    "Support for custom icons",
                    "Allow editing of WMS layer configurations",
                    "Improve editing of marginal costs (delete is now possible too)"
                ]
            },
            {
                "name": "Bug fixes",
                "items": [
                    "Fix small errors with missing units",
                    "Fix error for loading an ESDL file with an error in it"
                ]
            },
        ]
    },
    {
        "version": "22.10.0",
        "date": "2022-10-31T22:02:00Z",
        "general_message": "On October 31st 2022, we've released the new ESDL MapEditor version 22.10.0. " +
                           "See below for a list of new features and bug fixes",
        "categories": [
            {
                "name": "New features",
                "items": [
                    "Support for carrier costs (SingleValue and InfluxDBProfile)",
                    "Update ESDL version to v2210",
                ]
            },
            {
                "name": "Bug fixes",
                "items": [
                    "Improve browser memory usage when loading very large ESDLs",
                    "Fixed some things handling instances of type esdl.Potential",
                    "Improved interaction with ESSIM during preprocessing and errors",
                    "Fixed frontend error during editing asset properties",
                    "Fixed showing connection lines in correct map",
                    "Fixed lots of functionality in building editor",
                    "Refresh ESDL when ESDL browser is closed",
                ]
            },
        ]
    },
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
