import base64

from esdl import esdl


def all_buildings_from_area(area: esdl.Area) -> [esdl.Building]:
    buildings = []
    for content in area.eContents:
        if isinstance(content, esdl.Area):
            buildings += all_buildings_from_area(content)
        if isinstance(content, esdl.AbstractBuilding):
            buildings.append(content)
    return buildings


def all_buildings(instance: esdl.Instance) -> [esdl.Building]:
    return all_buildings_from_area(instance.area)


def all_energy_assets_from_building(building: esdl.Building) -> [esdl.EnergyAsset]:
    energy_assets = []
    for content in building.eContents:
        if isinstance(content, esdl.EnergyAsset):
            energy_assets.append(content)
    return energy_assets


def all_energy_assets_from_area(area: esdl.Area):
    energy_assets = []
    for content in area.eContents:
        if isinstance(content, esdl.EnergyAsset):
            energy_assets.append(content)
        elif isinstance(content, esdl.Building):
            energy_assets += all_energy_assets_from_building(content)
        elif isinstance(content, esdl.AggregatedBuilding):
            energy_assets += all_energy_assets_from_building(content)
        else:
            raise NotImplementedError(f"content: {type(content)}, not yet supported")
    return energy_assets


def all_energy_assets(instance: esdl.Instance) -> [esdl.Asset]:
    return all_energy_assets_from_area(instance.area)



#
#
# def remove_building(instance: esdl.Instance, building: esdl.AbstractBuilding):
#     area: esdl.Area = instance.area
#     area.asset.remove(building)
#
#
# def encode64_string():
#     with open('examples/single_value.esdl') as f:
#         content = f.read()
#         content_base64 = base64.b64encode(content.encode('utf-8'))
#     with open('examples/outputbase64', "wb") as f:
#         f.write(content_base64)