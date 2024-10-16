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
import copy
import logging
from datetime import datetime
from enum import Enum
from numbers import Number
from typing import TypedDict, List, Dict, Optional, Sequence, Iterable

from flask import Flask
from flask_socketio import SocketIO
from pyecore.valuecontainer import EList
from sqlalchemy import select, distinct, text, literal_column
from sqlalchemy.orm import Session

import esdl
from esdl import QuantityAndUnitType, PipeDiameterEnum
from esdl.processing.ESDLAsset import get_asset_capability_type
from esdl.processing.ESDLQuantityAndUnits import unit_to_string, build_qau_from_unit_string, qau_to_string
from extensions.data_manager import db
from extensions.data_manager.db_interaction import create_db, drop_db, create_test_data
from extensions.data_manager.db_model import DataSet, Variable, DataType, Data, BaseModel
from src import settings
from src.log import get_logger
import statistics

logger = get_logger(__name__)


class ESDLScope(Enum):
    ALL = 0
    PROFILE = 1
    KPI = 2


class QueryMessage(TypedDict):
    es_id: str


class FilterOptions(TypedDict):
    options: List[str]
    column: str
    key: Optional[str]

class Label(TypedDict):
    name: str
    value: str


def physical_q_to_str(qau: esdl.QuantityAndUnitType):
    if qau.physicalQuantity:
        name:str = qau.physicalQuantity.name
        return f'{name[0]}{name.lower()[1:]}'
    else:
        return "Unknown"

def filter_none(input_list: Sequence) -> List:
    return [x for x in input_list if x is not None]

def update_kpi_metadata(kpi: esdl.KPI, data: Data):
    print('Handle KPI ', kpi.name)
    labels = {}
    kpis_container = kpi.eContainer()
    level_cnt: int = 0
    while isinstance(kpis_container, esdl.KPI): # dealing with subkpi
        level_cnt += 1
        kpis_container = kpis_container.eContainer()
    labels['KPI level'] = level_cnt
    container = kpis_container.eContainer()
    data.sector = kpi.sector.name if kpi.sector else None
    data.input = kpi.carrier.name if kpi.carrier else None
    if kpi.matter:
        labels['Matter'] = kpi.matter.name or kpi.matter.id
        labels['Matter state'] = kpi.matter.stateOfMatter.name if kpi.matter.stateOfMatter else None
    if isinstance(container, esdl.Asset):
        # asset KPI
        data.region = container.area.name
        data.node = container.name or container.id
        data.technology = container.eClass.name
    elif isinstance(container, esdl.Area):
        # area KPI
        data.region = container.name

    if len(labels) > 0:
        data.labels = labels

def aggreate_based_on_unit(qau: esdl.QuantityAndUnitType, values: Iterable[float]) -> float:
    """
    Aggregates a list of values based on the physical quantity of a unit. E.g. sum energy, but average power values.
    :param qau: esdl.QuantityAndUnitType for the physical quantity
    :param values: List of values to aggregate
    :return: the aggregated value (sum or mean)
    """
    if qau.physicalQuantity == esdl.PhysicalQuantityEnum.ENERGY or \
            qau.physicalQuantity == esdl.PhysicalQuantityEnum.COST or \
            qau.physicalQuantity == esdl.PhysicalQuantityEnum.EMISSION or \
            qau.physicalQuantity == esdl.PhysicalQuantityEnum.LENGTH or \
            qau.physicalQuantity == esdl.PhysicalQuantityEnum.DISTANCE or \
            qau.physicalQuantity == esdl.PhysicalQuantityEnum.VOLUME or \
            qau.physicalQuantity == esdl.PhysicalQuantityEnum.AREA or \
            qau.physicalQuantity == esdl.PhysicalQuantityEnum.WEIGHT:
        value = sum(values)
    else:
        value = statistics.fmean(values)
    return value

def check_qau(qau: esdl.AbstractQuantityAndUnit) -> esdl.QuantityAndUnitType:
    while isinstance(qau, esdl.QuantityAndUnitReference):
        qau = qau.reference
    if not qau:
        #qau = build_qau_from_unit_string("GJ")
        #qau.physicalQuantity = esdl.PhysicalQuantityEnum.ENERGY
        qau = esdl.QuantityAndUnitType()  # empty/unknown unit
    return qau

