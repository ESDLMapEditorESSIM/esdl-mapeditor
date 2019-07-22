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

if os.environ.get('GEIS'):
    # Settings for in GEIS cloud behind redbird reverse proxy
    print('Starting application with GEIS settings (hosting at geis.hesi.energy/webeditor)')
    dir_settings = {
        'plugin_prefix': '/webeditor',
        'resource_prefix': 'webeditor',
        'socket_prefix': '/webeditor',
        'download_prefix': '/webeditor'
    }
elif os.environ.get('MAPEDITOR-TNO'):
    # Settings for in GEIS cloud behind redbird reverse proxy
    print('Starting application with MAPEDITOR-TNO settings (hosting at geis.hesi.energy/mapeditor)')
    dir_settings = {
        'plugin_prefix': '/mapeditor',
        'resource_prefix': 'mapeditor/',
        'socket_prefix': '/mapeditor',
        'download_prefix': '/mapeditor'
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
