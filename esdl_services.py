from esdl import esdl
import esdl_config


class ESDLServices:

    def __init__(self):
        self.config = esdl_config.esdl_config['predefined_esdl_services']

    def get_services_list(self):
        return self.config

    def call_esdl_service(self, service_params):
        pass