def handle_profile(profile: esdl.GenericProfile, ds: DataSet, variable_name: str = None) -> [Data, esdl.QuantityAndUnitType, str]:
    """
    Process an esdl GenericProfile
    :param profile: Profile to process
    :param ds: Data set this data belongs to
    :param variable_name: variable name of this data point if already known, otherwise it will be created
    :return: Data point, its unit and variable_name of this data point
    """
    container = profile.eContainer() # save profile container (e.g. asset, also in case it is a reference)
    multiplier = 1
    while isinstance(profile, esdl.ProfileReference):
        multiplier = multiplier * profile.multiplier
        profile = profile.reference
    qau = check_qau(profile.profileQuantityAndUnit)
    d = Data(dataset=ds, value=0) # default no value
    if isinstance(profile, esdl.TimeSeriesProfile):
        ts_profile: esdl.TimeSeriesProfile = profile
        aggregate = aggreate_based_on_unit(qau, ts_profile.values) * multiplier
        d = Data(dataset=ds, value=aggregate)
    elif isinstance(profile, esdl.SingleValue):
        d = Data(dataset=ds, value=profile.value * multiplier)
    elif isinstance(profile, esdl.DateTimeProfile):
        logger.warn("DateTimeSeriesProfile not yet supported")
    elif isinstance(profile, esdl.InfluxDBProfile):
        logger.warn("DateTimeSeriesProfile not yet supported")
    if isinstance(container, esdl.Port):  # usually a port

        port: esdl.Port = container
        asset: esdl.EnergyAsset = port.energyasset
        capability = get_asset_capability_type(asset)
        labels = {'Capability': capability}
        area = asset.area
        if asset.containingBuilding or asset.containingAsset:
            container_asset = asset.eContainer()
            area = container_asset.area
            labels['Parent asset'] = container_asset.name
        d.sector = asset.sector.name if asset.sector else None
        d.node = asset.name or asset.id
        d.region = area.name
        d.technology = asset.eClass.name


        variable_name = f'{physical_q_to_str(qau)} [{unit_to_string(qau)}]'
        if isinstance(port, esdl.InPort):
            d.input = port.carrier.name if port.carrier else None
            labels["Flow direction"] = 'In'
        else:
            port: esdl.OutPort
            d.output = port.carrier.name if port.carrier else None
            labels["Flow direction"] = 'Out'
            if len(port.connectedTo) > 0:
                target_asset = port.connectedTo[0].energyasset
                d.to_node = target_asset.name or target_asset.id
        other_ports = asset.port.select(lambda p: p != port)
        if len(other_ports) > 0:
            labels['Graph position'] = "Interior"
        else:
            labels['Graph position'] = "Edge"
        d.labels = labels
    elif isinstance(container, esdl.CostInformation):  # handle costinformation
        cost_type = profile.eContainmentFeature().name
        labels = {"Cost type": cost_type}
        if profile.name and profile.name != "":
            labels["Cost type"] = profile.name
        if not variable_name:
            variable_name = f'{physical_q_to_str(qau)} [{unit_to_string(qau)}]'
            # variable_name =
        asset = container.eContainer()
        if isinstance(asset, esdl.EnergyAsset):  # TODO: could also be measure
            area = asset.area
            if asset.containingBuilding or asset.containingAsset:
                container_asset = asset.eContainer()
                area = container_asset.area
                labels['Parent asset'] = container_asset.name
            d.sector = asset.sector.name if asset.sector else None
            d.node = asset.name or asset.id
            d.region = area.name
            d.technology = asset.eClass.name
        d.labels = labels
    # else:
    #     # e.g. container is Profiles section, we can ignore these as they are not directy attached to an asset port
    #     continue
    return d, qau, variable_name


