from functools import wraps

from werkzeug.exceptions import abort

from extensions.session_manager import get_session


def mapeditor_admin_required(f):
    """
    Decorator for Flask endpoints to only allow mapeditor admins.
    :param f: The function to protect.
    :return: Either the function or it throws a 403.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if is_mapeditor_admin():
            return f(*args, **kwargs)
        else:
            abort(403)
    return decorated_function


def is_mapeditor_admin() -> bool:
    """
    Check if the user is a mapeditor admin.
    :return:
    """
    mapeditor_role = get_session('user-mapeditor-role')
    return mapeditor_role and 'mapeditor-admin' in mapeditor_role
