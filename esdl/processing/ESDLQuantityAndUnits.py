import uuid
from esdl import esdl
from pyecore.ecore import EClass, EEnum, EAttribute, EOrderedSet, EObject


def get_qau_information(esdl_doc = None):
    qaut = esdl.QuantityAndUnitType()

    attributes = dict()
    for x in qaut.eClass.eAllStructuralFeatures():
        # print('{} is of type {}'.format(x.name, x.eClass.name))
        if isinstance(x, EAttribute):
            attr = dict()
            attr['name'] = x.name
            attr['type'] = x.eType.name
            # if isinstance(x., EEnum):
            #    attr['value'] = list(es.eGet(x))
            attr['value'] = qaut.eGet(x)
            if attr['value'] is not None:
                if x.many:
                    if isinstance(attr['value'], EOrderedSet):
                        attr['value'] = [x.name for x in attr['value']]
                        attr['many'] = True
                    else:
                        attr['value'] = list(x.eType.to_string(attr['value']))
                else:
                    attr['value'] = x.eType.to_string(attr['value'])
            if isinstance(x.eType, EEnum):
                attr['type'] = 'EEnum'
                attr['enum_type'] = x.eType.name
                attr['options'] = list(lit.name for lit in x.eType.eLiterals)
                attr['default'] = x.eType.default_value.name
            else:
                attr['default'] = x.eType.default_value
                if x.eType.default_value is not None:
                    attr['default'] = x.eType.to_string(x.eType.default_value)
            if x.eType.name == 'EBoolean':
                attr['options'] = ['true', 'false']
            attr['doc'] = x.__doc__
            if x.__doc__ is None and esdl_doc is not None:
                attr['doc'] = esdl_doc.get_doc(qaut.eClass.name, x.name)

            attributes[x.name] = attr

    return attributes


def get_profile_type_enum_values():
    ptenum = esdl.ProfileTypeEnum
    values = list(pt.name for pt in ptenum.eType.eLiterals)

    values.remove("UNDEFINED")
    values.sort()
    values.insert(0, "UNDEFINED")

    return values


def build_qau_from_dict(qau_dict):
    qau = esdl.QuantityAndUnitType()

    if 'id' in qau_dict:
        qau.id = qau_dict['id']
    else:
        qau.id = str(uuid.uuid4())

    if 'description' in qau_dict:
        qau.description = qau_dict['description']
    else:
        qau.description = ''

    if 'physicalQuantity' in qau_dict:
        qau.physicalQuantity = esdl.PhysicalQuantityEnum.from_string(qau_dict['physicalQuantity'])
    if 'multiplier' in qau_dict:
        qau.multiplier = esdl.MultiplierEnum.from_string(qau_dict['multiplier'])
    if 'unit' in qau_dict:
        qau.unit = esdl.UnitEnum.from_string(qau_dict['unit'])
    if 'perMultiplier' in qau_dict:
        qau.perMultiplier = esdl.MultiplierEnum.from_string(qau_dict['perMultiplier'])
    if 'perUnit' in qau_dict:
        qau.perUnit = esdl.UnitEnum.from_string(qau_dict['perUnit'])
    if 'perTimeUnit' in qau_dict:
        qau.perTimeUnit = esdl.TimeUnit.from_string(qau_dict['perTimeUnit'])

    return qau