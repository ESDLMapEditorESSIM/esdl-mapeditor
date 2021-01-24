from esdl import esdl
from esdl.processing.ESDLQuantityAndUnits import *
from esdl.esdl_handler import EnergySystemHandler

esdl.QuantityAndUnitType.__repr__ = \
    lambda x: '{}'.format(EnergySystemHandler.attr_to_dict(x))


def test_qau(descr, qau):
    print("{}:".format(descr))
    qau.description = descr
    qau_str = qau_to_string(qau)
    print("- {}".format(qau_str))

    print("- Building unit from the QaU sting:")
    unit_str = unit_to_string(qau)
    unit_qau = build_qau_from_unit_string(unit_str)
    qau_dict = esh.attr_to_dict(unit_qau)
    print("  Unit: {}".format(unit_to_string(unit_qau)))
    print("  {}".format(qau_dict))


if __name__ == "__main__":
    esh = EnergySystemHandler()

    qau = esdl.QuantityAndUnitType(id=str(uuid4()))
    qau.physicalQuantity = esdl.PhysicalQuantityEnum.DIRECTION
    qau.unit = esdl.UnitEnum.DEGREES
    test_qau("Wind direction in degrees", qau)

    qau = esdl.QuantityAndUnitType(id=str(uuid4()))
    qau.physicalQuantity = esdl.PhysicalQuantityEnum.POWER
    qau.multiplier = esdl.MultiplierEnum.KILO
    qau.unit = esdl.UnitEnum.WATT
    test_qau("Power in kiloWatt", qau)

    qau = esdl.QuantityAndUnitType(id=str(uuid4()))
    qau.physicalQuantity = esdl.PhysicalQuantityEnum.ENERGY
    qau.multiplier = esdl.MultiplierEnum.TERA
    qau.unit = esdl.UnitEnum.JOULE
    test_qau("Energy in TeraJoule", qau)

    qau = esdl.QuantityAndUnitType(id=str(uuid4()))
    qau.physicalQuantity = esdl.PhysicalQuantityEnum.COEFFICIENT
    qau.unit = esdl.UnitEnum.CUBIC_METRE
    qau.perTimeUnit = esdl.TimeUnitEnum.HOUR
    qau.perUnit = esdl.UnitEnum.BAR
    test_qau("Coefficient in m³/h/bar", qau)

    qau = esdl.QuantityAndUnitType(id=str(uuid4()))
    qau.physicalQuantity = esdl.PhysicalQuantityEnum.COST
    qau.multiplier = esdl.MultiplierEnum.MEGA
    qau.unit = esdl.UnitEnum.EURO
    qau.perMultiplier = esdl.MultiplierEnum.KILO
    qau.perUnit = esdl.UnitEnum.WATT
    qau.perTimeUnit = esdl.TimeUnitEnum.YEAR
    test_qau("Maintenance costs in millions of Euros / kW / year", qau)

    qau = esdl.QuantityAndUnitType(id=str(uuid4()))
    qau.physicalQuantity = esdl.PhysicalQuantityEnum.POSITION
    qau.unit = esdl.UnitEnum.NONE
    test_qau("Position [-]", qau)
