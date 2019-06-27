from esdl import esdl


class ESDLAsset:

    # ---------------------------------------------------------------------------------------------------------------------
    #  Functions to find assets in, remove assets from and add assets to areas and buildings
    # ---------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def find_area(area, area_id):
        if area.id == area_id: return area
        for a in area.area:
            ar = ESDLAsset.find_area(a, area_id)
            if ar:
                return ar
        return None

    @staticmethod
    def find_asset_in_building(building, asset_id):
        for ass in building.asset:
            if ass.id == asset_id:
                return ass
            if isinstance(ass, esdl.AbstractBuilding):
                asset = ESDLAsset.find_asset_in_building(ass, asset_id)
                if asset:
                    return asset
        return None

    @staticmethod
    def find_asset(area, asset_id):
        for ass in area.asset:
            if ass.id == asset_id:
                return ass
            if isinstance(ass, esdl.AbstractBuilding):
                asset = ESDLAsset.find_asset_in_building(ass, asset_id)
                if asset:
                    return asset

        for subarea in area.area:
            asset = ESDLAsset.find_asset(subarea, asset_id)
            if asset:
                return asset

        return None

    @staticmethod
    def find_potential(area, pot_id):
        for pot in area.potential:
            if pot.id == pot_id:
                return pot

        for subarea in area.area:
            pot = ESDLAsset.find_potential(subarea, pot_id)
            if pot:
                return pot

        return None

    @staticmethod
    def find_asset_in_building_and_container(building, asset_id):
        for ass in building.asset:
            if ass.id == asset_id:
                return ass, building
            if isinstance(ass, esdl.AbstractBuilding):
                asset, build = ESDLAsset.find_asset_in_building_and_container(ass, asset_id)
                if asset:
                    return asset, build
        return None

    @staticmethod
    def find_asset_and_container(area, asset_id):
        for ass in area.asset:
            if ass.id == asset_id:
                return ass, area
            if isinstance(ass, esdl.AbstractBuilding):
                asset, ar = ESDLAsset.find_asset_in_building_and_container(ass, asset_id)
                if asset:
                    return asset, ar

        for subarea in area.area:
            asset, ar = ESDLAsset.find_asset_and_container(subarea, asset_id)
            if asset:
                return asset, ar

        return None

    @staticmethod
    def add_asset_to_area(es, asset, area_id):
        # find area with area_id
        instance = es.instance[0]
        area = instance.area
        ar = ESDLAsset.find_area(area, area_id)

        if ar:
            ar.add_asset_with_type(asset)
            return 1
        else:
            return 0

    @staticmethod
    def add_asset_to_building(es, asset, building_id):
        # find area with area_id
        instance = es.instance[0]
        area = instance.area
        ar = ESDLAsset.find_asset(area, building_id)

        if ar:
            ar.add_asset_with_type(asset)
            return 1
        else:
            return 0

    @staticmethod
    def remove_object_from_building(building, object_id):
        for ass in building.asset:
            if ass.id == object_id:
                for p in ass.port:
                    _remove_port_references(p)
                building.asset.remove(ass)
                print('Asset with id ' + object_id + ' removed from building with id: ', + building.get_id())

    @staticmethod
    def recursively_remove_object_from_area(area, object_id):
        for ass in area.asset:
            if ass.id == object_id:
                for p in ass.port:
                    _remove_port_references(p)
                area.asset.remove(ass)
                print('Asset with id ' + object_id + ' removed from area with id: ' + area.get_id())
            if isinstance(ass, esdl.AggregatedBuilding) or isinstance(ass, esdl.Building):
                _remove_object_from_building(ass, object_id)
        for pot in area.potential:
            if pot.id == object_id:
                area.potential.remove(pot)
                print('Potential with id ' + object_id + ' removed from area with id: ' + area.get_id())
        for sub_area in area.area:
            ESDLAsset.recursively_remove_object_from_area(sub_area, object_id)

    @staticmethod
    def remove_object_from_energysystem(es, object_id):
        # find area with area_id
        instance = es.instance[0]
        area = instance.area
        ESDLAsset.recursively_remove_object_from_area(area, object_id)

    @staticmethod
    def get_asset_capability_type(asset):
        if isinstance(asset, esdl.Producer): return 'Producer'
        if isinstance(asset, esdl.Consumer): return 'Consumer'
        if isinstance(asset, esdl.Storage): return 'Storage'
        if isinstance(asset, esdl.Transport): return 'Transport'
        if isinstance(asset, esdl.Conversion): return 'Conversion'
        return 'none'

    @staticmethod
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
                            carrier_info['energyCarrierType'] = carrier.energyCarrierType
                            carrier_info['stateOfMatter'] = carrier.stateOfMatter

                        # carrier_list.append({carrier.id: carrier_info})
                        carrier_list.append(carrier_info)

        return carrier_list



