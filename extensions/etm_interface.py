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

from flask import Flask
from flask_socketio import SocketIO, emit
import requests
import csv
import codecs
import json
import re
from uuid import uuid4

from esdl import esdl
from esdl.processing.ESDLQuantityAndUnits import unit_to_string
from extensions.session_manager import get_session, get_project_manager
from extensions.settings_storage import SettingsStorage
import src.settings as settings
import src.log as log
from src.process_es_area_bld import get_area_id_from_mapeditor_id


logger = log.get_logger(__name__)

ETM_INTERFACE_SYSTEM_CONFIG = 'ETM_INTERFACE_SYSTEM_CONFIG'
ETM_INTERFACE_DEFAULT_SYSTEM_CONFIG = {
    'etm_base_url': 'https://engine.energytransitionmodel.com/api/v3',
    'etm_municipalities_file': 'data/ETM_municipalities.csv'
}


class ETMInterface:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.etm_municipalities = dict()

        self.plugin_settings = self.get_settings()
        self.register()

        self.read_etm_municipalities()

    def register(self):
        logger.info('Registering ETMInterface extension')

        @self.socketio.on('etm_get_sankey_data', namespace='/esdl')
        def etm_get_sankey_data(area_id):
            # area_id could have "(3 of 5)" in it, if the Area clicked is the third polygon af a total of five polygons
            area_id = get_area_id_from_mapeditor_id(area_id)
            active_es_id = get_session('active_es_id')
            pm = get_project_manager()
            area = pm.get_by_id(active_es_id, area_id)

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

    def process_data_and_add_to_area(self, pm, active_es_id, area, etm_sankey_data):
        es = pm.get_active_energy_system()

        etm_sankey = ETMSankeyToESDL(etm_sankey_data)
        etm_sankey.add_carriers_and_sectors(es)
        etm_sankey.add_info_to_area(area)
        etm_sankey.clear_area_logbook()

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
        self.local_production_assets = {
            "WindTurbine": {},
            "PVInstallation": {},
            "GeothermalSource": {},
            "SolarCollector": {}
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
            "Natural gas": {"id": "etm_carrier_natural_gas", "name": "Natural gas", "carrier": None},
            "Oil": {"id": "etm_carrier_oil", "name": "Oil", "carrier": None},
            "Solar thermal": {"id": "etm_carrier_solar_thermal", "name": "Solar thermal", "carrier": None},
            "Steam hot water": {"id": "etm_carrier_shw", "name": "Steam hot water", "carrier": None},
            "Uranium": {"id": "etm_carrier_uranium", "name": "Uranium", "carrier": None}
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

    def add_energy_balance_kpi(self, area):
        local_production = 0
        local_consumption = 0

        for asset in area.asset:
            asset_class_name = asset.eClass.name
            if isinstance(asset, esdl.EnergyDemand):
                local_consumption += asset.port[0].profile[0].value
            elif asset_class_name in self.local_production_assets:
                local_production += asset.port[0].profile[0].value

        kpi_name = "Local production vs. consumption [%]"
        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
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

        kpi_unit = None

        for asset in area.asset:
            if isinstance(asset, esdl.EnergyDemand):
                this_sector = asset.sector
                self.sectors[this_sector.name]["final_demand"] += asset.port[0].profile[0].value
                if not kpi_unit:
                    kpi_unit = asset.port[0].profile[0].profileQuantityAndUnit

        kpi_name = "Final demand per sector [" + unit_to_string(kpi_unit) + "]"

        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
        kpi.distribution = esdl.StringLabelDistribution(name=kpi_name)
        for sect, sect_info in self.sectors.items():
            if abs(sect_info["final_demand"]) > 1e-6:
                distr_item = esdl.StringItem(label=sect, value=sect_info["final_demand"])
                kpi.distribution.stringItem.append(distr_item)

        area.KPIs.kpi.append(kpi)

    def add_final_demand_per_carrier_kpi(self, area):
        for carr, carr_info in self.carriers.items():
            carr_info["final_demand"] = 0.0

        kpi_unit = None

        for asset in area.asset:
            if isinstance(asset, esdl.EnergyDemand):
                this_carrier = asset.port[0].carrier
                self.carriers[this_carrier.name]["final_demand"] += asset.port[0].profile[0].value
                if not kpi_unit:
                    kpi_unit = asset.port[0].profile[0].profileQuantityAndUnit

        kpi_name = "Final demand per carrier [" + unit_to_string(kpi_unit) + "]"

        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
        kpi.distribution = esdl.StringLabelDistribution(name=kpi_name)
        for carr, carr_info in self.carriers.items():
            if abs(carr_info["final_demand"]) > 1e-6:
                distr_item = esdl.StringItem(label=carr, value=carr_info["final_demand"])
                kpi.distribution.stringItem.append(distr_item)

        area.KPIs.kpi.append(kpi)

    def add_import_per_carrier_kpi(self, area):
        for carr, carr_info in self.carriers.items():
            carr_info["import"] = 0.0

        kpi_unit = None

        for asset in area.asset:
            if isinstance(asset, esdl.Import):
                this_carrier = asset.port[0].carrier
                self.carriers[this_carrier.name]["import"] += asset.port[0].profile[0].value
                if not kpi_unit:
                    kpi_unit = asset.port[0].profile[0].profileQuantityAndUnit

        kpi_name = "Import per carrier [" + unit_to_string(kpi_unit) + "]"

        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
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

        kpi_unit = None

        for asset in area.asset:
            if isinstance(asset, esdl.EnergyDemand):
                this_sector = asset.sector
                cluster = self.sectors[this_sector.name]["cluster"]
                cluster_totals[cluster] += asset.port[0].profile[0].value

                if not kpi_unit:
                    kpi_unit = asset.port[0].profile[0].profileQuantityAndUnit

        kpi_name = "Clustered final demand [" + unit_to_string(kpi_unit) + "]"

        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
        kpi.distribution = esdl.StringLabelDistribution(name=kpi_name)
        for cluster, cluster_total in cluster_totals.items():
            if abs(cluster_totals[cluster]) > 1e-6:
                distr_item = esdl.StringItem(label=cluster, value=cluster_total)
                kpi.distribution.stringItem.append(distr_item)

        area.KPIs.kpi.append(kpi)

    def add_local_production_kpi(self, area):
        for local_prod, local_prod_info in self.local_production_assets.items():
            local_prod_info["total"] = 0.0

        kpi_unit = None

        for asset in area.asset:
            asset_class_name = asset.eClass.name
            if asset_class_name in self.local_production_assets:
                self.local_production_assets[asset_class_name]["total"] += asset.port[0].profile[0].value

                if not kpi_unit:
                    kpi_unit = asset.port[0].profile[0].profileQuantityAndUnit

        kpi_name = "Local production [" + unit_to_string(kpi_unit) + "]"
        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
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

        kpi_unit = None

        for asset in area.asset:
            asset_class_name = asset.eClass.name
            if asset_class_name in self.local_production_assets:
                self.local_production_assets[asset_class_name]["total"] += asset.port[0].profile[0].value
            elif asset_class_name == "Import":
                import_total += asset.port[0].profile[0].value

                if not kpi_unit:
                    kpi_unit = asset.port[0].profile[0].profileQuantityAndUnit

        kpi_name = "Local production (incl. Import) [" + unit_to_string(kpi_unit) + "]"
        kpi = esdl.DistributionKPI(id=str(uuid4()), name=kpi_name)
        kpi.distribution = esdl.StringLabelDistribution(name=kpi_name)
        for local_prod, local_prod_info in self.local_production_assets.items():
            if local_prod_info["total"] > 0:
                distr_item = esdl.StringItem(label=local_prod, value=local_prod_info["total"])
                kpi.distribution.stringItem.append(distr_item)

        if import_total > 0:
            distr_item = esdl.StringItem(label="Import", value=import_total)
            kpi.distribution.stringItem.append(distr_item)

        area.KPIs.kpi.append(kpi)

    def add_kpis(self, area):
        area.KPIs = esdl.KPIs(id=str(uuid4()), description="ETM KPIs present_year")
        self.add_energy_balance_kpi(area)
        self.add_clustered_demand_kpi(area)
        self.add_local_production_kpi(area)
        self.add_local_production_incl_import_kpi(area)
        self.add_final_demand_per_sector_kpi(area)
        self.add_final_demand_per_carrier_kpi(area)
        self.add_import_per_carrier_kpi(area)

    def add_info_to_area(self, area):
        self.add_final_demands(area)
        self.add_production(area)
        self.add_carrier_losses(area)
        self.add_conversions(area)
        self.add_kpis(area)

    def add_carriers_and_sectors(self, es):
        self.create_carriers(es)
        self.create_sectors(es)
