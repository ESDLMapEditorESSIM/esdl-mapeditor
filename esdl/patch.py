#  This work is based on original code developed and copyrighted by TNO 2023.
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

from pyecore.ecore import EObject, EClass, EAttribute
from pyecore.utils import alias

import esdlproject
from esdl import support_functions, esdl


def esdl_attr_to_dict(esdl_object):
    d = dict()
    d['esdlType'] = esdl_object.eClass.name
    for attr in dir(esdl_object):
        attr_value = esdl_object.eGet(attr)
        if attr_value is not None:
            d[attr] = attr_value
    return d


def patch_esdl():
    """
    Patch the ESDL classes to add some functionality that is not in the original ESDL classes.

    TODO: Should be moved to PyESDL.
    """
    # fix python builtin 'from' that is also used in ProfileElement as attribute
    # use 'start' instead of 'from' when using a ProfileElement
    # and make sure that it is serialized back as 'from' instead of 'from_'
    esdl.ProfileElement.from_.name = 'from'
    setattr(esdl.ProfileElement, 'from', esdl.ProfileElement.from_)
    alias('start', esdl.ProfileElement.from_)
    # also for FromToIntItem
    esdl.FromToIntItem.from_.name = 'from'
    setattr(esdl.FromToIntItem, 'from', esdl.FromToIntItem.from_)
    alias('start', esdl.FromToIntItem.from_)
    # also for FromToDoubleItem
    esdl.FromToDoubleItem.from_.name = 'from'
    setattr(esdl.FromToDoubleItem, 'from', esdl.FromToDoubleItem.from_)
    alias('start', esdl.FromToDoubleItem.from_)

    # add support for cloning of EObjects and copy.copy()
    setattr(EObject, '__copy__', support_functions.clone)
    setattr(EObject, 'clone', support_functions.clone)

    # add support for deepcopying EObjects and copy.deepcopy()
    setattr(EObject, '__deepcopy__', support_functions.deepcopy)
    setattr(EObject, 'deepcopy', support_functions.deepcopy)

    # have a nice __repr__ for some ESDL classes when printing ESDL objects (includes all Assets and EnergyAssets)
    esdl.EnergySystem.__repr__ = \
        lambda x: '{}: ({})'.format(x.name, esdl_attr_to_dict(x))

    esdl.Port.__repr__ = \
        lambda x: f'<{x.eClass.name}[{x.name}] of {x.eContainer().name if x.eContainer() else None}, id="{x.id}">'
    esdl.Area.__repr__ = \
        lambda x: f'<{x.eClass.name}[{x.name}] of {x.eContainer().name if x.eContainer() else None}, id="{x.id}">'

    esdlproject.DetailedChange.__repr__ = \
        lambda x: f'<{x.eClass.name} {attr_string(x)}>'
        #lambda x: f'<{x.eClass.name} ownerFragment="{x.ownerFragment}", feature="{x.feature}", stringValue="{x.stringValue}", previousValue="{x.previousValue}", objectFragment="{x.objectFragment}">'
    esdlproject.HighLevelChange.__repr__ = \
        lambda x: f'<{x.eClass.name} label="{x.label}", len(change)={len(x.change)}, change={x.change}>'

    def attr_string(e: EObject):
        cls: EClass = e.eClass
        s = []
        for f in cls.eAllStructuralFeatures():
            if e.eIsSet(f):
                if isinstance(f, EAttribute):
                    s.append(f'{f.name}="{e.eGet(f)}"')
                else:
                    v = e.eGet(f)
                    content = "[content]"
                    if isinstance(v, EObject):
                        content = f'<{v.eClass.name} {"name=" + v.name + "" if hasattr(v, "name") else ""}>'
                    s.append(f'{f.name}={content}')
        return ', '.join(s)