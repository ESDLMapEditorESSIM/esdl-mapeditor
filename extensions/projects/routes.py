from extensions.projects import projects


@projects.route('/', methods=['GET', 'POST'])
def index():
    return {'hello': 1}
