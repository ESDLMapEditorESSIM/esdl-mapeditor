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

import os
from dotenv import load_dotenv

load_dotenv()
print('Starting application with {} settings'.format(os.environ.get("SETTINGS_TITLE", "NO")))

# Flask settings
FLASK_SERVER_HOST = '0.0.0.0'
FLASK_SERVER_PORT = 8111
_flask_debug = os.environ.get('FLASK_DEBUG', '')        # Do not use debug mode in production
FLASK_DEBUG = (_flask_debug.upper() == 'TRUE' or _flask_debug == '1')

USER_LOGGING_ENABLED = True
# ASYNC_MODE = 'gevent_uwsgi'
ASYNC_MODE = None # default for non uWGSI deployments

OIDC_CLIENT_SECRETS = os.environ.get('OIDC_CLIENT_SECRETS', None) # 'credentials/client_secrets_opensource.json'
_use_gevent = os.environ.get('MAPEDITOR_USE_GEVENT', '')
USE_GEVENT = (_use_gevent.upper() == 'TRUE' or _use_gevent == '1')

settings_storage_config = {
    "host": os.environ.get('SETTINGS_STORAGE_HOST', None),  # "mongo",
    "port": os.environ.get('SETTINGS_STORAGE_PORT', "27017"),
    "database": "esdl_mapeditor_settings"
}

user_logging_config = {
    "host": os.environ.get('USER_LOGGING_HOST', None),  # "influxdb",
    "port": os.environ.get('USER_LOGGING_PORT', "8086"),
    "database": "user_logging"
}

boundaries_config = {
    "host": os.environ.get('BOUNDARY_SERVICE_HOST', None),  # "boundary-service",
    "port": os.environ.get('BOUNDARY_SERVICE_PORT', None),  # "4002",
    "path_names": "/names",
    "path_boundaries": "/boundaries"
}

profile_database_config = {
    "protocol": "http",
    "host": os.environ.get('PROFILE_DATABASE_HOST', None),  # "influxdb",
    "port": os.environ.get('PROFILE_DATABASE_PORT', "8086"),
    "database": "energy_profiles",
    "filters": "",
    "upload_user": "admin",
    "upload_password": "admin"
}

panel_service_config = {
    "external_url": os.environ.get('PANEL_SERVICE_EXTERNAL_URL', None),  # "http://localhost:3400",
    "internal_url": os.environ.get('PANEL_SERVICE_INTERNAL_URL', None),  # "http://panel-service:5000"
    "profile_database_protocol": "http",
    "profile_database_host": os.environ.get('PANEL_SERVICE_PROFILE_DB_HOST', None),
    "profile_database_port": os.environ.get('PANEL_SERVICE_PROFILE_DB_PORT', "8086"),
    "profile_database_upload_user": "admin",
    "profile_database_upload_password": "admin"
}

essim_config = {
    "ESSIM_host": os.environ.get('ESSIM_URL', None),  # "http://essim-engine:8112",
    "ESSIM_host_loadflow": os.environ.get('ESSIM_LOADFLOW_URL', None),  # "",
    "ESSIM_path": "/essim/simulation",
    "influxURL": os.environ.get('ESSIM_INFLUX_URL', None),  # "http://influxdb:8086",
    "grafanaURL": os.environ.get('ESSIM_GRAFANA_URL', None),  # "http://grafana:3000",
    "user": "essim",
    "ESSIM_database_server": os.environ.get('ESSIM_DATABASE_HOST', None),  # "influxdb",
    "ESSIM_database_port": os.environ.get('ESSIM_DATABASE_PORT', 8086),
    "start_datetime": "2015-01-01T00:00:00+0100",
    "end_datetime": "2016-01-01T00:00:00+0100",
    "natsURL": "nats://nats:4222"
}

edr_config = {
    "host": os.environ.get('EDR_URL', None),  # "https://edr.hesi.energy",
}

esdl_store_config = {
    "hostname": os.environ.get('ESDL_STORE_URL', None)  # None
}
mondaine_hub_config = {
    "hostname": os.environ.get('MONDAINE_HUB_URL', None)  # None
}
esdl_drive_config = {
    "hostname": os.environ.get('ESDL_DRIVE_URL', None)  # "http://esdl-drive:9080"
}

ibis_config = {
    "host": os.environ.get('IBIS_SERVICE_HOST', None),
    "port": "4500",
    "path_list": "/api/v1/BusinessParks/",
    "path_contour": "/api/v1/BusinessParks/contour/"
}

bag_config = {
    "host": os.environ.get('BAG_SERVICE_HOST', None),
    "port": "4012",
    "path_contour": "/polygon"
}

statistics_settings_config = {
    "host": os.environ.get('STATISTICS_SERVICE_HOST', None),
    "port": "6003",
    "path": "/api/statistics/calculate"
}

ielgas_config = {
    "host": os.environ.get('IELGAS_DATABASE_HOST', None)
}

heatnetwork_dispatcher_config = {
    "host": os.environ.get('DISPATCHER_HOST', 'http://localhost'),
    "port": os.environ.get('DISPATCHER_PORT', 9200)
}