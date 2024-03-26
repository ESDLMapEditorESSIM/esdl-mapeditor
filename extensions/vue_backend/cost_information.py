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

from pyecore.ecore import EReference
from extensions.session_manager import get_session, set_session, get_handler
from esdl import esdl
from esdl.processing.ESDLQuantityAndUnits import unit_to_string
from esdl.esdl_handler import EnergySystemHandler
import src.log as log
from uuid import uuid4
from utils.utils import str2float, camelCaseToWords
import re

logger = log.get_logger(__name__)


def get_cost_information(obj):
    """
    Builds up a dictionary with cost information about the object

    :param EObject obj: the object for which the cost information must be collected
    :return dict: the dictionary with all required information
    """
    result = list()
    # for x in esdl.costInformation.eAllStructuralFeatures:
    #     if isinstance(x, EReference):
    #         result[x.name] = dict()
    # result['investmentCosts'] = dict()
    # result['installationCosts'] = dict()
    # result['fixedOperationalAndMaintenanceCosts'] = dict()
    # result['variableOperationalAndMaintenanceCosts'] = dict()
    # result['marginalCosts'] = dict()

    ci = obj.costInformation
    for x in esdl.CostInformation.eClass.eAllStructuralFeatures():
        if isinstance(x, EReference):
            ci_instance = dict()
            ci_instance['key'] = str(uuid4())
            ci_instance['name'] = x.name
            ci_instance['uiname'] = camelCaseToWords(x.name)
            ci_instance['changed'] = False

            if ci:
                profile = ci.eGet(x)
                if profile:
                    if isinstance(profile, esdl.SingleValue):
                        ci_instance['value'] = profile.value
                        
                        if profile.profileQuantityAndUnit:
                            qau = profile.profileQuantityAndUnit
                            if isinstance(qau, esdl.QuantityAndUnitReference):
                                qau = qau.reference
                            ci_instance['unit'] = unit_to_string(qau)
                        else:
                            ci_instance['unit'] = None
                    else:
                        logger.warn('Cost information profiles other than SingleValue are not supported')
                        ci_instance['value'] = None
                else:
                    ci_instance['value'] = None
            else:
                ci_instance['value'] = None

            result.append(ci_instance)
 
    return result


