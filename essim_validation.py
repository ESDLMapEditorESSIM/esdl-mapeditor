from model import esdl_sup as esdl


def validate_ESSIM_asset(asset, results):
    asset_has_marginal_costs = False
    asset_has_profile = False
    asset_id = asset.get_id()
    asset_name = asset.get_name()
    if not asset_name:
        asset_name = asset_id

    if not asset_id:
        asset_id = 'NO_ASSET_ID'
        results.append('WARNING: Asset of type ' + type(asset).__name__ + ' has no id')

    port = asset.get_port()
    if port:
        for p in port:
            port_id = p.get_id()
            if not port_id:
                port_id = 'NO_PORT_ID'
                results.append('ERROR: Port of asset ' + asset_name + 'has no id')

            conn_to = p.get_connectedTo()
            if not conn_to:
                results.append('ERROR: Port ' + port_id + ' of asset ' + asset_name + 'is not connected')

            carr = p.get_carrier()
            if not carr:
                results.append('ERROR: Port' + port_id + ' of asset ' + asset_name + 'has no carrier')

            profile = p.get_profile()
            if profile:
                if asset_has_profile:
                    results.append('ERROR: asset ' + asset_name + ' has more than one profile')
                else:
                    asset_has_profile = True
    else:
        results.append('ERROR: Asset ' + asset_name + ' has no ports')

    ci = asset.get_costInformation()
    if ci:
        mc = ci.get_marginalCosts()
        if mc:
            value = mc.get_value()
            if value < 0 or value > 1:
                results.append('WARNING: Marginal costs for asset ' + asset_name + ' not between 0 and 1')
            asset_has_marginal_costs = True

    if isinstance(asset, esdl.Producer):
        # Producer must have a power and marginal costs specified or a profile
        if not asset_has_profile:
            power = asset.get_power()
            if power:
                if power == 0:
                    results.append('ERROR: Producer ' + asset_name + ' has power of 0')
            else:
                results.append('ERROR: Producer ' + asset_name + ' has no power specified')
            if not asset_has_marginal_costs:
                results.append('ERROR: Producer ' + asset_name + ' has no marginal costs specified')

        else:
            if asset_has_marginal_costs:
                results.append('ERROR: Producer ' + asset_name + ' has both a profile and marginal costs specified')

    if isinstance(asset, esdl.Consumer):
        if not asset_has_profile:
            power = asset.get_power()
            if power:
                if power == 0:
                    results.append('ERROR: Consumer ' + asset_name + ' has power of 0')
            else:
                results.append('WARNING: Consumer ' + asset_name + ' has no power specified')
        else:
            if asset_has_marginal_costs:
                results.append('ERROR: Consumer ' + asset_name + ' has both a profile and marginal costs specified')

    if isinstance(asset, esdl.Conversion):
        power = asset.get_power()  # TODO: what is result if no power specified?
        if power:
            if power == 0:
                results.append('ERROR: Conversion ' + asset_name + ' has power of 0')
        else:
            results.append('WARNING: Conversion ' + asset_name + ' has no power specified')

        eff = asset.get_efficiency()  # TODO: what is result if no efficiency is specified?
        if eff:
            if eff == 0:
                results.append('ERROR: Conversion ' + asset_name + ' has efficiency of 0')
        else:
            results.append('WARNING: Conversion ' + asset_name + ' has no efficiency specified')

        cs = asset.get_controlStrategy()
        if cs:
            if isinstance(cs, esdl.DrivenByDemand):
                port = cs.get_inPort()
                if not port:
                    results.append('ERROR: Conversion ' + asset_name + ' has a DrivenByDemand strategy without an InPort')
            if isinstance(cs, esdl.DrivenBySupply):
                port = cs.get_inPort()
                if not port:
                    results.append('ERROR: Conversion ' + asset_name + ' has a DrivenBySupply strategy without an OutPort')
            if isinstance(cs, esdl.DrivenByProfile):
                prof = cs.get_profile()
                if not prof:
                    results.append('ERROR: Conversion ' + asset_name + ' has a DrivenByProfile strategy without a profile')
            if isinstance(cs, esdl.StorageStrategy):
                results.append('ERROR: Conversion ' + asset_name + ' has a StorageStrategy attached to it')
            if isinstance(cs, esdl.CurtailmentStrategy):
                results.append('ERROR: CurtailmentStrategy not supported yet')
        else:
            results.append('WARNING: Conversion ' + asset_name + ' has no control strategy')


def validate_ESSIM_building(building, results):
    for asset in building.get_asset():
        if isinstance(asset, esdl.AbstractBuilding):    # To validate BuildingUnits
            validate_ESSIM_building(asset, results)
        else:
            validate_ESSIM_asset(asset, results)


def validate_ESSIM_area(area, results):
    for asset in area.get_asset():
        if isinstance(asset, esdl.AbstractBuilding):
            validate_ESSIM_building(asset, results)
        else:
            validate_ESSIM_asset(asset, results)

    for ar in area.get_area():
        validate_ESSIM_area(ar, results)


def validate_ESSIM(es):
    results = []

    esi = es.get_energySystemInformation()
    if esi:
        carrs = esi.get_carriers()
        if carrs:
            if not carrs.get_carrier():
                results.append('ERROR: No carriers or commodities defined')
        else:
            results.append('ERROR: No carriers or commodities defined')

    control_strategy_found = False
    serv = es.get_services()
    if serv:
        for s in serv.get_service():
            if isinstance(s, esdl.ControlStrategy):
                control_strategy_found = True

    if not control_strategy_found:
        results.append('WARNING: No control strategies found')

    instance = es.get_instance()
    if instance:
        area = instance[0].get_area()
        if area:
            validate_ESSIM_area(area, results)
        else:
            results.append('ERROR: No top level area in first instance')
    else:
        results.append('ERROR: No instance in energysystem')

    return results