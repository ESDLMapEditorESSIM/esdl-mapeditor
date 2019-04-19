import os

# Flask settings
FLASK_SERVER_HOST = '0.0.0.0'
FLASK_SERVER_PORT = 8111
FLASK_DEBUG = True  # Do not use debug mode in production

# Flask-Restplus settings
RESTPLUS_SWAGGER_UI_DOC_EXPANSION = 'list'
RESTPLUS_VALIDATE = True
RESTPLUS_MASK_SWAGGER = False
RESTPLUS_ERROR_404_HELP = False

if os.environ.get('GEIS'):
    # Settings for in GEIS cloud behind redbird reverse proxy
    dir_settings = {
        'plugin_prefix': '/webeditor',
        'resource_prefix': 'webeditor/',
        'socket_prefix': '/webeditor'
    }
else:
    # Local settings
    dir_settings = {
       'plugin_prefix': '',
       'resource_prefix': '',
       'socket_prefix': ''
    }