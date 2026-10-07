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

from typing import Union, Type

from pyecore.ecore import EObject, EClass, MetaEClass

from esdl import esdl
from esdl.ecore_documentation import EcoreDocumentation

__esdl_ecore_documentation = None


"""
Convert between ESDL quantities and units, e.g. MW to kW or EUR/kW to MEUR/GW 
including some convertable units, e.g. Joule to Wh and Kelvin to Celsius)
"""

POWER_IN_TW = esdl.QuantityAndUnitType(description="Power in TW", id="POWER_in_TW",
                                       physicalQuantity=esdl.PhysicalQuantityEnum.POWER,
                                       unit=esdl.UnitEnum.WATT,
                                       multiplier=esdl.MultiplierEnum.TERA)
"""Power in TW [QuantityAndUnitType]"""

POWER_IN_GW = esdl.QuantityAndUnitType(description="Power in GW", id="POWER_in_GW",
                                       physicalQuantity=esdl.PhysicalQuantityEnum.POWER,
                                       unit=esdl.UnitEnum.WATT,
                                       multiplier=esdl.MultiplierEnum.GIGA)
"""Power in GW [QuantityAndUnitType]"""

POWER_IN_MW = esdl.QuantityAndUnitType(description="Power in MW", id="POWER_in_MW",
                                       physicalQuantity=esdl.PhysicalQuantityEnum.POWER,
                                       unit=esdl.UnitEnum.WATT,
                                       multiplier=esdl.MultiplierEnum.MEGA)
"""Power in MW [QuantityAndUnitType]"""

POWER_IN_kW = esdl.QuantityAndUnitType(description="Power in kW", id="POWER_in_kW",
                                      physicalQuantity=esdl.PhysicalQuantityEnum.POWER,
                                      unit=esdl.UnitEnum.WATT,
                                      multiplier=esdl.MultiplierEnum.KILO)
"""Power in kW [QuantityAndUnitType]"""

POWER_IN_W = esdl.QuantityAndUnitType(description="Power in Watt", id="POWER_in_W",
                                      physicalQuantity=esdl.PhysicalQuantityEnum.POWER,
                                      unit=esdl.UnitEnum.WATT)
"""Power in W [QuantityAndUnitType]"""

ENERGY_IN_PJ = esdl.QuantityAndUnitType(description="Energy in PJ", id="ENERGY_in_PJ",
                                        physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                                        unit=esdl.UnitEnum.JOULE,
                                        multiplier=esdl.MultiplierEnum.PETA)
"""Energy in PJ [QuantityAndUnitType]"""

ENERGY_IN_TJ = esdl.QuantityAndUnitType(description="Energy in TJ", id="ENERGY_in_TJ",
                                        physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                                        unit=esdl.UnitEnum.JOULE,
                                        multiplier=esdl.MultiplierEnum.TERA)
"""Energy in TJ [QuantityAndUnitType]"""

ENERGY_IN_GJ = esdl.QuantityAndUnitType(description="Energy in GJ", id="ENERGY_in_GJ",
                                        physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                                        unit=esdl.UnitEnum.JOULE,
                                        multiplier=esdl.MultiplierEnum.GIGA)
"""Energy in GJ [QuantityAndUnitType]"""

ENERGY_IN_MJ = esdl.QuantityAndUnitType(description="Energy in MJ", id="ENERGY_in_MJ",
                                        physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                                        unit=esdl.UnitEnum.JOULE,
                                        multiplier=esdl.MultiplierEnum.MEGA)
"""Energy in MJ [QuantityAndUnitType]"""

ENERGY_IN_kJ = esdl.QuantityAndUnitType(description="Energy in kJ", id="ENERGY_in_kJ",
                                        physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                                        unit=esdl.UnitEnum.JOULE,
                                        multiplier=esdl.MultiplierEnum.KILO)
"""Energy in kJ [QuantityAndUnitType]"""

ENERGY_IN_J = esdl.QuantityAndUnitType(description="Energy in J", id="ENERGY_in_J",
                                        physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                                        unit=esdl.UnitEnum.JOULE,
                                        multiplier=esdl.MultiplierEnum.NONE)
"""Energy in J [QuantityAndUnitType]"""

