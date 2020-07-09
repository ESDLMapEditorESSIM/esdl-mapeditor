from extensions.settings_storage import SettingType, SettingsStorage
from extensions.session_manager import get_session
import copy

PROFILES_SETTING = 'profiles'


class Profiles:
    def __init__(self, settings_storage: SettingsStorage):
        self.settings_storage = settings_storage
        # add initial profiles when not in the system settings
        if not self.settings_storage.has_system(PROFILES_SETTING):
            self.settings_storage.set_system(PROFILES_SETTING, default_profiles)
        else:
            print('No need to update default list, already in User Settings')

    def add_profile(self, profile_id, profile):
        setting_type = SettingType(profile['setting_type'])
        project_name = profile['project_name']
        identifier = self._get_identifier(setting_type, project_name)
        if identifier is not None and self.settings_storage.has(setting_type, identifier, PROFILES_SETTING):
            profiles = self.settings_storage.get(setting_type, identifier, PROFILES_SETTING)
        else:
            profiles = dict()
        profiles[profile_id] = profile
        self.settings_storage.set(setting_type, identifier, PROFILES_SETTING, profiles)

    def remove_profile(self, profile_id):
        # as we only have an ID, we don't know if it is a user, project or system profile
        # get the whole list, so we can find out the setting_type
        profile = self.get_profiles()[PROFILES_SETTING][profile_id]
        setting_type = SettingType(profile['setting_type'])
        identifier = self._get_identifier(setting_type, profile['project_name'])
        if identifier is None:
            return
        if self.settings_storage.has(setting_type, identifier, PROFILES_SETTING):
            # update profile dict
            profiles = self.settings_storage.get(setting_type, identifier, PROFILES_SETTING)
            print('Deleting profile {}'.format(profiles[profile_id]))
            del(profiles[profile_id])
            self.settings_storage.set(setting_type, identifier, PROFILES_SETTING, profiles)

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

    def get_profiles(self):
        # gets the default list and adds the user profiles
        all_profiles = dict()
        if self.settings_storage.has_system(PROFILES_SETTING):
            all_profiles.update(self.settings_storage.get_system(PROFILES_SETTING))

        user = get_session('user-email')
        user_group = get_session('user-group')
        role = get_session('user-role')
        mapeditor_role = get_session('user-mapeditor-role')
        print('User: ', user)
        print('Groups: ', user_group)
        print('Roles: ', role)
        print('Mapeditor roles: ', mapeditor_role)
        if user is not None and self.settings_storage.has_user(user, PROFILES_SETTING):
            # add user profiles if available
            all_profiles.update(self.settings_storage.get_user(user, PROFILES_SETTING))

        if user_group is not None:
            for group in user_group:
                identifier = self._get_identifier(SettingType.PROJECT, group)
                if self.settings_storage.has_project(identifier, PROFILES_SETTING):
                    # add project profiles if available
                    all_profiles.update(self.settings_storage.get_project(identifier, PROFILES_SETTING))

        # generate message
        message = copy.deepcopy(default_profile_groups)
        possible_groups = message["groups"]
        # if enough rights, mark Standard profiles editable
        if 'mapeditor-admin' in mapeditor_role:
            for g in possible_groups:
                if g['setting_type'] == SettingType.SYSTEM.value:
                    g['readonly'] = False
        possible_groups.extend(self._create_group_profiles_for_projects(user_group))
        message[PROFILES_SETTING] = all_profiles
        print(message)
        return message

    def _create_group_profiles_for_projects(self, groups):
        project_list = list()
        if groups is not None:
            for group in groups:
                identifier = self._get_identifier(SettingType.PROJECT, group)
                json = {"setting_type": SettingType.PROJECT.value, "project_name": identifier, "name": "Project Layers for " + group, "readonly": False}
                project_list.append(json)
        return project_list


default_profile_groups = {
    "groups": [
        {"setting_type": SettingType.USER.value, "project_name": SettingType.USER.value, "name": "Personal Layers", "readonly": False},
        {"setting_type": SettingType.SYSTEM.value, "project_name": SettingType.SYSTEM.value, "name": "Standard Layers", "readonly": True}
    ]
}

#{"id": SettingType.PROJECT.value, "name": "Project Layers"},

default_profiles = {
    "AHN2_5m": {
        "description": "AHN2 5 meter",
        "url": "http://geodata.nationaalgeoregister.nl/ahn2/wms?",
        "profile_name": "ahn2_5m",
        "setting_type": SettingType.SYSTEM.value,
        "profile_ref": None,
        "visible": False,
        "attribution": ''
    },
    "RVO_Restwarmte": {
        "description": "Restwarmte (RVO: ligging industrie)",
        "url": "https://geodata.nationaalgeoregister.nl/restwarmte/wms?",
        "profile_name": "liggingindustrieco2",
        "setting_type": SettingType.SYSTEM.value,
        "profile_ref": None,
        "visible": False,
        "attribution": ''
    }
}