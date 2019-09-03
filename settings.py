import os

# Flask settings
FLASK_SERVER_HOST = '0.0.0.0'
FLASK_SERVER_PORT = 8111
FLASK_DEBUG = False  # Do not use debug mode in production

# Flask-Restplus settings
RESTPLUS_SWAGGER_UI_DOC_EXPANSION = 'list'
RESTPLUS_VALIDATE = True
RESTPLUS_MASK_SWAGGER = False
RESTPLUS_ERROR_404_HELP = False

GEIS_CLOUD_HOSTNAME = '10.30.2.1'
ESDL_STORE_PORT = '3003'
BOUNDARY_SERVICE_PORT = '4002'

essim_config = {
    "ESSIM_host": "http://geis.hesi.energy:8112",
    "ESSIM_path": "/essim/simulation",
    "influxURL": "http://geis.hesi.energy:8086",
    "grafanaURL": "http://geis.hesi.energy:3000",
    "user": "essim",
    "ESSIM_database_server": "geis.hesi.energy",
    "ESSIM_database_port": 8086,
    "start_datetime": "2015-01-01T00:00:00+0100",
    "end_datetime": "2016-01-01T00:00:00+0100"
}

# for JWT verification, see https://idaccessman.wordpress.com/2018/10/19/keycloak-and-signed-jwts/
IDM_PUBLIC_KEY = b'-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAlPYHgu7ovAOEzL3uBoN7KJWSn9UvqNqYbEkfMTbJrJRs8E1WULtxGzCDRVLJWBdLdq05/+8BXEISiggrWOukjsd+uqLTqQMI0he2bZMBRHSD2ISIXhGp5kpUCsbb0xd2bvp/LqSAuWKZmVLRWGRba6Hi+wFjLYc48tdTJUbbShZTojIsDY/ivH+5xJ6N/z7Iwq0HqPVGMiOywPGi9xqT9g5lUxhBuXJ7crmGncpxA4LH1foSBtIXqVTjESPc+G/4Si61xtmHckf3KkaFYgM89TxDtCyiwoKSu5RVbS38+jXP6Wx25F655244V+FSNty11ApSf2VaY9t5tCfv3RQvAwIDAQAB\n-----END PUBLIC KEY-----'
#IDM_PUBLIC_KEY = b'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAlPYHgu7ovAOEzL3uBoN7KJWSn9UvqNqYbEkfMTbJrJRs8E1WULtxGzCDRVLJWBdLdq05/+8BXEISiggrWOukjsd+uqLTqQMI0he2bZMBRHSD2ISIXhGp5kpUCsbb0xd2bvp/LqSAuWKZmVLRWGRba6Hi+wFjLYc48tdTJUbbShZTojIsDY/ivH+5xJ6N/z7Iwq0HqPVGMiOywPGi9xqT9g5lUxhBuXJ7crmGncpxA4LH1foSBtIXqVTjESPc+G/4Si61xtmHckf3KkaFYgM89TxDtCyiwoKSu5RVbS38+jXP6Wx25F655244V+FSNty11ApSf2VaY9t5tCfv3RQvAwIDAQAB'

#ASYNC_MODE = 'gevent' # default for non uWGSI deployments
ASYNC_MODE = None # default for non uWGSI deployments

edr_config = {
    "EDR_host": "https://edr.hesi.energy",
    "EDR_path": "/store/esdl/",
}

if os.environ.get('GEIS'):
    # Settings for in GEIS cloud behind redbird reverse proxy
    print('Starting application with GEIS settings (hosting at geis.hesi.energy/webeditor)')
    dir_settings = {
        'plugin_prefix': '/webeditor',
        'resource_prefix': 'webeditor',
        'socket_prefix': '/webeditor',
        'download_prefix': '/webeditor'
    }
    OIDC_CLIENT_SECRETS = 'credentials/client_secrets_geis.json'
elif os.environ.get('MAPEDITOR-TNO'):
    # Settings for in GEIS cloud behind traefik reverse proxy and served at /mapeditor
    print('Starting application with MAPEDITOR-TNO settings (hosting at geis.hesi.energy/mapeditor)')
    dir_settings = {
        'plugin_prefix': '/mapeditor',
        'resource_prefix': 'mapeditor/',
        'socket_prefix': '/mapeditor',
        'download_prefix': '/mapeditor'
    }
    OIDC_CLIENT_SECRETS = 'credentials/client_secrets_mapeditor.json'

elif os.environ.get('MAPEDITOR_HESI_ENERGY'):
    # Settings for in GEIS cloud behind traefik reverse proxy and served at mapeditor.hesi.energy
    print('Starting application with MAPEDITOR_HESI_ENERGY settings (hosting at mapeditor.hesi.energy)')
    dir_settings = {
        'plugin_prefix': '',
        'resource_prefix': '',
        'socket_prefix': '',
        'download_prefix': ''
    }
    FLASK_DEBUG = False 
    #ASYNC_MODE = 'gevent_uwsgi'
    ASYNC_MODE = None
    OIDC_CLIENT_SECRETS = 'credentials/client_secrets_mapeditor.hesi.energy.json'

    essim_config = {
        "ESSIM_host": "http://10.30.2.1:8112",
        "ESSIM_path": "/essim/simulation",
        "influxURL": "http://10.30.2.1:8086",
        "grafanaURL": "http://geis.hesi.energy:3000",
        "user": "essim",
        "ESSIM_database_server": "10.30.2.1",
        "ESSIM_database_port": 8086,
        "start_datetime": "2015-01-01T00:00:00+0100",
        "end_datetime": "2016-01-01T00:00:00+0100"
    }
else:
    # Local settings
    print('Starting application with local settings (hosting at localhost:port/ without a subpath)')
    dir_settings = {
        'plugin_prefix': '',
        'resource_prefix': '',
        'socket_prefix': '',
        'download_prefix': ''
    }
    #FLASK_DEBUG = True
    OIDC_CLIENT_SECRETS = 'credentials/client_secrets_local.json'
    # GEIS_CLOUD_HOSTNAME = 'geis.hesi.energy'