ENERGY_IN_TWh = esdl.QuantityAndUnitType(description="Energy in TWh", id="ENERGY_in_TWh",
                                         physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                                         unit=esdl.UnitEnum.WATTHOUR,
                                         multiplier=esdl.MultiplierEnum.TERA)
"""Energy in TWh [QuantityAndUnitType]"""

ENERGY_IN_GWh = esdl.QuantityAndUnitType(description="Energy in GWh", id="ENERGY_in_GWh",
                                         physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                                         unit=esdl.UnitEnum.WATTHOUR,
                                         multiplier=esdl.MultiplierEnum.GIGA)
"""Energy in GWh [QuantityAndUnitType]"""

ENERGY_IN_MWh = esdl.QuantityAndUnitType(description="Energy in MWh", id="ENERGY_in_MWh",
                                         physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                                         unit=esdl.UnitEnum.WATTHOUR,
                                         multiplier=esdl.MultiplierEnum.MEGA)
"""Energy in MWh [QuantityAndUnitType]"""

ENERGY_IN_kWh = esdl.QuantityAndUnitType(description="Energy in kWh", id="ENERGY_in_kWh",
                                         physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                                         unit=esdl.UnitEnum.WATTHOUR,
                                         multiplier=esdl.MultiplierEnum.KILO)
"""Energy in kWh [QuantityAndUnitType]"""

ENERGY_IN_Wh = esdl.QuantityAndUnitType(description="Energy in Wh", id="ENERGY_in_Wh",
                                         physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                                         unit=esdl.UnitEnum.WATTHOUR,
                                         multiplier=esdl.MultiplierEnum.NONE)
"""Energy in Wh [QuantityAndUnitType]"""

COST_IN_MEur = esdl.QuantityAndUnitType(description="Cost in MEur", id="COST_in_MEUR",
                                        physicalQuantity=esdl.PhysicalQuantityEnum.COST,
                                        unit=esdl.UnitEnum.EURO,
                                        multiplier=esdl.MultiplierEnum.MEGA)
"""Cost in Million Euro [QuantityAndUnitType]"""

COST_IN_Eur_per_MWh = esdl.QuantityAndUnitType(description="Cost in €/MWh", id="COST_in_EURperMWH",
                                        physicalQuantity=esdl.PhysicalQuantityEnum.COST,
                                        unit=esdl.UnitEnum.EURO,
                                        perMultiplier=esdl.MultiplierEnum.MEGA,
                                        perUnit=esdl.UnitEnum.WATTHOUR)
"""Cost in Euro per MWh [QuantityAndUnitType]"""

COST_IN_Eur_per_GJ = esdl.QuantityAndUnitType(description="Cost in €/GJ", id="COST_in_EURperGJ",
                                        physicalQuantity=esdl.PhysicalQuantityEnum.COST,
                                        unit=esdl.UnitEnum.EURO,
                                        perMultiplier=esdl.MultiplierEnum.GIGA,
                                        perUnit=esdl.UnitEnum.JOULE)
"""Cost in Euro per GigaJoule [QuantityAndUnitType]"""

COST_IN_MEur_per_GW_per_year = esdl.QuantityAndUnitType(description="Cost in M€/GW/yr", id="COST_in_MEURperGWperYear",
                                        physicalQuantity=esdl.PhysicalQuantityEnum.COST,
                                        multiplier=esdl.MultiplierEnum.MEGA,
                                        unit=esdl.UnitEnum.EURO,
                                        perMultiplier=esdl.MultiplierEnum.GIGA,
                                        perUnit=esdl.UnitEnum.WATT,
                                        perTimeUnit=esdl.TimeUnitEnum.YEAR)
"""Operational costs (OPEX) in MEUR/GW/yr [QuantityAndUnitType]"""

COST_IN_MEur_per_GW = esdl.QuantityAndUnitType(description="Cost in M€/GW", id="COST_in_MEURperGW",
                                        physicalQuantity=esdl.PhysicalQuantityEnum.COST,
                                        multiplier=esdl.MultiplierEnum.MEGA,
                                        unit=esdl.UnitEnum.EURO,
                                        perMultiplier=esdl.MultiplierEnum.GIGA,
                                        perUnit=esdl.UnitEnum.WATT)
