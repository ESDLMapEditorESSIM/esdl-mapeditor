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
from flask_socketio import SocketIO
import requests
import csv
import codecs
import json
import re
from uuid import uuid4

from esdl import esdl
from esdl.processing.ESDLQuantityAndUnits import unit_to_string
from extensions.session_manager import get_handler, get_session
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
            esh = get_handler()
            area = esh.get_by_id(active_es_id, area_id)
            if area.scope is not esdl.AreaScopeEnum.MUNICIPALITY:
                return "Can only be called for municipalities"

            etm_sankey_data = self.request_sankey_info(area_id)
            if etm_sankey_data:
                self.process_data_and_add_to_area(esh, active_es_id, area, etm_sankey_data)
                return "Ok"
            else:
                return "Something went wrong"

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

    def request_sankey_info(self, municipality_code):
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

    def process_data_and_add_to_area(self, esh, active_es_id, area, etm_sankey_data):
        es = esh.get_energy_system(es_id=active_es_id)

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

        self.carriers = {
            "Ammonia": {"name": "Ammonia"},
            "Biomass": {"name": "Biomass"},
            "Coal": {"name": "Coal"},
            "Electricity": {"name": "Electricity"},
            "Geothermal": {"name": "Geothermal"},
            "Hydrogen": {"name": "Hydrogen"},
            "Liquid hydrogen": {"name": "Liquid hydrogen"},
            "LOHC": {"name": "LOHC"},
            "Natural gas": {"name": "Natural gas"},
            "Oil": {"name": "Oil"},
            "Solar thermal": {"name": "Solar thermal"},
            "Steam hot water": {"name": "Steam hot water"},
            "Uranium": {"name": "Uranium"}
        }

        self.sectors = {
            "Agriculture": {"name": "Agriculture"},
            "Buildings excl. space heating": {"name": "Buildings excl. space heating"},
            "Buildings space heating": {"name": "Buildings space heating"},
            "Energy": {"name": "Energy"},
            "Export": {"name": "Export"},
            "Feedstock": {"name": "Feedstock"},
            "Households excl. space heating and hot water": {"name": "Households excl. space heating and hot water"},
            "Households space heating and hot water": {"name": "Households space heating and hot water"},
            "Industry excl. ICT": {"name": "Industry excl. ICT"},
            "Industry excl. ICT and power-to-heat": {"name": "Industry excl. ICT and power-to-heat"},
            "Industry ICT": {"name": "Industry ICT"},
            "Industry power-to-heat": {"name": "Industry power-to-heat"},
            "International transport": {"name": "International transport"},
            "National transport": {"name": "National transport"},
            "Other": {"name": "Other"},
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
            carr_id = str(uuid4())
            carr = esdl.EnergyCarrier(id=carr_id, name=c_info["name"])
            c_info["id"] = carr_id
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
            sector_id = str(uuid4())
            sector = esdl.Sector(id=sector_id, name=s_info["name"])
            s_info["id"] = sector_id
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

    def add_kpis(self, area):
        area.KPIs = esdl.KPIs(id=str(uuid4()), description="ETM KPIs present_year")
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
