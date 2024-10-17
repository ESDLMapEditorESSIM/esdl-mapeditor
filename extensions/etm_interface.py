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
import numpy as np
from flask import Flask
from flask_socketio import SocketIO, emit
import requests
import csv
import codecs
import json
import re
from uuid import uuid4

from esdl import esdl
from esdl.processing import ESDLAsset
from esdl.processing.ESDLQuantityAndUnits import build_qau_from_unit_string
from esdl.profiles.influxdbprofilemanager import InfluxDBProfileManager
from esdl.undo_wrapper import undo_record_changes
from esdl.units.conversion import convert_to_unit, ENERGY_IN_PJ
from extensions.session_manager import get_project_manager, get_session
from extensions.settings_storage import SettingsStorage

import src.log as log
from src.edr_client import EDRClient
from src.process_es_area_bld import get_area_id_from_mapeditor_id, find_boundaries_in_ESDL
from utils.utils import timed

logger = log.get_logger(__name__)

ETM_INTERFACE_SYSTEM_CONFIG = 'ETM_INTERFACE_SYSTEM_CONFIG'
ETM_INTERFACE_DEFAULT_SYSTEM_CONFIG = {
    # 'etm_base_url': 'https://engine.energytransitionmodel.com/api/v3',
    'etm_base_url': 'https://beta.energytransitionmodel.com/api/v3',
    'etm_municipalities_file': 'data/ETM_municipalities.csv'
}

# Global profile information about clusters, so information can be retrieved once and reused between calls
global_clusters = {
    "Landbouw": {"profile_ref": "/edr/Public/Profiles/Ruimte voor Energie/RvE_profiles_test - Landbouw.edd", "profile_data": None},
    "Utiliteiten": {"profile_ref": "/edr/Public/Profiles/Ruimte voor Energie/RvE_profiles_test - Utiliteiten.edd", "profile_data": None},
    "Industrie": {"profile_ref": "/edr/Public/Profiles/Ruimte voor Energie/RvE_profiles_test - Industrie.edd", "profile_data": None},
    "Huishoudens": {"profile_ref": "/edr/Public/Profiles/Ruimte voor Energie/RvE_profiles_test - Huishoudens.edd", "profile_data": None},
    "Mobiliteit": {"profile_ref": "/edr/Public/Profiles/Ruimte voor Energie/RvE_profiles_test - Mobiliteit.edd", "profile_data": None},
    "Wind": {"profile_ref": "/edr/Public/Profiles/Ruimte voor Energie/RvE_profiles_test - Wind.edd", "profile_data": None},
    "Zon": {"profile_ref": "/edr/Public/Profiles/Ruimte voor Energie/RvE_profiles_test - Zon.edd", "profile_data": None},
}