"""Installation cost (CAPEX) in MEUR/GW [QuantityAndUnitType]"""

COST_IN_MEur_per_PJ = esdl.QuantityAndUnitType(description="Cost in M€/PJ", id="COST_in_MEURperPJ",
                                        physicalQuantity=esdl.PhysicalQuantityEnum.COST,
                                        multiplier=esdl.MultiplierEnum.MEGA,
                                        unit=esdl.UnitEnum.EURO,
                                        perMultiplier=esdl.MultiplierEnum.GIGA,
                                        perUnit=esdl.UnitEnum.JOULE)
"""Variable cost in MEUR/PJ [QuantityAndUnitType]"""


def equals(base_unit: esdl.QuantityAndUnitType, other: esdl.QuantityAndUnitType) -> bool:
    """Checks if two units are equal based on physical quantity, multiplier, perMultiplier and perUnit attributes"""
    if base_unit.unit == other.unit and \
            base_unit.multiplier == other.multiplier and \
            base_unit.perUnit == other.perUnit and \
            base_unit.perMultiplier == other.perMultiplier and \
            base_unit.perTimeUnit == other.perTimeUnit and \
            base_unit.perScope == other.perScope and \
            base_unit.physicalQuantity == other.physicalQuantity:
        return True
    return False


def convertable(source: esdl.UnitEnum, target: esdl.UnitEnum) -> bool:
    """Checks if a unit can be converted to another unit, e.g. Joule -> Wh or Kelvin -> Celsius"""
    try:
        convert_unit(0, source, target)  # check if convert_unit does not raise an exception
        return True
    except UnitException as e:
        return False


def same_physical_quantity(source: esdl.QuantityAndUnitType, target: esdl.QuantityAndUnitType) -> bool:
    """Returns if two esdl.QuantityAndUnitType are equal or if the unit is convertable (e.g. J to Wh)"""
    return source.physicalQuantity == target.physicalQuantity \
        and source.perTimeUnit == target.perTimeUnit \
        and (source.unit == target.unit and source.perUnit == target.perUnit) or \
            (convertable(source.unit, target.unit) and convertable(source.perUnit, target.perUnit))


def convert_to_unit(value: float, source_unit: esdl.AbstractQuantityAndUnit, target_unit: esdl.AbstractQuantityAndUnit) -> float:
    """
    Converts a value from the source_unit into a target_unit

    example: converted_value: float = convert_to_unit(10, ENERGY_IN_J, ENERGY_IN_MWh)

    :param value: the value that needs to be converted
    :param source_unit: the QuantityAndUnit of the source (can also be a reference)
    :param target_unit: the QuantityAndUnit of the target (can also be a reference, they are resolved to a Type)
    :return: the converted value
    """
    if source_unit is None or target_unit is None:
        raise UnitException(f'Missing source unit in unit conversion: source:{source_unit}, target:{target_unit}')
    while isinstance(source_unit, esdl.QuantityAndUnitReference):  # resolve QaU references if necessary
        source_unit = source_unit.reference
    while isinstance(target_unit, esdl.QuantityAndUnitReference):  # resolve QaU references if necessary
        target_unit = target_unit.reference
    if same_physical_quantity(target_unit, source_unit):
        return convert_unit(
            convert_unit(
                convert_multiplier(source_unit, target_unit) * value, source_unit.unit, target_unit.unit), source_unit.perUnit, target_unit.perUnit)

    else:
        raise UnitException(f'Conversion mismatch between units: source_unit={source_unit}, target_unit={target_unit}')


def convert_multiplier(source: esdl.QuantityAndUnitType, target: esdl.QuantityAndUnitType) -> float:
    """
    Calculates the factor between the source unit and the target unit
    """
    value = multipier_value(source.multiplier) / multipier_value(target.multiplier) * \
        multipier_value(target.perMultiplier) / multipier_value(source.perMultiplier)
    #print(f"{multipier_value(source.multiplier)} / {multipier_value(target.multiplier)} * {multipier_value(target.perMultiplier)} / {multipier_value(source.perMultiplier)}")
    #print(f"Converting source {source} to {target}: factor={value}")
    return value


    # MultiplierEnum
    # ['NONE', 'ATTO', 'FEMTO', 'PICO', 'NANO', 'MICRO',
    #  'MILLI', 'CENTI', 'DECI', 'DEKA', 'HECTO', 'KILO', 'MEGA',
    #  'GIGA', 'TERA', 'TERRA', 'PETA', 'EXA']