def _change_cost_unit(qau, cost_unit_string):
    qau.multiplier = esdl.MultiplierEnum.NONE
    qau.unit = esdl.UnitEnum.NONE
    qau.perMultiplier = esdl.MultiplierEnum.NONE
    qau.perUnit = esdl.UnitEnum.NONE
    qau.perTimeUnit = esdl.TimeUnitEnum.NONE

    if re.match(r"%", cost_unit_string):
        qau.unit = esdl.UnitEnum.PERCENT
    elif re.match(r"EUR", cost_unit_string):
        qau.unit = esdl.UnitEnum.EURO
    elif re.match(r"USD", cost_unit_string):
        qau.unit = esdl.UnitEnum.DOLLAR
    else:
        logger.warn('probably not a cost unit')

    if re.match(r"\w+/Wh", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.WATTHOUR
        qau.perMultiplier = esdl.MultiplierEnum.NONE
    elif re.match(r"\w+/kWh", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.WATTHOUR
        qau.perMultiplier = esdl.MultiplierEnum.KILO
    elif re.match(r"\w+/MWh", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.WATTHOUR
        qau.perMultiplier = esdl.MultiplierEnum.MEGA
    elif re.match(r"\w+/GWh", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.WATTHOUR
        qau.perMultiplier = esdl.MultiplierEnum.GIGA
    elif re.match(r"\w+/TWh", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.WATTHOUR
        qau.perMultiplier = esdl.MultiplierEnum.TERA
    elif re.match(r"\w+/J", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.JOULE
        qau.perMultiplier = esdl.MultiplierEnum.NONE
    elif re.match(r"\w+/kJ", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.JOULE
        qau.perMultiplier = esdl.MultiplierEnum.KILO
    elif re.match(r"\w+/MJ", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.JOULE
        qau.perMultiplier = esdl.MultiplierEnum.MEGA
    elif re.match(r"\w+/GJ", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.JOULE
        qau.perMultiplier = esdl.MultiplierEnum.GIGA
    elif re.match(r"\w+/TJ", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.JOULE
        qau.perMultiplier = esdl.MultiplierEnum.TERA
    elif re.match(r"\w+/W", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.WATT
        qau.perMultiplier = esdl.MultiplierEnum.NONE
    elif re.match(r"\w+/kW", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.WATT
        qau.perMultiplier = esdl.MultiplierEnum.KILO
    elif re.match(r"\w+/MW", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.WATT
        qau.perMultiplier = esdl.MultiplierEnum.MEGA
    elif re.match(r"\w+/GW", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.WATT
        qau.perMultiplier = esdl.MultiplierEnum.GIGA
    elif re.match(r"\w+/TW", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.WATT
        qau.perMultiplier = esdl.MultiplierEnum.TERA
    elif re.match(r"\w+/km", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.METRE
        qau.perMultiplier = esdl.MultiplierEnum.KILO
    elif re.match(r"\w+/m3", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.CUBIC_METRE
        qau.perMultiplier = esdl.MultiplierEnum.NONE
    elif re.match(r"\w+/m2", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.SQUARE_METRE
        qau.perMultiplier = esdl.MultiplierEnum.NONE
    elif re.match(r"\w+/m", cost_unit_string):
        qau.perUnit = esdl.UnitEnum.METRE
        qau.perMultiplier = esdl.MultiplierEnum.NONE

    if re.match(r".+/yr", cost_unit_string):
        qau.perTimeUnit = esdl.TimeUnitEnum.YEAR
    # make sure the description matches this updated/new qau
    qau.description = 'Cost in ' + unit_to_string(qau)


def _create_cost_qau(cost_unit_string):
    qau = esdl.QuantityAndUnitType(id=str(uuid4()), physicalQuantity=esdl.PhysicalQuantityEnum.COST, description='Cost in '+cost_unit_string)
    _change_cost_unit(qau, cost_unit_string)
    print('new qau', EnergySystemHandler.attr_to_dict(qau))
    return qau


def set_cost_information(obj, cost_information_data):
    esh = get_handler()
    active_es_id = get_session('active_es_id')
    
    obj_ci = obj.costInformation
    if not obj_ci:
        obj_ci = esdl.CostInformation(id=str(uuid4()))
        obj.costInformation = obj_ci
        esh.add_object_to_dict(active_es_id, obj.costInformation)

    for ci_component in cost_information_data:
        ci_component_name = ci_component['name']

        attribute = obj_ci.eClass.findEStructuralFeature(ci_component_name)
        if attribute is not None:
            if ci_component['changed']:
                current_cost_component_profile = obj_ci.eGet(ci_component_name)
                if current_cost_component_profile:
                    if ci_component['value'] is None:
                        current_cost_component_profile.delete()
                    elif isinstance(current_cost_component_profile, esdl.SingleValue):
                        new_value_str = ci_component['value']
                        if new_value_str != '':
                            current_cost_component_profile.value = str2float(new_value_str)

                        qau = current_cost_component_profile.profileQuantityAndUnit
                        if qau:
                            if isinstance(qau, esdl.QuantityAndUnitReference):
                                qau = qau.reference
                            current_unit = unit_to_string(qau)
                            if current_unit != ci_component['unit']:
                                _change_cost_unit(qau, ci_component['unit'])
                        else:
                            if ci_component['unit'] is not None and ci_component['unit'] != '':
                                qau = _create_cost_qau(ci_component['unit'])
                else:
                    if ci_component['value'] is not None and ci_component['value'] != '':
                        new_cost_component_profile = esdl.SingleValue(id=str(uuid4()))
                        new_cost_component_profile.value = str2float(ci_component['value'])
                        if 'unit' in ci_component and ci_component['unit'] is not None and ci_component['unit'] != '':
                            new_cost_component_profile.profileQuantityAndUnit = _create_cost_qau(ci_component['unit'])

                        obj_ci.eSet(ci_component_name, new_cost_component_profile)
                        esh.add_object_to_dict(active_es_id, new_cost_component_profile)