class ETMInterface:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.etm_municipalities = dict()
        self.municipalities_bld_info = dict()

        self.plugin_settings = self.get_settings()
        self.register()

        self.read_etm_municipalities()
        self.read_gemeente_pand_info()

    def register(self):
        logger.info('Registering ETMInterface extension')

        @self.socketio.on('etm_get_sankey_data', namespace='/esdl')
        @undo_record_changes(label="Add ETM Sankey data")
        def etm_get_sankey_data(area_id):
            # area_id could have "(3 of 5)" in it, if the Area clicked is the third polygon af a total of five polygons
            area_id = get_area_id_from_mapeditor_id(area_id)
            active_es_id = get_session('active_es_id')
            pm = get_project_manager()
            area = pm.get_by_id(active_es_id, area_id)

            # Get profiles for all clusters from the EDR if not done already
            emit("update-etm-query-log", f"Loading EDR cluster profiles...")
            self.get_edr_profiles()

            emit("update-etm-query-log", f"Requested ETM Sankey data for {area.name} ({area.id})")
            if area.scope is not esdl.AreaScopeEnum.MUNICIPALITY:
                area_with_scope_municipality_found = False
                at_least_one_etm_query_succeeded = False
                for logical_group in area.area:
                    if logical_group.logicalGroup:
                        for sub_area in logical_group.area:
                            if sub_area.scope is esdl.AreaScopeEnum.MUNICIPALITY:
                                if not area_with_scope_municipality_found:
                                    # Only first time
                                    emit("update-etm-query-log", f"area {area.name} contains sub areas of scope MUNICIPALITY")
                                area_with_scope_municipality_found = True

                                emit("update-etm-query-log", f"Query ETM for area {sub_area.name} ({sub_area.id})")
                                etm_sankey_data = self.request_sankey_info_municipality(sub_area.id)
                                if etm_sankey_data:
                                    at_least_one_etm_query_succeeded = True
                                    self.process_data_and_add_to_area(pm, active_es_id, sub_area, etm_sankey_data)
                                else:
                                    emit("update-etm-query-log", f"- ETM scenario for {sub_area.name} could not be created")
                            else:
                                continue

                if area_with_scope_municipality_found:
                    if at_least_one_etm_query_succeeded:
                        emit("update-etm-query-log", "Done")
                        return True
                    else:
                        emit("update-etm-query-log", "No ETM scenarios could be created for any of the sub areas with scope MUNICIPALITY")
                        return False
                else:
                    emit("update-etm-query-log", f"area {area.name} doesn't contain sub areas of scope MUNICIPALITY")
                    return False
            else:
                etm_sankey_data = self.request_sankey_info_municipality(area_id)
                if etm_sankey_data:
                    self.process_data_and_add_to_area(pm, active_es_id, area, etm_sankey_data)
                    emit("update-etm-query-log", "Done")
                    return True
                else:
                    emit("update-etm-query-log", f"- ETM scenario for {area.name} could not be created")
                    return False

        @self.socketio.on('etm_update_sankey_data', namespace='/esdl')
        @undo_record_changes(label="Update ETM Sankey data")
        def etm_update_sankey_data(area_id):
            # area_id could have "(3 of 5)" in it, if the Area clicked is the third polygon af a total of five polygons
            area_id = get_area_id_from_mapeditor_id(area_id)
            active_es_id = get_session('active_es_id')
            pm = get_project_manager()
            area = pm.get_by_id(active_es_id, area_id)

            # Get profiles for all clusters from the EDR if not done already
            emit("update-etm-query-log", f"Loading EDR cluster profiles...")
            self.get_edr_profiles()

            emit("update-etm-query-log", f"Updating ETM Sankey data for {area.name} ({area.id})")
            if area.scope is not esdl.AreaScopeEnum.MUNICIPALITY:
                area_with_scope_municipality_found = False
                for logical_group in area.area:
                    if logical_group.logicalGroup:
                        for sub_area in logical_group.area:
                            if sub_area.scope is esdl.AreaScopeEnum.MUNICIPALITY:
                                emit("update-etm-query-log", f"Recalculating KPIs for area {sub_area.name} ({sub_area.id})")
                                self.update_kpis_for_area(sub_area)
                            else:
                                continue
            else:
                emit("update-etm-query-log", f"Recalculating KPIs for area {area.name} ({area.id})")
                self.update_kpis_for_area(area)

            return True

        @self.socketio.on('etm_heat_transition_get_area_info', namespace='/esdl')
        def etm_heat_transition_get_area_info(area_id):
            # area_id could have "(3 of 5)" in it, if the Area clicked is the third polygon af a total of five polygons
            area_id = get_area_id_from_mapeditor_id(area_id)
            active_es_id = get_session('active_es_id')
            pm = get_project_manager()
            area = pm.get_by_id(active_es_id, area_id)

            # Get profiles for all clusters from the EDR if not done already
            self.get_edr_profiles()

            if area_id in self.municipalities_bld_info:
                info = self.municipalities_bld_info[area_id]
                return {
                    "name": area.name,
                    "info": info
                }
            else:
                return None

        @self.socketio.on('etm_heat_transition_apply', namespace='/esdl')
        def etm_heat_transition_apply(message):
            # area_id could have "(3 of 5)" in it, if the Area clicked is the third polygon af a total of five polygons
            area_id = get_area_id_from_mapeditor_id(message["area_id"])
            active_es_id = get_session('active_es_id')
            pm = get_project_manager()
            area = pm.get_by_id(active_es_id, area_id)

            etm_sankey = ETMSankeyToESDL(None)
            etm_sankey.apply_heat_transition(area, message["technology_info"])

    def get_settings(self):
        if self.settings_storage.has_system(ETM_INTERFACE_SYSTEM_CONFIG):
            etm_interface_plugin_settings = self.settings_storage.get_system(ETM_INTERFACE_SYSTEM_CONFIG)
        else:
            etm_interface_plugin_settings = ETM_INTERFACE_DEFAULT_SYSTEM_CONFIG
            self.settings_storage.set_system(ETM_INTERFACE_SYSTEM_CONFIG, etm_interface_plugin_settings)
        return etm_interface_plugin_settings

    def read_etm_municipalities(self):
        municipalities_file = self.plugin_settings['etm_municipalities_file']

        with codecs.open(municipalities_file, encoding='utf-8-sig') as csv_file:
            reader = csv.reader(csv_file, delimiter=';')
            for row in reader:
                self.etm_municipalities[row[0].split('_')[0]] = row[0]

        logger.debug(f"ETM plugin read {len(self.etm_municipalities)} municipalities from input file")

    def read_gemeente_pand_info(self):
        municipalities_bld_info_file = "data/gemeente_pand_info.csv"

        with codecs.open(municipalities_bld_info_file, encoding='utf-8-sig') as csv_file:
            reader = csv.DictReader(csv_file, delimiter=',')
            for row in reader:
                self.municipalities_bld_info[row['gm_code']] = row

        logger.debug(f"ETM plugin read {len(self.municipalities_bld_info)} municipalities from input file")

    @timed
    def request_sankey_info_municipality(self, municipality_code):
        if municipality_code not in self.etm_municipalities:
            return None
        else:
            session = requests.Session()
            post_data = {
                "scenario": {
                    "title": self.etm_municipalities[municipality_code],
                    "area_code": self.etm_municipalities[municipality_code],
                    "end_year": 2050
                }
            }
            response = session.post(self.plugin_settings["etm_base_url"] + "/scenarios", json=post_data, headers={'Connection': 'close'})

            if response.ok:
                scenario_id = response.json()['id']
                logger.info(f"Created scenario in ETM for {self.etm_municipalities[municipality_code]} with id {scenario_id}")

                scenario_url = response.json()["url"]
                sankey_url = scenario_url + "/sankey.csv"

                sankey_response = requests.get(sankey_url)
                text = codecs.iterdecode(sankey_response.iter_lines(), 'utf-8')
                reader = csv.DictReader(text, delimiter=',')

                etm_sankey_data = list()
                for row in reader:
                    etm_sankey_data.append(row)

                return etm_sankey_data
            else:
                logger.error(f"Could not create ETM scenario for {self.etm_municipalities[municipality_code]}")
                logger.error(f"Response code: {response.status_code}")
                return None

    @timed
    def process_data_and_add_to_area(self, pm, active_es_id, area, etm_sankey_data):
        es = pm.get_active_energy_system()

        etm_sankey = ETMSankeyToESDL(etm_sankey_data)
        etm_sankey.add_carriers_and_sectors(es)
        etm_sankey.add_info_to_area(area)
        etm_sankey.clear_area_logbook()

    def update_kpis_for_area(self, area):
        etm_sankey = ETMSankeyToESDL(None)
        etm_sankey.recalculate_kpis(area)

    def call_etm_interface_api(self, id):
        id = get_area_id_from_mapeditor_id(id)
        url = self.plugin_settings['etm_interface_api'].replace('<ID>', id)
        result = None

        try:
            logger.info("Querying URL "+url)
            r = requests.get(url)
            if r.status_code == 200:
                result = json.loads(r.text)
            else:
                logger.debug("ETML API returned status code: {}".format(r.status_code))
        except Exception as e:
            logger.debug("Error accessing ETM API: " + str(e))

        return result

    def get_edr_profiles(self):
        edr_client = EDRClient.get_instance()

        for cluster_name, cluster_info in global_clusters.items():
            if not cluster_info["profile_data"]:
                profile_esdl_str = edr_client.get_object_from_EDR(cluster_info["profile_ref"])
                profile_esdl = ESDLAsset.load_asset_from_string(profile_esdl_str)
                profile_mngr = InfluxDBProfileManager.create_esdl_influxdb_profile_manager(profile_esdl, use_ssl=True, verify_ssl=True)
                cluster_info["profile_data"] = [x[1] for x in profile_mngr.profile_data_list]


