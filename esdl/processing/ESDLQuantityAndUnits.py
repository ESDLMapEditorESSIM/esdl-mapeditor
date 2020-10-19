#  This work is based on original code developed and copyrighted by TNO 2020.
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
        qau.perTimeUnit = esdl.TimeUnitEnum.from_string(qau_dict['perTimeUnit'])

    return qau

unitdict = {
    'JOULE': 'J',
    'WATTHOUR': 'Wh',
    'WATT': 'W',
    'VOLT': 'V',
    'BAR': 'bar',
    'PSI': 'psi',
    'DEGREES_CELSIUS': 'oC',
    'KELVIN': 'K',
    'GRAM': 'g',
    'EURO': 'EUR',
    'DOLLAR': 'USD',
    'METRE': 'm',
    'SQUARE_METRE': 'm2',
    'CUBIC_METRE': 'm3',
    'LITRE': 'l',
    'WATTSECOND': 'Ws',
    'ARE': 'a',
    'HECTARE': 'ha',
    'PERCENT': '%',
    'VOLT_AMPERE': 'VA',
    'VOLT_AMPERE_REACTIVE': 'VAR'
}

timeunitdict = {
    'SECOND': 'sec',
    'MINUTE': 'min',
    'QUARTER': '15mins',
    'HOUR': 'hr',
    'DAY': 'day',
    'WEEK': 'wk',
    'MONTH': 'mon',
    'YEAR': 'yr'
}

multiplierdict = {
    'PICO': 'p',
    'NANO': 'n',
    'MICRO': 'u',
    'MILLI': 'm',
    'KILO': 'k',
    'MEGA': 'M',
    'GIGA': 'G',
    'TERRA': 'T',
    'PETA': 'P'
}


def qau_to_string(qau):
    s = qau.physicalQuantity.name
    str_unit = unit_to_string(qau)
    if str_unit != '':
        s += ' in ' + str_unit

    return s


def unit_to_string(qau):
    mult = qau.multiplier.name
    unit = qau.unit.name
    pmult = qau.perMultiplier.name
    punit = qau.perUnit.name
    ptunit = qau.perTimeUnit.name

    s = ''

    if unit != 'NONE' and unit != 'UNDEFINED':
        if mult != 'NONE' and mult != 'UNDEFINED':
            s += multiplierdict[mult]
        s += unitdict[unit]
    if punit != 'NONE' and punit != 'UNDEFINED':
        s += '/'
        if pmult != 'NONE' and pmult != 'UNDEFINED':
            s += multiplierdict[pmult]
        try:
            s += unitdict[punit]
        except KeyError:  # SECOND etc is not in the dict
            s += punit
    if ptunit != 'NONE' and ptunit != 'UNDEFINED':
        s += '/' + timeunitdict[ptunit]

    return s