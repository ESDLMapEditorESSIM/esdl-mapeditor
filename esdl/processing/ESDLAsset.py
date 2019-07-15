from esdl import esdl
from pyecore.ecore import EClass

# ---------------------------------------------------------------------------------------------------------------------
#  Functions to find assets in, remove assets from and add assets to areas and buildings
# ---------------------------------------------------------------------------------------------------------------------

def find_area(area, area_id):
    if area.id == area_id: return area
    for a in area.area:
        ar = find_area(a, area_id)
        if ar:
            return ar
    return None


def find_port(ports, port_id):
    for port in ports:
        if port.id == port_id:
            return port


def find_asset_in_building(building, asset_id):
    for ass in building.asset:
        if ass.id == asset_id:
            return ass
        if isinstance(ass, esdl.AbstractBuilding):
            asset = find_asset_in_building(ass, asset_id)
            if asset:
                return asset
    return None


def find_asset(area, asset_id):
    for ass in area.asset:
        if ass.id == asset_id:
            return ass
        if isinstance(ass, esdl.AbstractBuilding):
            asset = find_asset_in_building(ass, asset_id)
            if asset:
                return asset

    for subarea in area.area:
        asset = find_asset(subarea, asset_id)
        if asset:
            return asset

    return None


def find_potential(area, pot_id):
    for pot in area.potential:
        if pot.id == pot_id:
            return pot

    for subarea in area.area:
        pot = find_potential(subarea, pot_id)
        if pot:
            return pot

    return None


def find_asset_in_building_and_container(building, asset_id):
    for ass in building.asset:
        if ass.id == asset_id:
            return ass, building
        if isinstance(ass, esdl.AbstractBuilding):
            asset, build = find_asset_in_building_and_container(ass, asset_id)
            if asset:
                return asset, build
    return None


def find_asset_and_container(area, asset_id):
    for ass in area.asset:
        if ass.id == asset_id:
            return ass, area
        if isinstance(ass, esdl.AbstractBuilding):
            asset, ar = find_asset_in_building_and_container(ass, asset_id)
            if asset:
                return asset, ar

    for subarea in area.area:
        asset, ar = find_asset_and_container(subarea, asset_id)
        if asset:
            return asset, ar

    return None


def add_asset_to_area(es, asset, area_id):
    # find area with area_id
    instance = es.instance[0]
    area = instance.area
    ar = find_area(area, area_id)

    if ar:
        ar.asset.append(asset)
        return 1
    else:
        return 0


def add_asset_to_building(es, asset, building_id):
    # find area with area_id
    instance = es.instance[0]
    area = instance.area
    ar = find_asset(area, building_id)

    if ar:
        ar.add_asset_with_type(asset)
        return 1
    else:
        return 0


def remove_object_from_building(building, object_id):
    for ass in building.asset:
        if ass.id == object_id:
            for p in ass.port:
                p.connectedTo.clear()

            building.asset.remove(ass)
            print('Asset with id ' + object_id + ' removed from building with id: ', + building.id)


def recursively_remove_object_from_area(area, object_id):
    for ass in area.asset:
        if ass.id == object_id:
            for p in ass.port:
                p.connectedTo.clear()
            area.asset.remove(ass)
            print('Asset with id ' + object_id + ' removed from area with id: ' + area.id)
        if isinstance(ass, esdl.AggregatedBuilding) or isinstance(ass, esdl.Building):
            remove_object_from_building(ass, object_id)
    for pot in area.potential:
        if pot.id == object_id:
            area.potential.remove(pot)
            print('Potential with id ' + object_id + ' removed from area with id: ' + area.id)
    for sub_area in area.area:
        recursively_remove_object_from_area(sub_area, object_id)


# todo: move to EnergySystemHandler
def remove_object_from_energysystem(es, object_id):
    # find area with area_id
    instance = es.instance[0]
    area = instance.area
    recursively_remove_object_from_area(area, object_id)


def get_carrier_list(es):
    carrier_list = []
    esi = es.energySystemInformation
    if esi:
        ecs = esi.carriers
        if ecs:
            ec = ecs.carrier

            if ec:
                for carrier in ec:
                    carrier_info = {
                        'type': type(carrier).__name__,
                        'id': carrier.id,
                        'name': carrier.name,
                    }
                    if isinstance(carrier, esdl.Commodity):
                        if isinstance(carrier, esdl.ElectricityCommodity):
                            carrier_info['voltage'] = carrier.voltage
                        if isinstance(carrier, esdl.GasCommodity):
                            carrier_info['pressure'] = carrier.pressure
                        if isinstance(carrier, esdl.HeatCommodity):
                            carrier_info['supplyTemperature'] = carrier.supplyTemperature
                            carrier_info['returnTemperature'] = carrier.returnTemperature

                    if isinstance(carrier, esdl.EnergyCarrier):
                        carrier_info['energyContent'] = carrier.energyContent
                        carrier_info['emission'] = carrier.emission
                        carrier_info['energyCarrierType'] = carrier.energyCarrierType.name #ENUM
                        carrier_info['stateOfMatter'] = carrier.stateOfMatter.name #ENUM

                    # carrier_list.append({carrier.id: carrier_info})
                    carrier_list.append(carrier_info)
    return carrier_list


def get_asset_capability_type(asset):
    if isinstance(asset, esdl.Producer): return 'Producer'
    if isinstance(asset, esdl.Consumer): return 'Consumer'
    if isinstance(asset, esdl.Storage): return 'Storage'
    if isinstance(asset, esdl.Transport): return 'Transport'
    if isinstance(asset, esdl.Conversion): return 'Conversion'
    return 'none'

def get_capabilities_list():
    capabilities = dict()
    capabilities['Producer'] = get_capability_list(esdl.Producer)
    capabilities['Consumer'] = get_capability_list(esdl.Consumer)
    capabilities['Storage'] = get_capability_list(esdl.Storage)
    capabilities['Transport'] = get_capability_list(esdl.Transport)
    capabilities['Conversion'] = get_capability_list(esdl.Conversion)
    return capabilities


def get_capability_list(capability=esdl.Producer):
    """Returns a list of all subtypes of the specified capability.
    Used to get a list of e.g. all producers in ESDL
    The list is automatically generated based on the ESDL meta model"""
    subtype_list = list()
    for eclassifier in esdl.eClass.eClassifiers:
        if isinstance(eclassifier, EClass):
            if capability.eClass in eclassifier.eAllSuperTypes() and not eclassifier.abstract:
                subtype_list.append(eclassifier.name)
    return subtype_list







    # end