class ETMSankeyToESDL:

    def __init__(self, etm_data):
        self.etm_data = etm_data

        self.multiplier_mapping = {
            "J": esdl.MultiplierEnum.NONE,
            "k": esdl.MultiplierEnum.KILO,
            "M": esdl.MultiplierEnum.MEGA,
            "G": esdl.MultiplierEnum.GIGA,
            "T": esdl.MultiplierEnum.TERA,
            "P": esdl.MultiplierEnum.PETA,
        }

        # Note: Do not forget to add new assets to list of local_production_assets
        # if you add assets to the next mapping
        self.category_to_asset_type_mapping = {
            "Import": {"type": esdl.Import},
            "Export": {"type": esdl.Export},
            "Wind coastal": {"type": esdl.WindTurbine},
            "Wind inland": {"type": esdl.WindTurbine},
            "Wind offshore": {"type": esdl.WindTurbine},
            "Solar": {"type": esdl.PVInstallation},
            "Production": {"carrier_mapping": {
                "Geothermal": esdl.GeothermalSource,
                "Solar thermal": esdl.SolarCollector
            }}
        }

        # Check: not sure if all clusters will be used. For now only Wind and Zon
        self.local_production_assets = {
            "WindTurbine": {"total": 0.0, "cluster": "Wind", "carrier": "Electricity"},
            "PVInstallation": {"total": 0.0, "cluster": "Zon", "carrier": "Electricity"},
            "GeothermalSource": {"total": 0.0, "cluster": "Warmte"},
            "SolarCollector": {"total": 0.0, "cluster": "Warmte"},
        }

        self.carriers = {
            "Ammonia": {"id": "etm_carrier_ammonia", "name": "Ammonia", "carrier": None},
            "Biomass": {"id": "etm_carrier_biomass", "name": "Biomass", "carrier": None},
            "Coal": {"id": "etm_carrier_coal", "name": "Coal", "carrier": None},
            "Electricity": {"id": "etm_carrier_electricity", "name": "Electricity", "carrier": None},
            "Geothermal": {"id": "etm_carrier_geothermal", "name": "Geothermal", "carrier": None},
            "Hydrogen": {"id": "etm_carrier_h2", "name": "Hydrogen", "carrier": None},
            "Liquid hydrogen": {"id": "etm_carrier_liquid_h2", "name": "Liquid hydrogen", "carrier": None},
            "LOHC": {"id": "etm_carrier_lohc", "name": "LOHC", "carrier": None},
            "Methanol": {"id": "etm_carrier_methanol", "name": "Methanol", "carrier": None},
            "Natural gas": {"id": "etm_carrier_natural_gas", "name": "Natural gas", "carrier": None},
            "Non-biogenic waste": {"id": "etm_carrier_non_biogenic_waste", "name": "Non-biogenic waste", "carrier": None},
            "Not defined": {"id": "etm_carrier_not_defined", "name": "Not defined", "carrier": None},
            "Oil": {"id": "etm_carrier_oil", "name": "Oil", "carrier": None},
            "Solar thermal": {"id": "etm_carrier_solar_thermal", "name": "Solar thermal", "carrier": None},
            "Steam hot water": {"id": "etm_carrier_shw", "name": "Steam hot water", "carrier": None},
            "Uranium": {"id": "etm_carrier_uranium", "name": "Uranium", "carrier": None},
            "Waste mix": {"id": "etm_carrier_waste_mix", "name": "Waste mix", "carrier": None}
        }

        self.asset_to_carrier_mapping = {
            "ElectricityDemand": "Electricity",
            "PVInstallation": "Electricity",
            "PVPark": "Electricity",
            "EVChargingStation": "Electricity",
            "WindTurbine": "Electricity",
            "WindPark": "Electricity"
        }

        self.asset_to_sector_mapping = {
            "ElectricityDemand": {
                "Elektriciteitsvraag (gebouwgebonden)": {
                    "sector": "Households space heating and hot water",
                    "parent": esdl.AbstractBuilding,
                    "parent_type": esdl.BuildingTypeEnum.RESIDENTIAL
                },
                "Elektriciteitsvraag (apparaten)": {
                    "sector": "Households excl. space heating and hot water",
                    "parent": esdl.AbstractBuilding,
                    "parent_type": esdl.BuildingTypeEnum.RESIDENTIAL
                }
            },
            "EVChargingStation": {
                "Thuislaadpunten": {
                    "sector": "Households excl. space heating and hot water"
                },
                "Semi publiekelaadpunten": {
                    "sector": "National transport"
                },
                "Laadpunten parkeergarages": {
                    "sector": "National transport"
                },
            }
        }

        self.sectors = {
            "Agriculture": {"id": "etm_sector_agri", "name": "Agriculture", "cluster": "Landbouw", "sector": None},
            "Buildings excl. space heating": {"id": "etm_sector_buildings_excl_sh", "name": "Buildings excl. space heating", "cluster": "Utiliteiten", "sector": None},
            "Buildings space heating": {"id": "etm_sector_buildings_sh", "name": "Buildings space heating", "cluster": "Utiliteiten", "sector": None},
            "Energy": {"id": "etm_sector_energy", "name": "Energy", "cluster": "Overig", "sector": None},
            "Export": {"id": "etm_sector_export", "name": "Export", "cluster": "Export", "sector": None},
            "Feedstock": {"id": "etm_sector_feedstock", "name": "Feedstock", "cluster": "Industrie", "sector": None},
            "Households excl. space heating and hot water": {"id": "etm_sector_hh_excl_sph_hw", "name": "Households excl. space heating and hot water", "cluster": "Huishoudens", "sector": None},
            "Households space heating and hot water": {"id": "etm_sector_hh_sph_hw", "name": "Households space heating and hot water", "cluster": "Huishoudens", "sector": None},
            "Industry excl. ICT": {"id": "etm_sector_industry_excl_ict", "name": "Industry excl. ICT", "cluster": "Industrie", "sector": None},
            "Industry excl. ICT and power-to-heat": {"id": "etm_sector_industry_excl_ict_p2h", "name": "Industry excl. ICT and power-to-heat", "cluster": "Industrie", "sector": None},
            "Industry ICT": {"id": "etm_sector_industry_ict", "name": "Industry ICT", "cluster": "Industrie", "sector": None},
            "Industry power-to-heat": {"id": "etm_sector_industry_p2h", "name": "Industry power-to-heat", "cluster": "Industrie", "sector": None},
            "International transport": {"id": "etm_sector_int_transp", "name": "International transport", "cluster": "Mobiliteit", "sector": None},
            "National transport": {"id": "etm_sector_nat_transp", "name": "National transport", "cluster": "Mobiliteit", "sector": None},
            "Other": {"id": "etm_sector_other", "name": "Other", "cluster": "Overig", "sector": None},
        }

        self.profiles_last_updated = None

    def set_etm_data(self, etm_data):
        self.etm_data = etm_data

    def clear_area_logbook(self):
        for carr, carr_info in self.carriers.items():
            if "network" in carr_info:
                del carr_info["network"]

            if "final_demand" in carr_info:
                del carr_info["final_demand"]

            if "import" in carr_info:
                del carr_info["import"]

        for sect, sect_info in self.sectors.items():
            if "final_demand" in sect_info:
                del sect_info["final_demand"]

    ###################################################################################################################
    #   functions to create the ESDL from the ETM Sankey data
    ###################################################################################################################
    def create_qau(self, unit):
        return esdl.QuantityAndUnitType(
            id=str(uuid4()),
            description="ENERGY in " + unit,
            physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
            multiplier=self.multiplier_mapping[unit[0]],
            unit=esdl.UnitEnum.JOULE        # assume Joule for now
        )

    def create_carriers(self, es: esdl.EnergySystem):
        esi = es.energySystemInformation
        if not esi:
            esi = esdl.EnergySystemInformation(id=str(uuid4()))
            es.energySystemInformation = esi

        ec = esi.carriers
        if not ec:
            ec = esdl.Carriers(id=str(uuid4()))
            esi.carriers = ec

        for c in self.carriers:
            c_info = self.carriers[c]
            # Only add carrier if not done earlier already
            if not c_info["carrier"]:
                carr = esdl.EnergyCarrier(id=c_info["id"], name=c_info["name"])
                c_info["carrier"] = carr
                ec.carrier.append(carr)

    def create_sectors(self, es: esdl.EnergySystem):
        esi = es.energySystemInformation
        if not esi:
            esi = esdl.EnergySystemInformation(id=str(uuid4()))
            es.energySystemInformation = esi

        sects = esi.sectors
        if not sects:
            sects = esdl.Sectors(id=str(uuid4()))
            esi.sectors = sects

        for s in self.sectors:
            s_info = self.sectors[s]
            # Only add sector if not done earlier already
            if not s_info["sector"]:
                sector = esdl.Sector(id=s_info["id"], name=s_info["name"])
                s_info["sector"] = sector
                sects.sector.append(sector)

    def add_final_demands(self, area):
        for etm_item in self.etm_data:
            if etm_item["Group"] == "Final demand":
                value = etm_item["present_year"]
                if value != "0.000":
                    profile = esdl.SingleValue(id=str(uuid4()), value=float(value))
                    profile.profileQuantityAndUnit = self.create_qau(etm_item["Value Unit"])

                    inport = esdl.InPort(id=str(uuid4()), name="In")
                    inport.carrier = self.carriers[etm_item["Carrier"]]["carrier"]
                    inport.profile.append(profile)

                    name = etm_item["Group"] + '_' + etm_item["Carrier"] + '_' + etm_item["Category"]
                    demand = esdl.EnergyDemand(id=str(uuid4()), name=name, sector=self.sectors[etm_item["Category"]]["sector"])
                    demand.port.append(inport)

                    area.asset.append(demand)
                    self.find_carrier_network_and_connect(area, inport, etm_item["Carrier"])

    def add_production(self, area):
        for etm_item in self.etm_data:
            if etm_item["Group"] == "Primary demand":
                value = etm_item["present_year"]
                if value != "0.000":
                    profile = esdl.SingleValue(id=str(uuid4()), value=float(value))
                    profile.profileQuantityAndUnit = self.create_qau(etm_item["Value Unit"])

                    outport = esdl.OutPort(id=str(uuid4()), name="Out")
                    outport.carrier = self.carriers[etm_item["Carrier"]]["carrier"]
                    outport.profile.append(profile)

                    name = etm_item["Group"] + '_' + etm_item["Carrier"] + '_' + etm_item["Category"]
                    if etm_item["Category"] in self.category_to_asset_type_mapping:
                        if "type" in self.category_to_asset_type_mapping[etm_item["Category"]]:
                            asset_type = self.category_to_asset_type_mapping[etm_item["Category"]]["type"]
                        elif "carrier_mapping" in self.category_to_asset_type_mapping[etm_item["Category"]]:
                            asset_type = self.category_to_asset_type_mapping[etm_item["Category"]]["carrier_mapping"][etm_item["Carrier"]]

                        asset = asset_type(id=str(uuid4()), name=name)
                    else:
                        asset = esdl.GenericProducer(id=str(uuid4()), name=name)
                    asset.port.append(outport)

                    area.asset.append(asset)
                    self.find_carrier_network_and_connect(area, outport, etm_item["Carrier"])

    def find_carrier_network_and_connect(self, area, port, carr_name):
        """ Creates a network if it doesn't exist yet and connects asset """

        if "network" in self.carriers[carr_name]:
            netw = self.carriers[carr_name]["network"]
        else:
            netw = esdl.EnergyNetwork(id=str(uuid4()), name="Network for " + carr_name)
            inport = esdl.InPort(id=str(uuid4()), name="In", carrier=self.carriers[carr_name]["carrier"])
            netw.port.append(inport)
            outport = esdl.OutPort(id=str(uuid4()), name="Out", carrier=self.carriers[carr_name]["carrier"])
            netw.port.append(outport)
            area.asset.append(netw)

            self.carriers[carr_name]["network"] = netw

        if isinstance(port, esdl.InPort):
            netw.port[1].connectedTo.append(port)
        else:
            netw.port[0].connectedTo.append(port)

    def find_rest_of_conversion_data(self, conv_category):
        rest_of_data = list()
        for etm_item in self.etm_data:
            if etm_item["Group"] == "Conversion" and etm_item["Category"] == conv_category and "Processed" not in etm_item:
                etm_item["Processed"] = True
                rest_of_data.append(etm_item)

        return rest_of_data

    def create_conversion(self, area, conv_data):
        conv_asset = esdl.GenericConversion(id=str(uuid4()), name=conv_data[0]["Category"])

        add_later = list()      # to store OutPorts
        for cd in conv_data:
            if cd["Type"] == "Input":
                port = esdl.InPort(id=str(uuid4()))
            else:
                port = esdl.OutPort(id=str(uuid4()))

            port.carrier = self.carriers[cd["Carrier"]]["carrier"]
            profile = esdl.SingleValue(id=str(uuid4()), value=float(cd["present_year"]))
            profile.profileQuantityAndUnit = self.create_qau(cd["Value Unit"])
            port.profile.append(profile)
            self.find_carrier_network_and_connect(area, port, cd["Carrier"])

            # If InPort add to asset port list
            if isinstance(port, esdl.InPort):
                conv_asset.port.append(port)
            else:
                add_later.append(port)

        # Finally add OutPorts
        for p in add_later:
            conv_asset.port.append(p)

        area.asset.append(conv_asset)

    def add_conversions(self, area):
        for etm_item in self.etm_data:
            if etm_item["Group"] == "Conversion" and etm_item["Carrier"] != "Loss":
                if "Processed" in etm_item and etm_item["Processed"]:
                    continue

                etm_item["Processed"] = True

                conv_data = self.find_rest_of_conversion_data(etm_item["Category"])
                conv_data.append(etm_item)

                all_zero = True
                for cd in conv_data:
                    if cd["present_year"] != "0.000":
                        all_zero = False

                if not all_zero:
                    self.create_conversion(area, conv_data)

    def add_carrier_losses(self, area):
        for etm_item in self.etm_data:
            if etm_item["Carrier"] == "Loss":
                conv_loss_carriers = re.findall(r"([a-zA-Z ]+) to ([a-zA-Z ]+) conversion losses", etm_item["Category"])
                # # Only take into account carrier losses other than conversion losses
                # if conv_loss_carriers[0][0].lower() != conv_loss_carriers[0][1].lower():
                #     continue

                value = etm_item["present_year"]
                if value != "0.000":
                    profile = esdl.SingleValue(id=str(uuid4()), value=float(value))
                    profile.profileQuantityAndUnit = self.create_qau(etm_item["Value Unit"])

                    inport = esdl.InPort(id=str(uuid4()), name="In")
                    inport.carrier = self.carriers[conv_loss_carriers[0][0]]["carrier"]
                    inport.profile.append(profile)

                    name = etm_item["Category"]
                    demand = esdl.Losses(id=str(uuid4()), name=name)
                    demand.port.append(inport)

                    area.asset.append(demand)
                    self.find_carrier_network_and_connect(area, inport, conv_loss_carriers[0][0])

    def get_profile_value_in_PJ(self, asset):
        try:
            value = convert_to_unit(
                asset.port[0].profile[0].value,
                asset.port[0].profile[0].profileQuantityAndUnit,
                ENERGY_IN_PJ
            )
        except Exception as e:
            #print("Exception in etm_interface:", e)
            value = None

        return value

    def guess_sector_name(self, asset):
        if asset.eClass.name in self.asset_to_sector_mapping:
            asset_mapping = self.asset_to_sector_mapping[asset.eClass.name]
            if asset.name in asset_mapping:
                asset_info = asset_mapping[asset.name]
                return asset_info["sector"]

        return None

    ###################################################################################################################
    #   KPI calculations
    ###################################################################################################################
    def add_energy_balance_kpi(self, area):
        local_production = 0
        local_consumption = 0

        for asset in area.eAllContents():
            if isinstance(asset, esdl.EnergyAsset):
                value = self.get_profile_value_in_PJ(asset)
                if value:
                    asset_class_name = asset.eClass.name
                    if isinstance(asset, esdl.Consumer) and not isinstance(asset, esdl.Export) and not isinstance(asset, esdl.Losses):
                        local_consumption += value
                    elif asset_class_name in self.local_production_assets:
                        local_production += value

        kpi_name = "Local production vs. consumption [%]"
        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
        kpi.quantityAndUnit = esdl.QuantityAndUnitType(
            physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
            multiplier=esdl.MultiplierEnum.PETA,
            unit=esdl.UnitEnum.JOULE
        )
        kpi.distribution = esdl.StringLabelDistribution(name=kpi_name)
        if local_consumption > 0:
            distr_item = esdl.StringItem(label="Local consumption", value=local_consumption)
            kpi.distribution.stringItem.append(distr_item)
        if local_production > 0:
            distr_item = esdl.StringItem(label="Local production", value=local_production)
            kpi.distribution.stringItem.append(distr_item)

        area.KPIs.kpi.append(kpi)

    def add_final_demand_per_sector_kpi(self, area):
        for sect, sect_info in self.sectors.items():
            sect_info["final_demand"] = 0.0

        for asset in area.eAllContents():
            if isinstance(asset, esdl.Consumer) and not isinstance(asset, esdl.Export) and not isinstance(asset, esdl.Losses):
                value = self.get_profile_value_in_PJ(asset)
                if value:
                    this_sector = asset.sector

                    if this_sector:
                        self.sectors[this_sector.name]["final_demand"] += value
                    else:
                        sector = self.guess_sector_name(asset)
                        if sector:
                            self.sectors[sector]["final_demand"] += value

        kpi_name = "Final demand per sector [PJ]"

        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
        kpi.quantityAndUnit = esdl.QuantityAndUnitType(
            physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
            multiplier=esdl.MultiplierEnum.PETA,
            unit=esdl.UnitEnum.JOULE
        )
        kpi.distribution = esdl.StringLabelDistribution(name=kpi_name)
        for sect, sect_info in self.sectors.items():
            if abs(sect_info["final_demand"]) > 1e-6:
                distr_item = esdl.StringItem(label=sect, value=sect_info["final_demand"])
                kpi.distribution.stringItem.append(distr_item)

        area.KPIs.kpi.append(kpi)

    def add_final_demand_per_carrier_kpi(self, area):
        for carr, carr_info in self.carriers.items():
            carr_info["final_demand"] = 0.0

        for asset in area.eAllContents():
            if isinstance(asset, esdl.Consumer) and not isinstance(asset, esdl.Export) and not isinstance(asset, esdl.Losses):
                value = self.get_profile_value_in_PJ(asset)
                if value:
                    try:
                        this_carrier_name = asset.port[0].carrier.name
                    except:
                        if asset.eClass.name in self.asset_to_carrier_mapping:
                            this_carrier_name = self.asset_to_carrier_mapping[asset.eClass.name]
                        else:
                            this_carrier_name = None

                    if this_carrier_name:
                        self.carriers[this_carrier_name]["final_demand"] += value

        kpi_name = "Final demand per carrier [PJ]"

        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
        kpi.quantityAndUnit = esdl.QuantityAndUnitType(
            physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
            multiplier=esdl.MultiplierEnum.PETA,
            unit=esdl.UnitEnum.JOULE
        )
        kpi.distribution = esdl.StringLabelDistribution(name=kpi_name)
        for carr, carr_info in self.carriers.items():
            if abs(carr_info["final_demand"]) > 1e-6:
                distr_item = esdl.StringItem(label=carr, value=carr_info["final_demand"])
                kpi.distribution.stringItem.append(distr_item)

        area.KPIs.kpi.append(kpi)

    def add_import_per_carrier_kpi(self, area):
        for carr, carr_info in self.carriers.items():
            carr_info["import"] = 0.0

        for asset in area.asset:
            if isinstance(asset, esdl.Import):
                value = self.get_profile_value_in_PJ(asset)
                if value:
                    try:
                        this_carrier_name = asset.port[0].carrier.name
                    except:
                        if asset.eClass.name in self.asset_to_carrier_mapping:
                            this_carrier_name = self.asset_to_carrier_mapping[asset.eClass.name]
                        else:
                            this_carrier_name = None

                    if this_carrier_name:
                        self.carriers[this_carrier_name]["import"] += value

        kpi_name = "Import per carrier [PJ]"

        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
        kpi.quantityAndUnit = esdl.QuantityAndUnitType(
            physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
            multiplier=esdl.MultiplierEnum.PETA,
            unit=esdl.UnitEnum.JOULE
        )
        kpi.distribution = esdl.StringLabelDistribution(name=kpi_name)
        for carr, carr_info in self.carriers.items():
            if abs(carr_info["import"]) > 1e-6:
                distr_item = esdl.StringItem(label=carr, value=carr_info["import"])
                kpi.distribution.stringItem.append(distr_item)

        area.KPIs.kpi.append(kpi)

    def add_clustered_demand_kpi(self, area):
        cluster_totals = dict()
        for sect, sect_info in self.sectors.items():
            if not sect_info["cluster"] in cluster_totals:
                cluster_totals[sect_info["cluster"]] = 0.0

        for asset in area.eAllContents():
            if isinstance(asset, esdl.EnergyDemand):
                value = self.get_profile_value_in_PJ(asset)
                if value:
                    this_sector = asset.sector
                    cluster = self.sectors[this_sector.name]["cluster"]
                    cluster_totals[cluster] += value
            elif isinstance(asset, esdl.Consumer) and not isinstance(asset, esdl.Export) and not isinstance(asset, esdl.Losses):
                value = self.get_profile_value_in_PJ(asset)
                if value:
                    sector_name = self.guess_sector_name(asset)
                    if sector_name:
                        cluster = self.sectors[sector_name]["cluster"]
                        cluster_totals[cluster] += value

        kpi_name = "Clustered final demand [PJ]"

        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
        kpi.quantityAndUnit = esdl.QuantityAndUnitType(
            physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
            multiplier=esdl.MultiplierEnum.PETA,
            unit=esdl.UnitEnum.JOULE
        )
        kpi.distribution = esdl.StringLabelDistribution(name=kpi_name)
        for cluster, cluster_total in cluster_totals.items():
            if abs(cluster_totals[cluster]) > 1e-6:
                distr_item = esdl.StringItem(label=cluster, value=cluster_total)
                kpi.distribution.stringItem.append(distr_item)

        area.KPIs.kpi.append(kpi)

    def add_local_production_kpi(self, area):
        for local_prod, local_prod_info in self.local_production_assets.items():
            local_prod_info["total"] = 0.0

        for asset in area.eAllContents():
            if asset.eClass.name in self.local_production_assets:
                value = self.get_profile_value_in_PJ(asset)
                if value:
                    self.local_production_assets[asset.eClass.name]["total"] += value

        kpi_name = "Local production [PJ]"
        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
        kpi.quantityAndUnit = esdl.QuantityAndUnitType(
            physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
            multiplier=esdl.MultiplierEnum.PETA,
            unit=esdl.UnitEnum.JOULE
        )
        kpi.distribution = esdl.StringLabelDistribution(name=kpi_name)
        for local_prod, local_prod_info in self.local_production_assets.items():
            if local_prod_info["total"] > 0:
                distr_item = esdl.StringItem(label=local_prod, value=local_prod_info["total"])
                kpi.distribution.stringItem.append(distr_item)

        area.KPIs.kpi.append(kpi)

    def add_local_production_incl_import_kpi(self, area):
        for local_prod, local_prod_info in self.local_production_assets.items():
            local_prod_info["total"] = 0.0
        import_total = 0.0

        for asset in area.eAllContents():
            if isinstance(asset, esdl.Producer):
                value = self.get_profile_value_in_PJ(asset)
                if value:
                    if asset.eClass.name in self.local_production_assets:
                        self.local_production_assets[asset.eClass.name]["total"] += value
                    elif asset.eClass.name == "Import":
                        import_total += value

        kpi_name = "Local production (incl. Import) [PJ]"
        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
        kpi.quantityAndUnit = esdl.QuantityAndUnitType(
            physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
            multiplier=esdl.MultiplierEnum.PETA,
            unit=esdl.UnitEnum.JOULE
        )
        kpi.distribution = esdl.StringLabelDistribution(name=kpi_name)
        for local_prod, local_prod_info in self.local_production_assets.items():
            if local_prod_info["total"] > 0:
                distr_item = esdl.StringItem(label=local_prod, value=local_prod_info["total"])
                kpi.distribution.stringItem.append(distr_item)

        if import_total > 0:
            distr_item = esdl.StringItem(label="Import", value=import_total)
            kpi.distribution.stringItem.append(distr_item)

        area.KPIs.kpi.append(kpi)

    def add_electricity_demand_per_sector_and_cluster_kpi(self, area):
        electricity_demand_per_sector = dict()
        electricity_demand_per_cluster = dict()

        for asset in area.eAllContents():
            electricity_demand_asset = False
            if isinstance(asset, esdl.EnergyDemand):
                sector = asset.sector.name
                value = self.get_profile_value_in_PJ(asset)
                if value:
                    if asset.port[0].carrier and asset.port[0].carrier.name == "Electricity":
                        electricity_demand_asset = True
            elif isinstance(asset, esdl.ElectricityDemand):
                value = self.get_profile_value_in_PJ(asset)
                sector = self.guess_sector_name(asset)
                if value and sector:
                    electricity_demand_asset = True

            if electricity_demand_asset:
                cluster_name = self.sectors[sector]["cluster"]

                if sector in electricity_demand_per_sector:
                    electricity_demand_per_sector[sector] += value
                else:
                    electricity_demand_per_sector[sector] = value

                if cluster_name in electricity_demand_per_cluster:
                    electricity_demand_per_cluster[cluster_name] += value
                else:
                    electricity_demand_per_cluster[cluster_name] = value

        kpi_name = "Electricity demand per sector [PJ]"
        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
        kpi.quantityAndUnit = esdl.QuantityAndUnitType(
            physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
            multiplier=esdl.MultiplierEnum.PETA,
            unit=esdl.UnitEnum.JOULE
        )
        kpi.distribution = esdl.StringLabelDistribution(name=kpi_name)
        for sector_name, sector_total in electricity_demand_per_sector.items():
            if abs(electricity_demand_per_sector[sector_name]) > 1e-6:
                distr_item = esdl.StringItem(label=sector_name, value=sector_total)
                kpi.distribution.stringItem.append(distr_item)

        area.KPIs.kpi.append(kpi)

        kpi_name = "Electricity demand per cluster [PJ]"
        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
        kpi.quantityAndUnit = esdl.QuantityAndUnitType(
            physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
            multiplier=esdl.MultiplierEnum.PETA,
            unit=esdl.UnitEnum.JOULE
        )
        kpi.distribution = esdl.StringLabelDistribution(name=kpi_name)
        for cluster_name, cluster_total in electricity_demand_per_cluster.items():
            if abs(electricity_demand_per_cluster[cluster_name]) > 1e-6:
                distr_item = esdl.StringItem(label=cluster_name, value=cluster_total)
                kpi.distribution.stringItem.append(distr_item)

        area.KPIs.kpi.append(kpi)

        return electricity_demand_per_cluster

    def add_electricity_production_kpi(self, area):
        electricity_production_per_cluster = dict()

        for asset in area.eAllContents():
            electricity_production_asset = False
            asset_class_name = asset.eClass.name
            if asset_class_name in self.local_production_assets:
                value = self.get_profile_value_in_PJ(asset)
                if value:
                    if (asset.port[0].carrier and asset.port[0].carrier.name == "Electricity") or \
                        ("carrier" in self.local_production_assets[asset_class_name] and
                         self.local_production_assets[asset_class_name]["carrier"] == "Electricity"):
                        electricity_production_asset = True

            if electricity_production_asset:
                cluster_name = self.local_production_assets[asset_class_name]["cluster"]

                if cluster_name in electricity_production_per_cluster:
                    electricity_production_per_cluster[cluster_name] += value
                else:
                    electricity_production_per_cluster[cluster_name] = value

        kpi_name = "Electricity production per cluster [PJ]"
        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
        kpi.quantityAndUnit = esdl.QuantityAndUnitType(
            physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
            multiplier=esdl.MultiplierEnum.PETA,
            unit=esdl.UnitEnum.JOULE
        )
        kpi.distribution = esdl.StringLabelDistribution(name=kpi_name)
        for cluster_name, cluster_total in electricity_production_per_cluster.items():
            if abs(electricity_production_per_cluster[cluster_name]) > 1e-6:
                distr_item = esdl.StringItem(label=cluster_name, value=cluster_total)
                kpi.distribution.stringItem.append(distr_item)

        area.KPIs.kpi.append(kpi)

        return electricity_production_per_cluster

    def calculate_power_based_on_energy(self, area, electricity_demand_per_cluster, electricity_production_per_cluster):
        # Create hourly energy demand profiles for all clusters
        energy_demand_profiles = dict()
        for cluster_name, cluster_total in electricity_demand_per_cluster.items():
            if abs(electricity_demand_per_cluster[cluster_name]) > 1e-6:
                if cluster_name in global_clusters:
                    energy_demand_profiles[cluster_name] = \
                        [electricity_demand_per_cluster[cluster_name] * x
                         for x in global_clusters[cluster_name]["profile_data"]]

        # Calculate the max demand energy values over the year
        peak_demand_energy_per_hour = dict()
        sum_vector = np.zeros(len(energy_demand_profiles[list(energy_demand_profiles.keys())[0]]))
        for cluster_name, energy_values in energy_demand_profiles.items():
            this_cluster_values = np.array(energy_values)
            sum_vector += this_cluster_values
            peak_demand_energy_per_hour[cluster_name] = this_cluster_values.max()

        peak_demand_energy_per_hour["Total"] = sum_vector.max()

        # Create hourly energy production profiles for all clusters
        energy_production_profiles = dict()
        for cluster_name, cluster_total in electricity_production_per_cluster.items():
            if abs(electricity_production_per_cluster[cluster_name]) > 1e-6:
                if cluster_name in global_clusters:
                    energy_production_profiles[cluster_name] = \
                        [electricity_production_per_cluster[cluster_name] * x
                         for x in global_clusters[cluster_name]["profile_data"]]

        # Calculate the max production energy values over the year
        peak_production_energy_per_hour = dict()
        if energy_production_profiles:
            sum_vector = np.zeros(len(energy_production_profiles[list(energy_production_profiles.keys())[0]]))
            for cluster_name, energy_values in energy_production_profiles.items():
                this_cluster_values = np.array(energy_values)
                sum_vector += this_cluster_values
                peak_production_energy_per_hour[cluster_name] = this_cluster_values.max()

            peak_production_energy_per_hour["Total"] = sum_vector.max()

        # Add KPI with peak demand power value
        kpi_name = "Peak demand power per cluster [MW]"
        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
        kpi.quantityAndUnit = build_qau_from_unit_string("MW")
        kpi.distribution = esdl.StringLabelDistribution(name=kpi_name)
        for cluster_name, peak_energy in peak_demand_energy_per_hour.items():
            power = peak_energy / 3600 * 1e9
            distr_item = esdl.StringItem(label=cluster_name, value=float(power))
            kpi.distribution.stringItem.append(distr_item)
        area.KPIs.kpi.append(kpi)

        # Add KPI with peak production power value
        kpi_name = "Peak production power per cluster [MW]"
        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
        kpi.quantityAndUnit = build_qau_from_unit_string("MW")
        kpi.distribution = esdl.StringLabelDistribution(name=kpi_name)
        for cluster_name, peak_energy in peak_production_energy_per_hour.items():
            power = peak_energy / 3600 * 1e9
            distr_item = esdl.StringItem(label=cluster_name, value=float(power))
            kpi.distribution.stringItem.append(distr_item)
        area.KPIs.kpi.append(kpi)

    def recalculate_kpis(self, area):
        # Add will override the existing KPIs
        self.add_kpis(area)

    def add_kpis(self, area):
        area.KPIs = esdl.KPIs(id=str(uuid4()), description="ETM KPIs present_year")
        self.add_energy_balance_kpi(area)
        self.add_clustered_demand_kpi(area)
        self.add_local_production_kpi(area)
        self.add_local_production_incl_import_kpi(area)
        self.add_final_demand_per_sector_kpi(area)
        self.add_final_demand_per_carrier_kpi(area)
        self.add_import_per_carrier_kpi(area)

        electricity_demand_per_cluster = self.add_electricity_demand_per_sector_and_cluster_kpi(area)
        electricity_production_per_cluster = self.add_electricity_production_kpi(area)
        self.calculate_power_based_on_energy(area, electricity_demand_per_cluster, electricity_production_per_cluster)

    def replace_all_subarea_kpis(self, area):
        print(f"Handling {area.name}")
        if area.KPIs:
            self.add_kpis(area)

        for subarea in area.area:
            if subarea.KPIs:
                self.add_kpis(subarea)
            if subarea.area:
                self.replace_all_subarea_kpis(subarea)

    ###################################################################################################################
    #   Functions to add relevant info to an esdl.Area
    ###################################################################################################################

    def add_info_to_area(self, area):
        self.add_final_demands(area)
        self.add_production(area)
        self.add_carrier_losses(area)
        self.add_conversions(area)
        self.add_kpis(area)

    def add_carriers_and_sectors(self, es):
        self.create_carriers(es)
        self.create_sectors(es)

    ###################################################################################################################
    #   Functions to calculate effects of the heat transition
    ###################################################################################################################
    def apply_heat_transition(self, area, technology_info):
        # TODO: Deal with QaU, deal with "space heater" and "space heater combined", deal with tapwater
        gas_demand_households_heating = None
        energy_natural_gas_profile_PJ = None
        for asset in area.asset:
            if asset.name == "Final demand_Natural gas_Households space heating and hot water":
                gas_demand_households_heating = asset
                energy_natural_gas_profile_PJ = asset.port[0].profile[0].value
                break

        if gas_demand_households_heating and energy_natural_gas_profile_PJ:
            final_heating_demand_PJ = energy_natural_gas_profile_PJ / 0.9
            final_heating_demand_heatpump_PJ =  final_heating_demand_PJ * technology_info[0]["percentage"] / 100
            final_heating_demand_district_heating_PJ =  final_heating_demand_PJ * technology_info[1]["percentage"] / 100

            electricity_demand_PJ = final_heating_demand_heatpump_PJ / 3.5           # COP = 3.5
            steam_hotwater_demand_PJ = final_heating_demand_district_heating_PJ      # efficiency = 1

            for asset in area.asset:
                if asset.name == "Final demand_Electricity_Households space heating and hot water":
                    asset.port[0].profile[0].value += electricity_demand_PJ
                if asset.name == "Final demand_Steam hot water_Households space heating and hot water":
                    asset.port[0].profile[0].value += steam_hotwater_demand_PJ

                # TODO: now it is assumed extra energy is imported
                if asset.name == "Primary demand_Electricity_Import":
                    asset.port[0].profile[0].value += electricity_demand_PJ
                if asset.name == "Primary demand_Steam hot water_Import":
                    asset.port[0].profile[0].value += steam_hotwater_demand_PJ

            gas_demand_households_heating.port[0].profile[0].value = 0.0

            self.recalculate_kpis(area)

            container = area
            # container will become equal to the top-level area
            while isinstance(container.eContainer(), esdl.Area):
                container = container.eContainer()

            # redraw all areas and KPIs, as KPIs have changed
            find_boundaries_in_ESDL(container)
        else:
            logger.error("Cannot apply heat transition measures. Maybe ETM data is not loaded")
