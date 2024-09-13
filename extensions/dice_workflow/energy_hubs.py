import uuid

from esdl import esdl
from esdl.support_functions import deepcopy
from src.log import get_logger

logger = get_logger(__name__)

def generate_energy_hub(es: esdl.EnergySystem, building_ids: list[str]) -> esdl.EnergySystem | None:
    es_instance: esdl.Instance = es.instance[0]

    # Find the ElectricityNetwork asset
    assets = es.eAllContents()
    enetwork: esdl.ElectricityNetwork | None = None
    buildings: list[esdl.Building] = []
    for asset in assets:
        if isinstance(asset, esdl.ElectricityNetwork):
            logger.info(f"Found ElectricityNetwork: {asset.name}")
            enetwork = asset
        if isinstance(asset, esdl.Building):
            if asset.id in building_ids:
                buildings.append(asset)
    if enetwork is None:
        logger.warning("No ElectricityNetwork found in ESDL file")
        return None

    if len(buildings) == 0:
        logger.warning("No buildings found in ESDL file")
        return None

    if len(buildings) != len(building_ids):
        logger.warning("Not all companies found in ESDL file")
        return None

    logger.info(f"Found {len(buildings)} buildings to connect to the ElectricityNetwork")

    # Find the inport and outport of the ElectricityNetwork
    enetwork_inport: esdl.InPort | None = None
    enetwork_outport: esdl.OutPort | None = None
    for port in enetwork.port:
        if isinstance(port, esdl.InPort):
            enetwork_inport = port
        if isinstance(port, esdl.OutPort):
            enetwork_outport = port

    if enetwork_inport is None or enetwork_outport is None:
        logger.warning("No inport or outport found in ElectricityNetwork")
        return None

    carrier: esdl.EnergyCarrier = enetwork_inport.carrier
    carrier_emission_unit = carrier.emissionUnit
    carrier_energy_content_unit = carrier.energyContentUnit

    # Create a new EnergyCarrier for the internal electricity
    esi: esdl.EnergySystemInformation = es.energySystemInformation
    carrier_internal: esdl.EnergyCarrier = esdl.EnergyCarrier(
        id=str(uuid.uuid4()),
        name="Elektriciteit intern",
        energyCarrierType=carrier.energyCarrierType,
        emission=carrier.emission,
        energyContent=carrier.energyContent,
        stateOfMatter=carrier.stateOfMatter,
        emissionUnit=esdl.QuantityAndUnitType(
            id=str(uuid.uuid4()),
            unit=carrier_emission_unit.unit,
            physicalQuantity=carrier_emission_unit.physicalQuantity,
            multiplier=carrier_emission_unit.multiplier,
            perUnit=carrier_emission_unit.perUnit,
        ),
        energyContentUnit=esdl.QuantityAndUnitType(
            id=str(uuid.uuid4()),
            unit=carrier_energy_content_unit.unit,
            physicalQuantity=carrier_energy_content_unit.physicalQuantity,
            multiplier=carrier_energy_content_unit.multiplier,
            perUnit=carrier_energy_content_unit.perUnit,
        ),
    )
    esi.carriers.carrier.append(carrier_internal)

    # Create an internal ElectricityNetwork
    enetwork_internal = esdl.ElectricityNetwork(
        id=str(uuid.uuid4()),
        name="Elektriciteitsnetwerk intern",
    )
    enetwork_internal_inport = esdl.InPort(
        id=str(uuid.uuid4()), name="In", carrier=carrier_internal
    )
    enetwork_internal_outport = esdl.OutPort(
        id=str(uuid.uuid4()), name="Out", carrier=carrier_internal
    )
    enetwork_internal.port.append(enetwork_internal_inport)
    enetwork_internal.port.append(enetwork_internal_outport)
    es.instance[0].area.asset.append(enetwork_internal)

    # Create two GenericConversion assets, one for levering and one for teruglevering.
    terug_conv = esdl.GenericConversion(
        id=str(uuid.uuid4()),
        name="Teruglevering Connection",
        efficiency=1.0,
        power=1000000.0,
    )
    dbs = esdl.DrivenBySupply(
        id=str(uuid.uuid4()),
        name="DbD voor teruglevering energy hub",
        energyAsset=terug_conv,
    )
    es.services.service.append(dbs)
    terug_conv.controlStrategy = dbs

    levering_conv = esdl.GenericConversion(
        id=str(uuid.uuid4()),
        name="Levering Connection",
        efficiency=1.0,
        power=1000000.0,
    )
    dbd = esdl.DrivenByDemand(
        id=str(uuid.uuid4()),
        name="DbS voor levering energy hub",
        energyAsset=levering_conv,
    )
    es.services.service.append(dbd)
    levering_conv.controlStrategy = dbd
    es_instance.area.asset.append(terug_conv)
    es_instance.area.asset.append(levering_conv)

    # Create InPorts and OutPorts for the GenericConversions.
    # So for teruglevering, the inport is connected to the energy hub buildings through an internal network, the outport
    # to the electricity network.
    # For levering, the inport is connected to the electricity network, the outport to the energy hub buildings through
    # the internal network.
    terug_conv_inport = esdl.InPort(id=str(uuid.uuid4()), carrier=carrier_internal)
    terug_conv_outport = esdl.OutPort(id=str(uuid.uuid4()), carrier=carrier)
    terug_conv.port.append(terug_conv_inport)
    terug_conv.port.append(terug_conv_outport)
    dbs.inPort = terug_conv_inport

    levering_conv_inport = esdl.InPort(id=str(uuid.uuid4()), carrier=carrier)
    levering_conv_outport = esdl.OutPort(id=str(uuid.uuid4()), carrier=carrier_internal)
    levering_conv.port.append(levering_conv_inport)
    levering_conv.port.append(levering_conv_outport)
    dbd.outPort = levering_conv_outport

    dbs.inPort = terug_conv_inport
    dbd.outPort = levering_conv_outport

    # Connect the InPorts and OutPorts of the GenericConversions to the InPort and OutPort of the ElectricityNetwork
    terug_conv_outport.connectedTo.append(enetwork_inport)
    levering_conv_inport.connectedTo.append(enetwork_outport)

    # Connect the InPort and Outports of the GenericConversions to the InPort and OutPort of the internal ElectricityNetwork
    terug_conv_inport.connectedTo.append(enetwork_internal_outport)
    levering_conv_outport.connectedTo.append(enetwork_internal_inport)

    # For every building, find its EConnection. Then disconnect its inport from the ElectricityNetwork,
    # And connect it to internal ElectricityNetwork.
    # Also, for all assets and their ports, switch to the internal carrier.
    for building in buildings:
        assets = building.eAllContents()
        econn: esdl.ElectricityConnection | None = None
        for asset in assets:
            if isinstance(asset, esdl.EConnection):
                econn = asset
            if hasattr(asset, "port"):
                port = asset.port
                if isinstance(port, int):
                    pass
                else:
                    for port in asset.port:
                        if port.carrier.id == carrier.id:
                            port.carrier = carrier_internal

        if econn is None:
            logger.warning(f"No ElectricityConnection found in building {building.name}")
            return None

        econn_inport: esdl.InPort | None = None
        econn_outport: esdl.OutPort | None = None
        for port in econn.port:
            if isinstance(port, esdl.InPort):
                econn_inport = port
            if isinstance(port, esdl.OutPort):
                econn_outport = port

        if econn_inport is None or econn_outport is None:
            logger.warning(
                f"No inport or outport found in ElectricityConnection of building {building.name}"
            )
            return None

        # Disconnect the inport from the ElectricityNetwork
        enetwork_outport.connectedTo.remove(econn_inport)

        # Connect the inport to the internal ElectricityNetwork
        econn_inport.connectedTo.append(enetwork_internal_outport)

    return es
