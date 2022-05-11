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
from pathlib import Path

import esdl
import pandas as pd
from influxdb import InfluxDBClient

# Helper function
from influxdb.resultset import ResultSet


def write_excel_from_df(excel_name: Path, df: pd.DataFrame):
    if df.empty:
        print(f"the dataframe for: {excel_name} is empty, therefore not storing")
    else:
        print(f"writing excel: {excel_name}")
        # print(df.head)
        df.to_excel(excel_name, index=False)
        print(f"finished writing excel: {excel_name}")


def query_influx_db(
    influx_client: InfluxDBClient,
    id_to_energy_asset: {str: esdl.EnergyAsset},
    query: str,
):
    result: ResultSet = influx_client.query(query)
    df = pd.DataFrame()
    first_time = True
    for info, values in result.items():
        prop = info[1]
        energy_asset: esdl.EnergyAsset = id_to_energy_asset[prop["assetId"]]
        local_df = pd.DataFrame(values)
        column_name = f'{energy_asset.name}:{prop["assetClass"]}:{prop["carrierName"]}'
        if energy_asset.containingBuilding:
            column_name += f":{energy_asset.containingBuilding.originalIdInSource}"
        else:
            column_name += ":Bedrijventerrein"
        local_df.rename(columns={"allocationEnergy": column_name}, inplace=True)
        if not first_time:
            local_df.drop("time", axis=1, inplace=True)
        df = pd.concat([df, local_df], axis=1)
        first_time = False
    return df


def export_consumption(
    influx_client: InfluxDBClient,
    simulation_run: str,
    id_to_energy_asset: {str: esdl.EnergyAsset},
    network: str,
):
    query = f"SELECT \"allocationEnergy\" FROM \"{network}\" WHERE (\"simulationRun\" = '{simulation_run}' AND \"capability\" <> 'Transport') AND time >= 1546297200000ms and time <= 1577833200000ms GROUP BY \"assetId\", \"assetClass\", \"carrierName\""
    return query_influx_db(influx_client, id_to_energy_asset, query)


def export_consumptions(
    influx_client: InfluxDBClient,
    simulation_run: str,
    id_to_energy_asset: {str: esdl.EnergyAsset},
    networks: [str],
) -> dict[str, pd.DataFrame]:
    result = dict()
    for network in networks:
        df = export_consumption(
            influx_client, simulation_run, id_to_energy_asset, network
        )
        excel_name = f"{network}-Input-Output_J.xlsx"
        result[excel_name] = df
    return result


def export_emissions(
    influx_client: InfluxDBClient,
    simulation_run: str,
    id_to_energy_asset: {str: esdl.EnergyAsset},
    es_name: str,
) -> dict[str, pd.DataFrame]:
    query = f"SELECT \"emission\"  / 1000 FROM /.*/ WHERE (\"simulationRun\" = '{simulation_run}' AND \"capability\" = 'Producer') AND time >= 1546297200000ms and time <= 1577833200000ms GROUP BY \"assetId\", \"assetClass\", \"carrierName\""
    df = query_influx_db(influx_client, id_to_energy_asset, query)
    excel_name = f"{es_name}-emissions_ton-CO2.xlsx"
    return {excel_name: df}


def export_transport(
    influx_client: InfluxDBClient,
    simulation_run: str,
    id_to_energy_asset: {str: esdl.EnergyAsset},
    network: str,
):
    query = f"SELECT \"allocationEnergy\" FROM \"{network}\" WHERE (\"simulationRun\" = '{simulation_run}' AND \"capability\" = 'Transport') AND time >= 1546297200000ms and time <= 1577833200000ms GROUP BY \"assetId\", \"assetClass\", \"carrierName\""
    return query_influx_db(influx_client, id_to_energy_asset, query)


def export_transports(
    influx_client: InfluxDBClient,
    simulation_run: str,
    id_to_energy_asset: {str: esdl.EnergyAsset},
    networks: [str],
) -> dict[str, pd.DataFrame]:
    result = dict()
    for network in networks:
        df = export_transport(
            influx_client, simulation_run, id_to_energy_asset, network
        )
        excel_name = f"{network} Transport flows_J.xlsx"
        result[excel_name] = df
    return result


def export_energy_system_simulation(
    influx_client: InfluxDBClient,
    essim_id: str,
    es: esdl.EnergySystem,
    networks: [str],
) -> dict[str, pd.DataFrame]:
    if len(es.instance) != 1:
        raise Exception(
            "there are {} instances in this ESDL except 1".format(len(es.instance))
        )
    instance: esdl.Instance = es.instance[0]

    id_to_energy_asset = {ea.id: ea for ea in all_energy_assets(instance)}

    transport_results = export_transports(
        influx_client, essim_id, id_to_energy_asset, networks
    )
    consumption_results = export_consumptions(
        influx_client, essim_id, id_to_energy_asset, networks
    )
    emissions_results = export_emissions(
        influx_client, essim_id, id_to_energy_asset, es.name
    )
    return dict(**transport_results, **consumption_results, **emissions_results)


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
        else:
            raise NotImplementedError(f"content: {type(content)}, not yet supported")
    return energy_assets


def all_energy_assets(instance: esdl.Instance) -> [esdl.Asset]:
    return all_energy_assets_from_area(instance.area)
