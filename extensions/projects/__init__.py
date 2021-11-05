from flask import Blueprint

projects = Blueprint('projects', __name__, url_prefix='/projects')

from extensions.projects import routes  # noqa
# For some reason, importing here doesn't properly register the events. Import manually on bottom of app.py for now.
# from extensions.projects import events  # noqa