factors = [1, 1E-18, 1E-15, 1E-12, 1E-9, 1E-6, 1E-3, 1E-2, 1E-1, 1E1,
               1E2, 1E3, 1E6, 1E9, 1E12, 1E12, 1E15, 1E18]


def multipier_value(multiplier: esdl.MultiplierEnum):
    """Converts ESDL MultiplierEnum into a numeric value."""
    return factors[esdl.MultiplierEnum.eLiterals.index(multiplier)]


unit_mapping = {
    esdl.UnitEnum.WATTHOUR: {esdl.UnitEnum.JOULE: {'type': 'MULTIPLY', 'value': 3600.0}},
    esdl.UnitEnum.JOULE: {esdl.UnitEnum.WATTHOUR: {'type': 'MULTIPLY', 'value': 1.0/3600.0}},
    esdl.UnitEnum.DEGREES_CELSIUS: {esdl.UnitEnum.KELVIN: {'type': 'ADDITION', 'value': 273.15}},
    esdl.UnitEnum.KELVIN: {esdl.UnitEnum.DEGREES_CELSIUS: {'type': 'ADDITION', 'value': -273.15}},
    esdl.UnitEnum.TONNE: {esdl.UnitEnum.GRAM: {'type': 'MULTIPLY', 'value': 1E6}},
    esdl.UnitEnum.GRAM: {esdl.UnitEnum.TONNE: {'type': 'MULTIPLY', 'value': 1E-6}},
}


def convert_unit(value: float, source_quantity_unit: esdl.UnitEnum, target_quantity_unit: esdl.UnitEnum) -> float:
    """
    Does some basic unit conversion, only Joule to Wh, Wh to Joule and \N{DEGREE SIGN}C to Kelvin and vice versa.
    Can only convert units when physical quantities are the same (e.g. Energy, Temperature)
    """
    if source_quantity_unit == target_quantity_unit:
        return value
    else:
        if source_quantity_unit in unit_mapping:
            source_map = unit_mapping[source_quantity_unit]
            if target_quantity_unit in source_map:
                conversion = source_map[target_quantity_unit]
                if conversion['type'] == 'MULTIPLY':
                    #print(f"Unit conversion factor {source_quantity_unit.name} to {target_quantity_unit.name} factor={conversion['value']}")
                    return value * conversion['value']
                elif conversion['type'] == 'ADDITION':
                    return value + conversion['value']
            else:
                raise UnitException(f"No mapping available from {source_quantity_unit.name} to {target_quantity_unit.name}")
        else:
            raise UnitException(f"Cannot convert {source_quantity_unit.name} into {target_quantity_unit.name}")


class UnitException(Exception):
    """Thrown when two esdl.QuantityAndUnitTypes can not be converted"""
    pass



def get_attribute_unit(esdl_class: Union[EClass, EObject, Type, str], attribute: str) -> str:
    """
    Retrieves the unit defined in the ESDL ecore schema for a specific attribute

    example: get_attribute_unit("PowerPlant", "power"), or
             get_attribute_unit(esdl.PowerPlant, "power"), or
             get_attribute_unit(myPowerPlant, "power")

    :param esdl_class: the ESDL class (as string, ESDL class or ESDL Object)
    :param attribute: string describing the attribute of the esdl_class
    :return: a string with the unit (e.g. W, m, years)
    """
    global __esdl_ecore_documentation
    if __esdl_ecore_documentation is None:
        __esdl_ecore_documentation = EcoreDocumentation()
    esdl_class_str = esdl_class
    if isinstance(esdl_class, EObject):
        # noinspection PyUnresolvedReferences
        esdl_class_str = esdl_class.eClass.name
    elif isinstance(esdl_class, MetaEClass):
        # noinspection PyUnresolvedReferences
        esdl_class_str = esdl_class.eClass.name
    return __esdl_ecore_documentation.get_unit(className=esdl_class_str, attributeName=attribute)
