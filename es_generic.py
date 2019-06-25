from model import esdl_sup as esdl


def get_carrier_list(es):
    carrier_list = []
    esi = es.get_energySystemInformation()
    if esi:
        ecs = esi.get_carriers()
        if ecs:
            ec = ecs.get_carrier()

            if ec:
                for carrier in ec:
                    carrier_info = {
                        'type': type(carrier).__name__,
                        'id': carrier.get_id(),
                        'name': carrier.get_name(),
                    }
                    if isinstance(carrier, esdl.Commodity):
                        if isinstance(carrier, esdl.ElectricityCommodity):
                            carrier_info['voltage'] = carrier.get_voltage()
                        if isinstance(carrier, esdl.GasCommodity):
                            carrier_info['pressure'] = carrier.get_pressure()
                        if isinstance(carrier, esdl.HeatCommodity):
                            carrier_info['supplyTemperature'] = carrier.get_supplyTemperature()
                            carrier_info['returnTemperature'] = carrier.get_returnTemperature()

                    if isinstance(carrier, esdl.EnergyCarrier):
                        carrier_info['energyContent'] = carrier.get_energyContent()
                        carrier_info['emission'] = carrier.get_emission()
                        carrier_info['energyCarrierType'] = carrier.get_energyCarrierType()
                        carrier_info['stateOfMatter'] = carrier.get_stateOfMatter()

                    # carrier_list.append({carrier.get_id(): carrier_info})
                    carrier_list.append(carrier_info)

    return carrier_list
