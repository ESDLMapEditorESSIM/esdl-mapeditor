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
import uuid


def find_area(area, area_id):
    if area.id == area_id: return area
    for a in area.area:
        ar = find_area(a, area_id)
        if ar:
            return ar
    return None


def add_area_to_area(es, new_area, area_id):
    # find area with area_id
    instance = es.instance[0]
    area = instance.area
    ar = find_area(area, area_id)

    if ar:
        ar.area.append(new_area)
        return 1
    else:
        return 0


def remove_area(area, area_id):
    for a in set(area.area):
        if a.id == area_id:
            area.area.remove(a)
            return 1
        else:
            result = remove_area(a, area_id)
            if result:
                return 1
    return 0


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
                        carrier_info['energyCarrierType'] = carrier.energyCarrierType.__str__() #ENUM
                        carrier_info['stateOfMatter'] = carrier.stateOfMatter.__str__() #ENUM

                    # carrier_list.append({carrier.id: carrier_info})
                    carrier_list.append(carrier_info)
    return carrier_list


def get_sector_list(es):
    sector_list = []
    esi = es.energySystemInformation
    if esi:
        sectors = esi.sectors
        if sectors:
            sector = sectors.sector

            if sector:
                for s in sector:
                    sector_info = { 'id': s.id, 'name': s.name, 'descr': s.description, 'code': s.code }
                    sector_list.append(sector_info)

    return sector_list


def add_sector(es, sector_name, sector_code, sector_descr):
    esi = es.energySystemInformation
    if not esi:
        esi = esdl.EnergySystemInformation(id=str(uuid.uuid4()))
        es.energySystemInformation = esi
    sectors = esi.sectors
    if not sectors:
        sectors = esdl.Sectors(id=str(uuid.uuid4()))
        esi.sectors = sectors

    sector = sectors.sector
    sector_info = esdl.Sector()
    sector_info.id = str(uuid.uuid4())
    sector_info.name = sector_name
    sector_info.code = sector_code
    sector_info.description = sector_descr
    sector.append(sector_info)


def remove_sector(es, sector_id):
    esi = es.energySystemInformation
    if esi:
        sectors = esi.sectors
        if sectors:
            sector = sectors.sector
            if sector:
                for s in set(sector):
                    if s.id == sector_id:
                        sector.remove(s)


def process_area_KPIs(area):
    kpi_list = []
    kpis = area.KPIs
    if kpis:
        for area_kpi in kpis.kpi:
            kpi = {}
            kpi['id'] = area_kpi.id
            kpi['name'] = area_kpi.name

            sub_kpi = dict()
            sub_kpi['unit'] = 'N/A'
            sub_kpi['name'] = area_kpi.name

            if isinstance(area_kpi, esdl.DistributionKPI):
                sub_kpi['type'] = 'Distribution'

                distribution = area_kpi.distribution
                parts = []
                if isinstance(distribution, esdl.FromToDistribution):
                    for from_to_item in distribution.fromToItem:
                        parts.append({
                            'from': from_to_item.start,
                            'to': from_to_item.to,
                            'value': from_to_item.value
                        })
                if isinstance(distribution, esdl.StringLabelDistribution):
                    for string_item in distribution.stringItem:
                        parts.append({
                            'label': string_item.label,
                            'value': string_item.value
                        })
                sub_kpi['distribution'] = parts
            else:
                sub_kpi['value'] = area_kpi.value
                # TODO: Support for QuantityAndUnits

                if isinstance(area_kpi, esdl.IntKPI):
                    sub_kpi['type'] = 'Int'
                if isinstance(area_kpi, esdl.DoubleKPI):
                    sub_kpi['type'] = 'Double'
                if isinstance(area_kpi, esdl.StringKPI):
                    sub_kpi['type'] = 'String'

                targets = []
                if area_kpi.target:
                    for target in area_kpi.target:
                        targets.append({"year": target.year, "value": target.value})
                sub_kpi['targets'] = targets

            kpi['sub_kpi'] = [sub_kpi]
            kpi_list.append(kpi)

    return kpi_list
