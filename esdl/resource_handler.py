from pyecore.resources import ResourceSet


class ResourceHandlerBase:
    """
    Base class for all handlers and mixins. Mainly exists to define available variables.
    """
    rset: ResourceSet
