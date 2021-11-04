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

from extensions.settings_storage import SettingType, SettingsStorage
from extensions.session_manager import get_session
import copy
import src.log as log

logger = log.get_logger(__name__)

KPI_DASHBOARD_SETTING = 'kpi_dashboards'


class KPIDashboard:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.register()

        if not self.settings_storage.has_system(KPI_DASHBOARD_SETTING):
            self.settings_storage.set_system(KPI_DASHBOARD_SETTING, default_system_dashboards)
        else:
            logger.info('Found dashboards in System Settings')

    def register(self):
        logger.info("Registering KPIDashboard")

        @self.flask_app.route('/kpi_dashboards')
        def get_kpi_dashboards():
            return self.get_dashboards()

        @self.socketio.on('kpi_dashboard_set____', namespace='/esdl')
        def kpi_dashboard_set____():
            user = get_session('user-email')

    def add_dashboard(self, dashboard_id, dashboard_settings):
        setting_type = SettingType(dashboard_settings['setting_type'])
        project_name = dashboard_settings['project_name']
        identifier = self._get_identifier(setting_type, project_name)

        if identifier is not None and self.settings_storage.has(setting_type, identifier, KPI_DASHBOARD_SETTING):
            dashboards = self.settings_storage.get(setting_type, identifier, KPI_DASHBOARD_SETTING)
        else:
            dashboards = dict()
        dashboards[dashboard_id] = dashboard_settings
        self.settings_storage.set(setting_type, identifier, KPI_DASHBOARD_SETTING, dashboards)

    def remove_dashboard(self, dashboard_id):
        # as we only have an ID, we don't know if it is a user, project or system setting
        # get the whole list, so we can find out the setting_type
        dashboard_settings = self.get_layers()[KPI_DASHBOARD_SETTING][dashboard_id]
        setting_type = SettingType(dashboard_settings['setting_type'])
        identifier = self._get_identifier(setting_type, dashboard_settings['project_name'])
        if identifier is None:
            return
        if self.settings_storage.has(setting_type, identifier, KPI_DASHBOARD_SETTING):
            # update dashboards dict
            dashboards = self.settings_storage.get(setting_type, identifier, KPI_DASHBOARD_SETTING)
            logger.info('Deleting dashboard {}'.format(dashboards[dashboard_id]))
            del(dashboards[dashboard_id])
            self.settings_storage.set(setting_type, identifier, KPI_DASHBOARD_SETTING, dashboards)

    def _get_identifier(self, setting_type: SettingType, project_name=None):
        if setting_type is None:
            return
        elif setting_type == SettingType.USER:
            identifier = get_session('user-email')
        elif setting_type == SettingType.PROJECT:
            if project_name is not None:
                identifier = project_name.replace(' ', '_')
            else:
                identifier = 'unnamed project'
        elif setting_type == SettingType.SYSTEM:
            identifier = SettingsStorage.SYSTEM_NAME_IDENTIFIER
        else:
            return None
        return identifier

    def get_dashboards(self):
        # gets the default list and adds the user dashboards
        all_dashboards = dict()
        if self.settings_storage.has_system(KPI_DASHBOARD_SETTING):
            all_dashboards.update(self.settings_storage.get_system(KPI_DASHBOARD_SETTING))

        user = get_session('user-email')
        user_group = get_session('user-group')
        role = get_session('user-role')
        mapeditor_role = get_session('user-mapeditor-role')
        # logger.debug('User: {}'.format(user))
        # logger.debug('Groups: {}'.format(user_group))
        # logger.debug('Roles: {}'.format(role))
        # logger.debug('Mapeditor roles: {}'.format(mapeditor_role))
        if user is not None and self.settings_storage.has_user(user, KPI_DASHBOARD_SETTING):
            # add user layers if available
            all_dashboards.update(self.settings_storage.get_user(user, KPI_DASHBOARD_SETTING))

        if user_group is not None:
            for group in user_group:
                identifier = self._get_identifier(SettingType.PROJECT, group)
                if self.settings_storage.has_project(identifier, KPI_DASHBOARD_SETTING):
                    # add project layers if available
                    all_dashboards.update(self.settings_storage.get_project(identifier, KPI_DASHBOARD_SETTING))

        # generate message
        message = copy.deepcopy(default_dashboard_groups)
        possible_groups = message["groups"]
        # if enough rights, mark Standard layers editable
        if 'mapeditor-admin' in mapeditor_role:
            for g in possible_groups:
                if g['setting_type'] == SettingType.SYSTEM.value:
                    g['readonly'] = False
        possible_groups.extend(self._create_dashboard_groups_for_projects(user_group))
        message[KPI_DASHBOARD_SETTING] = all_dashboards
        # logger.debug(message)
        return message

    def _create_dashboard_groups_for_projects(self, groups):
        project_list = list()
        if groups is not None:
            for group in groups:
                identifier = self._get_identifier(SettingType.PROJECT, group)
                json = {"setting_type": SettingType.PROJECT.value, "project_name": identifier, "name": "Project dashboards for " + group, "readonly": False}
                project_list.append(json)
        return project_list


default_dashboard_groups = {
    "groups": [
        {"setting_type": SettingType.USER.value, "project_name": SettingType.USER.value, "name": "Personal dashboards", "readonly": False},
        {"setting_type": SettingType.SYSTEM.value, "project_name": SettingType.SYSTEM.value, "name": "Standard dashboards", "readonly": True}
    ]
}

default_system_dashboards = {
    "id": {
        "setting_type": SettingType.SYSTEM.value,
        "name": "Default dashboard",
        "description": "",
        "state": "custom",      # Can be 'minimized' and 'maximized' too
        "location": {"x": 50, "y": 10},
        "size": {"height": 400, "width": 600},
        "panels": [],
    }
}