class DataManager:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self):
        logger.info("Registering DataManager extension")
        sqllogger = logging.getLogger("sqlalchemy.engine")
        sqllogger.setLevel(logging.INFO)
        logger.info(f"Connecting to Data Manager database using: {settings.SQLALCHEMY_DATABASE_URI}")
        self.flask_app.config.update({"SQLALCHEMY_DATABASE_URI": settings.SQLALCHEMY_DATABASE_URI})
        db.init_app(self.flask_app)  # init SQLAlchemy

        # init database
        with self.flask_app.app_context():
            #drop_db(self.flask_app.config["SQLALCHEMY_DATABASE_URI"])
            create_db(self.flask_app.config["SQLALCHEMY_DATABASE_URI"])

        self.query_data(db.session)

        @self.socketio.on("datamanager/query", namespace="/esdl")
        def query_data(message):
            with self.flask_app.app_context():
                pass

    def process_esdl(self, es: esdl.EnergySystem, owner: str, scenario_name=None) -> List[BaseModel]:
        """
        processes the ESDL with
        :param es: ecore EObject  (e.g. EnergySystem)
        :param owner: the owner/email of the dataset that is created
        :return: List of database entries to add to the database (BaseModel subclasses)
        """

        data_list: List[BaseModel] = []
        variables: Dict[str, Variable] = {}

        year = datetime.now().year
        first_instance: esdl.Instance = es.instance[0]
        if first_instance.date:
            if isinstance(first_instance.date, esdl.InstanceDate):
                instance_datetime: datetime = first_instance.date.date
                year = instance_datetime.year

        if not scenario_name:
            scenario_name = f"Data from {es.name}"

        ds = DataSet(name=es.name, energy_system_id=es.id, created_by=owner, description=es.description, model="Unknown",
                     scenario=scenario_name)
        for eobj in es.eAllContents():
            #variable_name = eobj.name if hasattr(eobj, 'name') else None
            variable_name = None
            if isinstance(eobj, esdl.SingleValue) or isinstance(eobj, esdl.TimeSeriesProfile):
                logger.debug(f"Handling {eobj.eClass.name}/{eobj.name}")
                # single value profile
                # profile: esdl.SingleValue = eobj
                d, qau, variable_name = handle_profile(eobj, ds, variable_name)

            elif isinstance(eobj, esdl.ProfileReference):
                # handle reference too, as we need a reference to the asset
                d, qau, variable_name = handle_profile(eobj, ds, variable_name)
            elif isinstance(eobj, esdl.DoubleKPI):
                d = Data(dataset=ds)
                d.labels = d.labels if d.labels is not None else {}
                update_kpi_metadata(eobj, d)
                qau = check_qau(eobj.quantityAndUnit)
                variable_name = f'KPI - {physical_q_to_str(qau)} [{unit_to_string(qau)}]'
                d.labels["KPI type"] = eobj.name
                d.value = eobj.value
            elif isinstance(eobj, esdl.IntKPI):
                d = Data(dataset=ds)
                d.labels = d.labels if d.labels is not None else {}
                update_kpi_metadata(eobj, d)
                qau = check_qau(eobj.quantityAndUnit)
                variable_name = f'KPI - {physical_q_to_str(qau)} [{unit_to_string(qau)}]'
                d.labels["KPI type"] = eobj.name
                d.value = float(eobj.value)
            elif isinstance(eobj, esdl.StringItem):
                # part of DistributionKPI
                d = Data(dataset=ds)
                try:
                    string_label_distribution = eobj.eContainer()
                    distribution_kpi = string_label_distribution.eContainer()
                except Exception:
                    continue # ignore KPI if containers are not ok
                update_kpi_metadata(distribution_kpi, d)
                d.labels = d.labels if d.labels is not None else {}
                qau = check_qau(distribution_kpi.quantityAndUnit)
                main_kpi = distribution_kpi  # use main kpi (parent KPI) as name, calculate this here
                # calculate label prefix for sub kpis
                if 'KPI level' in d.labels:
                    level_num = d.labels['KPI level']
                    while level_num > 0:
                        level_num -= 1
                        main_kpi = distribution_kpi.eContainer()
                variable_name = f'KPI - {main_kpi.name} - {physical_q_to_str(qau)} [{unit_to_string(qau)}]'
                d.labels["Label"] = f'{distribution_kpi.name} - {eobj.label}' if distribution_kpi is not main_kpi else eobj.label
                d.value = eobj.value
            # TODO other distributions
            #elif isinstance(distribution, esdl.FromToDistribution):
            elif isinstance(eobj, esdl.Pipe):
                length = eobj.length
                diameter = eobj.diameter.name  # e.g. DN250
                d = Data(dataset=ds, value=length)
                d.region = eobj.area.name
                d.labels = {'Diameter': diameter, 'State': eobj.state.name}
                d.node = eobj.name or eobj.id
                d.technology = eobj.eClass.name
                d.sector = eobj.sector.name if eobj.sector else None
                if len(eobj.port) > 0:
                    d.input = eobj.port[0].carrier.name if eobj.port[0].carrier else None
                variable_name = "Pipe Length (m)"
                qau = esdl.QuantityAndUnitType(physicalQuantity=esdl.PhysicalQuantityEnum.LENGTH,
                                               unit=esdl.UnitEnum.METRE, description="Length in m")
            # variable_name and qau and d should be defined here
            if not variable_name:
                #variable_name = eobj.name if hasattr(eobj, 'name') else None
                #logger.debug(f"Ignoring {eobj.eClass.name}")
                continue
            variable: Variable = variables.get(variable_name, None)
            if variable is None:
                if variable_name is None:
                    logger.warn(f"Variable name is empty for {eobj}, ignoring")
                    continue
                variable = Variable(
                    name=variable_name,
                    unit=unit_to_string(qau),
                    quantity=qau.physicalQuantity.name if qau.physicalQuantity else None,
                    datatype=DataType.SINGLE_VALUE,
                )
                variables[variable.name] = variable
                data_list.append(variable)
            # update input description if necessary
            if d.input is not None and variable.input_description is None:
                variable.input_description = "Carrier"
            if d.output is not None and variable.output_description is None:
                variable.output_description = "Carrier"
            d.year = year  # defaults to current year
            variable.dataset = ds
            d.variable = variable
            data_list.append(d)
        data_list.append(ds)
        return data_list

    def update_filter_options(self, session:Session, dataset: DataSet):
        # get variables
        variables = session.scalars(select(Variable).where(Variable.dataset_id == dataset.id)).all()
        for v in variables:
            filter_options = {}
            v:Variable
            unique_sectors = filter_none(session.scalars(select(Data.sector).distinct().where(Data.variable_id == v.id).order_by(Data.sector)).all())
            unique_regions = filter_none(session.scalars(select(Data.region).distinct().where(Data.variable_id == v.id).order_by(Data.region)).all())
            unique_nodes = filter_none(session.scalars(select(Data.node).distinct().where(Data.variable_id == v.id).order_by(Data.node)).all())
            unique_to_nodes = filter_none(session.scalars(select(Data.to_node).distinct().where(Data.variable_id == v.id).order_by(Data.to_node)).all())
            unique_output = filter_none(session.scalars(select(Data.output).distinct().where(Data.variable_id == v.id).order_by(Data.output)).all())
            unique_input = filter_none(session.scalars(select(Data.input).distinct().where(Data.variable_id == v.id).order_by(Data.input)).all())
            unique_technology = filter_none(session.scalars(select(Data.technology).distinct().where(Data.variable_id == v.id).order_by(Data.technology)).all())
            unique_year = filter_none(session.scalars(select(Data.year).distinct().where(Data.variable_id == v.id).order_by(Data.year)).all())
            # get all label keys:
                # select distinct json_object_keys(labels) as keys from data where dataset_id=17;
                # per key get options: select distinct labels->>'Capability' as capability from data where dataset_id=17
            keys_list = session.scalars(select(literal_column("json_object_keys(labels)").label("keys")).distinct().select_from(Data).where(Data.variable_id == v.id)).all()
            for key in keys_list:
                print("-", key)
                #options_per_label_key = session.scalars(select(literal_column("labels->>'"+key+"'").label("options")).distinct().select_from(Data).where(Data.variable_id == v.id)).all()
                options_per_label_key = filter_none(session.scalars(select(Data.labels[key].as_string().label("options")).distinct().select_from(Data).where(Data.variable_id == v.id)).all())
                filter_options[key] = FilterOptions(options=options_per_label_key, column="labels", key=key)

            if len(unique_sectors) > 0 and unique_sectors[0] is not None:
                filter_options['Sector'] = FilterOptions(options=list(unique_sectors), column='sector', key=None)
            if len(unique_regions) > 0 and unique_regions[0] is not None:
                filter_options['Region'] = FilterOptions(options=list(unique_regions), column='region', key=None)
            if len(unique_nodes) > 0 and unique_nodes[0] is not None:
                filter_options['Node'] = FilterOptions(options=unique_nodes, column='node', key=None)
            if len(unique_to_nodes) > 0 and unique_to_nodes[0] is not None:
                filter_options['Flow to Node'] = FilterOptions(options=unique_to_nodes, column='to_node', key=None)
            if len(unique_output) > 0 and unique_output[0] is not None:
                fo = FilterOptions(options=unique_output, column='output', key=None)
                if v.output_description:
                    filter_options[v.output_description] = fo
                else:
                    filter_options['Output'] = fo
            if len(unique_input) > 0 and unique_input[0] is not None:
                fo = FilterOptions(options=unique_input, column='input', key=None)
                if v.input_description:
                    filter_options[v.input_description] = fo
                else:
                    filter_options['Input'] = fo
            if len(unique_technology) > 0 and unique_technology[0] is not None:
                filter_options['Technology'] = FilterOptions(options=unique_technology, column='technology', key=None)
            if len(unique_year) > 0 and unique_year[0] is not None:
                filter_options['Year'] = FilterOptions(options=unique_year, column='year', key=None)

            v.filter_options = filter_options
            session.add(v)
            session.commit()


    def query_data(self, session: Session):
        with self.flask_app.app_context():
            print("Query data")
            datasets = session.query(DataSet).all()
            for d in datasets:
                print(f"{d.name} @ {d.created}")

