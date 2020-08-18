import os

# Flask settings
FLASK_SERVER_HOST = '0.0.0.0'
FLASK_SERVER_PORT = 8111
FLASK_DEBUG = False  # Do not use debug mode in production

USER_LOGGING_ENABLED = True

# for JWT verification, see https://idaccessman.wordpress.com/2018/10/19/keycloak-and-signed-jwts/
IDM_PUBLIC_KEY = b'-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAlPYHgu7ovAOEzL3uBoN7KJWSn9UvqNqYbEkfMTbJrJRs8E1WULtxGzCDRVLJWBdLdq05/+8BXEISiggrWOukjsd+uqLTqQMI0he2bZMBRHSD2ISIXhGp5kpUCsbb0xd2bvp/LqSAuWKZmVLRWGRba6Hi+wFjLYc48tdTJUbbShZTojIsDY/ivH+5xJ6N/z7Iwq0HqPVGMiOywPGi9xqT9g5lUxhBuXJ7crmGncpxA4LH1foSBtIXqVTjESPc+G/4Si61xtmHckf3KkaFYgM89TxDtCyiwoKSu5RVbS38+jXP6Wx25F655244V+FSNty11ApSf2VaY9t5tCfv3RQvAwIDAQAB\n-----END PUBLIC KEY-----'

ASYNC_MODE = None # default for non uWGSI deployments

ibis_config = {
    "host": "10.30.2.1",
    "port": "4500",
    "path_list": "/api/v1/BusinessParks/",
    "path_contour": "/api/v1/BusinessParks/contour/"
}

bag_config = {
    "host": "10.30.2.1",
    "port": "4012",
    "path_contour": "/polygon"
}

boundaries_config = {
    "host": "10.30.2.1",
    "port": "4002",
    "path_names": "/names",
    "path_boundaries": "/boundaries"
}

edr_config = {
    "EDR_host": "https://edr.hesi.energy",
    "EDR_path": "/store/esdl/",
}

esdl_store_config = {
    "hostname": "http://10.30.2.1:3003"
}

mondaine_hub_config = {
    "hostname": "http://10.30.2.1:3002"
}

cdo_mondaine_config = {
    "hostname": "http://10.30.2.1:9080"
}

user_logging_config = {
    "host": "10.30.2.1",
    "port": "8086",
    "database": "user_logging"
}

settings_storage_config = {
    "host": "10.30.2.1",
    "port": "27017",
    "database": "esdl_mapeditor_settings"
}

statistics_settings_config = {
    "host": "10.30.2.1",
    "port": "6003",
    "path": "/api/statistics/calculate"
}

profile_database_config = {
    "protocol": "http",
    "host": "10.30.2.1",
    "port": "8086",
    "database": "energy_profiles",
    "filters": "",
    "upload_user": "admin",
    "upload_password": "admin"
}

panel_service_config = {
    "external_url": "https://panel-service.hesi.energy",
    "internal_url": "https://panel-service.hesi.energy"
}

if os.environ.get('MAPEDITOR_HESI_ENERGY'):
    # Settings for in GEIS cloud behind traefik reverse proxy and served at mapeditor.hesi.energy
    print('Starting application with MAPEDITOR_HESI_ENERGY settings (hosting at mapeditor.hesi.energy)')

    FLASK_DEBUG = False
    #ASYNC_MODE = 'gevent_uwsgi'
    ASYNC_MODE = None
    OIDC_CLIENT_SECRETS = 'credentials/client_secrets_mapeditor.hesi.energy.json'

    essim_config = {
        "ESSIM_host": "http://10.30.2.1:8112",
        "ESSIM_host_loadflow": "http://10.30.2.1:8113",
        "ESSIM_path": "/essim/simulation",
        "influxURL": "http://10.30.2.1:8086",
        "grafanaURL": "https://essim-dashboard.hesi.energy",
        "user": "essim",
        "ESSIM_database_server": "10.30.2.1",
        "ESSIM_database_port": 8086,
        "start_datetime": "2015-01-01T00:00:00+0100",
        "end_datetime": "2016-01-01T00:00:00+0100",
        "natsURL": "nats://nats:4222"
    }
elif os.environ.get('MAPEDITOR_OPEN_SOURCE'):
    print('Starting application with MAPEDITOR_OPEN_SOURCE settings (hosting at mapeditor:8111)')

    FLASK_DEBUG = False
    # ASYNC_MODE = 'gevent_uwsgi'
    ASYNC_MODE = None
    OIDC_CLIENT_SECRETS = 'credentials/client_secrets_opensource.json'

    essim_config = {
        "ESSIM_host": "http://essim-engine:8112",
        "ESSIM_host_loadflow": "",
        "ESSIM_path": "/essim/simulation",
        "influxURL": "http://influxdb:8086",
        "grafanaURL": "http://grafana:3000",
        "user": "essim",
        "ESSIM_database_server": "influxdb",
        "ESSIM_database_port": 8086,
        "start_datetime": "2015-01-01T00:00:00+0100",
        "end_datetime": "2016-01-01T00:00:00+0100",
        "natsURL": "nats://nats:4222"
    }
    boundaries_config = {
        "host": "boundary-service",
        "port": "4002",
        "path_names": "/names",
        "path_boundaries": "/boundaries"
    }

    edr_config = {
        "EDR_host": "https://edr.hesi.energy",
        "EDR_path": "/store/esdl/",
    }

    esdl_store_config = None
    mondaine_hub_config = None

    cdo_mondaine_config = {
        "hostname": "http://esdl-drive:9080"
    }

    user_logging_config = {
        "host": "influxdb",
        "port": "8086",
        "database": "user_logging"
    }

    profile_database_config = {
        "protocol": "http",
        "host": "influxdb",
        "port": "8086",
        "database": "energy_profiles",
        "filters": "",
        "upload_user": "admin",
        "upload_password": "admin"
    }

    settings_storage_config = {
        "host": "mongo",
        "port": "27017",
        "database": "esdl_mapeditor_settings"
    }

    panel_service_config = {
        "external_url": "http://localhost:3400",
        "internal_url": "http://panel-service:5000"
    }

else:
    # Local settings
    print('Starting application with local settings')

    OIDC_CLIENT_SECRETS = 'credentials/client_secrets_local.json'
    USER_LOGGING_ENABLED = False
    FLASK_DEBUG = True
    # settings_storage_config["host"] = 'localhost'
    # cdo_mondaine_config["hostname"] =  "http://localhost:9080"
    # GEIS_CLOUD_HOSTNAME = 'geis.hesi.energy'

    essim_config = {
        "ESSIM_host": "http://geis.hesi.energy:8112",
        "ESSIM_host_loadflow": "http://geis.hesi.energy:8113",
        "ESSIM_path": "/essim/simulation",
        "influxURL": "http://geis.hesi.energy:8086",
        "grafanaURL": "https://essim-dashboard.hesi.energy",
        "user": "essim",
        "ESSIM_database_server": "geis.hesi.energy",
        "ESSIM_database_port": 8086,
        "start_datetime": "2015-01-01T00:00:00+0100",
        "end_datetime": "2016-01-01T00:00:00+0100",
        "natsURL": "nats://nats:4222"
    }

