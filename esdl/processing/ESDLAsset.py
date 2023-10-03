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

from esdl import esdl
from pyecore.ecore import EClass
from pyecore.resources import ResourceSet
from esdl.esdl_handler import StringURI
from esdl.processing import ESDLEnergySystem
from extensions.session_manager import get_handler, get_session


# ---------------------------------------------------------------------------------------------------------------------
#  Functions to find assets in, remove assets from and add assets to areas and buildings
# ---------------------------------------------------------------------------------------------------------------------
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
    print(f"checking area {area.name}")
    for ass in area.asset:
        print(f"checking asset {ass.eClass.name}")
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

    return None, None


def add_object_to_area(es, obj, area_id):
    # find area with area_id
    instance = es.instance[0]
    area = instance.area
    ar = ESDLEnergySystem.find_area(area, area_id)

    if ar:
        if isinstance(obj, esdl.Asset):
            ar.asset.append(obj)
        elif isinstance(obj, esdl.Potential):
            ar.potential.append(obj)
        else:
            print("Serious error: Cannot add anything other than an Asset or a Potential to an area")
        return 1
    else:
        return 0


def add_object_to_building(es, obj, building_id):
    # find area with area_id
    instance = es.instance[0]
    area = instance.area
    ar = find_asset(area, building_id)

    if ar:
        if isinstance(obj, esdl.Asset):
            ar.asset.append(obj)
        elif isinstance(obj, esdl.Potential):
            ar.potential.append(obj)
        else:
            print("Serious error: Cannot add anything other than an Asset or a Potential to a building")
        return 1
    else:
        return 0


def remove_object_from_building(building, object_id):
    for ass in set(building.asset):
        if ass.id == object_id:
            # Remove port connections for EnergyAssets (and not for buildingunits)
            if isinstance(ass, esdl.EnergyAsset):
                for p in ass.port:
                    p.connectedTo.clear()

            building.asset.remove(ass)
            print('Asset with id ' + object_id + ' removed from building with id: ', + building.id)


def recursively_remove_object_from_area(area, object_id):
    for ass in set(area.asset):
        if ass.id == object_id:
            # Only remove port connections for EnergyAssets (and not for buildings)
            if isinstance(ass, esdl.EnergyAsset):
                for p in ass.port:
                    p.connectedTo.clear()
            area.asset.remove(ass)
            print('Asset with id ' + object_id + ' removed from area with id: ' + area.id)
        if isinstance(ass, esdl.AggregatedBuilding) or isinstance(ass, esdl.Building):
            remove_object_from_building(ass, object_id)
    for pot in set(area.potential):
        if pot.id == object_id:
            area.potential.remove(pot)
            print('Potential with id ' + object_id + ' removed from area with id: ' + area.id)
    for sub_area in area.area:
        recursively_remove_object_from_area(sub_area, object_id)


# todo: move to EnergySystemHandler
def remove_object_from_energysystem(es, object_id):
    esh = get_handler()
    active_es_id = get_session('active_es_id')
    obj = esh.get_by_id(active_es_id, object_id)
    obj.delete(recursive=True)


def get_asset_capability_type(asset):
    if isinstance(asset, esdl.Producer): return 'Producer'
    if isinstance(asset, esdl.Consumer): return 'Consumer'
    if isinstance(asset, esdl.Storage): return 'Storage'
    if isinstance(asset, esdl.Transport): return 'Transport'
    if isinstance(asset, esdl.Conversion): return 'Conversion'
    return 'none'


# creates a list of capabilities and a list of potentials
def get_objects_list():
    capabilities = dict()
    capabilities['Producer'] = get_capability_list(esdl.Producer)
    capabilities['Consumer'] = get_capability_list(esdl.Consumer)
    capabilities['Storage'] = get_capability_list(esdl.Storage)
    capabilities['Transport'] = get_capability_list(esdl.Transport)
    capabilities['Conversion'] = get_capability_list(esdl.Conversion)

    potentials = get_potentials_list()

    return {'capabilities': capabilities, 'potentials': potentials}


def get_capability_list(capability=esdl.Producer):
    """Returns a list of all subtypes of the specified capability.
    Used to get a list of e.g. all producers in ESDL
    The list is automatically generated based on the ESDL meta model"""
    subtype_list = list()
    for eclassifier in esdl.eClass.eClassifiers:
        if isinstance(eclassifier, EClass):
            if capability.eClass in eclassifier.eAllSuperTypes() and not eclassifier.abstract:
                subtype_list.append(eclassifier.name)
    subtype_list.sort()
    return subtype_list


def get_potentials_list():
    """Returns a list of all potentials.
    The list is automatically generated based on the ESDL meta model"""
    subtype_list = list()
    for eclassifier in esdl.eClass.eClassifiers:
        if isinstance(eclassifier, EClass):
            if esdl.Potential.eClass in eclassifier.eAllSuperTypes() and not eclassifier.abstract:
                subtype_list.append(eclassifier.name)
    subtype_list.sort()
    return subtype_list



def load_asset_from_string(esdl_string):
    uri = StringURI('from_string.esdl', esdl_string)
    # self._new_resource_set()
    rset = ResourceSet()
    resource = rset.create_resource(uri)
    resource.load()
    esdl_instance = resource.contents[0]
    return esdl_instance


def add_profile_to_port(port, profile):
    profile_list = port.profile

    for i in range(0,len(profile_list)):
        p = profile_list[i]
        # TODO: Support Quantity and Unit Type
        if p.profileType == profile.profileType:
            profile_list[i] = profile
            return

    profile_list.append(profile)


def remove_profile_from_port(port, profile_id):
    esh = get_handler()
    active_es_id = get_session('active_es_id')

    profile_list = port.profile

    for profile in set(profile_list):
        if profile.id == profile_id:
            profile_list.remove(profile)
            esh.remove_object_from_dict(active_es_id, profile, True)
