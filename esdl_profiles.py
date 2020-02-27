import esdl_config
import copy


class ESDLProfiles:

    def __init__(self):
        self.profiles = esdl_config.esdl_config['influxdb_profile_data']

    def get_profiles_list(self, roles=[]):

        print(roles)
        role_profiles = copy.deepcopy(self.profiles)
        for rp in list(role_profiles):
            if 'required_role' in rp:
                if not rp['required_role'] in roles:
                    role_profiles.remove(rp)

        return role_profiles
