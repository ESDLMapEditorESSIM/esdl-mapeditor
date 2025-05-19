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
import json
import logging
import statistics
from datetime import datetime
from enum import Enum
from typing import Any, TypedDict, List, Dict, Optional, Sequence, Iterable

import pandas as pd
from flask import Flask
from flask_socketio import SocketIO
from pandas import DataFrame
from sqlalchemy import select, delete, column
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql import text, func

import esdl
from esdl.processing.ESDLAsset import get_asset_capability_type
from esdl.processing.ESDLQuantityAndUnits import unit_to_string
from extensions.data_manager import db
from extensions.data_manager.data_manager_message import (ChartType,
                                                          MetadataUpdateRequestBody,
                                                          MetadataDeleteRequestBody,
                                                          MetadataOperationResp,
                                                          GetVariablesRequestBody,
                                                          GetColumnsRequestBody,
                                                          QueryRequestBody)
from extensions.data_manager.db_interaction import create_db_tables, get_db_driver_type, DriverType, create_db, drop_db, \
    drop_db_tables
from extensions.data_manager.db_model import DataSet, Variable, DataType, Data, BaseModel
from extensions.session_manager import get_session, get_project_manager
from src import settings
from src.log import get_logger

logger = get_logger(__name__)


class ESDLScope(Enum):
    ALL = 0
    PROFILE = 1
    KPI = 2

class MetadataCRUDStatus(Enum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"

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
    # logger.debug('Handle KPI ', kpi_name=kpi.name)
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
        labels['Area type'] = container.type.name

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
    # TODO: Handle cases when multiple profile references are 
    # presented or the profile is a 'relative profile'
    # See discussion: https://ci.tno.nl/gitlab/GEIS/esdl-mapeditor/-/merge_requests/39#note_754191
    while isinstance(qau, esdl.QuantityAndUnitReference):
        qau = qau.reference
    if not qau:
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
    d = Data(dataset=ds, value=None) # Default value to None
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
        labels['Area type'] = area.type.name
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

    if d.value is None:
        logger.warning(f"Data value of {d.variable} [{d.dataset}] is None")
        # To handle None value if required...

    return d, qau, variable_name

def preprocess_column(column_name: str) -> Any:
    if 'sqlite' in settings.SQLALCHEMY_DATABASE_URI:
        db_engine_driver = "sqlite"
    else:
        db_engine_driver = "postgresql"
    if '/' in column_name:
        key_name = column_name.split('/')[1]
        if db_engine_driver == "sqlite":
            return func.json_extract(Data.labels, f"$.{key_name}").label(column_name)
        else:
            return Data.labels[key_name].label(column_name)
    else:
        return column(column_name)

class DataManager:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self):
        logger.info("Registering DataManager extension")
        sqllogger = logging.getLogger("sqlalchemy.engine")
        sqllogger.setLevel(logging.ERROR)
        logger.info(f"Connecting to Data Manager database using: {settings.SQLALCHEMY_DATABASE_URI}")
        self.flask_app.config.update({"SQLALCHEMY_DATABASE_URI": settings.SQLALCHEMY_DATABASE_URI})
        db.init_app(self.flask_app)  # init SQLAlchemy

        # init database
        with self.flask_app.app_context():
            db_driver_type = get_db_driver_type()
            if db_driver_type == DriverType.SQLITE:
                drop_db(db_url=self.flask_app.config["SQLALCHEMY_DATABASE_URI"],
                        app_instance_path=self.flask_app.instance_path)
                create_db(self.flask_app.config["SQLALCHEMY_DATABASE_URI"])
            else:
                # The sqlite approach doesn't work well with Postgres, so just dropping the tables.
                drop_db_tables()
                create_db_tables()

        @self.socketio.on("datamanager/metadata/add_update", namespace="/esdl")
        def _add_or_update_metadata(params: Dict) -> str:
            req_body = MetadataUpdateRequestBody(**params)
            session_owner = get_session("user-email")
            resp = self.add_or_update_metadata(db.session, variant_id=req_body.es_id, owner=session_owner)
            return json.dumps(resp.__dict__)
        
        @self.socketio.on("datamanager/metadata/delete", namespace="/esdl")
        def _delete_dataset(params: Dict) -> str:
            req_body = MetadataDeleteRequestBody(**params)
            session_owner = get_session("user-email")
            resp = self.delete_dataset(db.session, dataset_name=req_body.dataset_name, owner=session_owner)
            return json.dumps(resp.__dict__)

        @self.socketio.on("datamanager/variants", namespace="/esdl")
        def _get_variants() -> list:
            pm = get_project_manager()
            variants = pm.get_variants()
            response = []
            for variant in variants:
                response.append({
                    'id': variant.id,
                    'name': variant.name,
                    'description': variant.description,
                })
            return response

        @self.socketio.on("datamanager/datasets", namespace="/esdl")
        def _get_datasets() -> list:
            session_owner = get_session("user-email")
            return self.get_datasets(db.session, owner=session_owner)
        
        @self.socketio.on("datamanager/variables", namespace="/esdl")
        def _get_variables(params: Dict) -> list:
            req_body = GetVariablesRequestBody(**params)
            return self.get_variables(db.session, dataset_ids=req_body.dataset_ids)
        
        @self.socketio.on("datamanager/columns", namespace="/esdl")
        def _get_columns(params: Dict) -> dict:
            req_body = GetColumnsRequestBody(**params)
            return self.get_columns(db.session, dataset_ids=req_body.dataset_ids, variable_name=req_body.variable_name)
        
        @self.socketio.on("datamanager/query", namespace="/esdl")
        def _query(params: Dict) -> list:
            params['chart_type'] = ChartType(params['chart_type'])
            req_body = QueryRequestBody(**params)
            return self.query(db.session,
                              dataset_ids=req_body.dataset_ids,
                              variable_name=req_body.variable_name,
                              group_by=req_body.group_by,
                              filters=req_body.filters,
                              chart_type=req_body.chart_type)

    def process_esdl(self, es: esdl.EnergySystem, owner: str) -> List[BaseModel]:
        """
        Processes the ESDL and returns a list of DataSet, Variable, and Data as database entries.

        :param es: ecore EObject  (e.g. EnergySystem)
        :param owner: The owner/email of the dataset that is created

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

        ds = DataSet(name=es.name, energy_system_id=es.id, created_by=owner, description=es.description, model="Unknown")

        for eobj in es.eAllContents():
            #variable_name = eobj.name if hasattr(eobj, 'name') else None
            variable_name = None
            if isinstance(eobj, esdl.SingleValue) or isinstance(eobj, esdl.TimeSeriesProfile):
                # logger.debug(f"Handling {eobj.eClass.name}/{eobj.name}")
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
            elif isinstance(eobj, esdl.Producer) or isinstance(eobj, esdl.Consumer) or isinstance(eobj, esdl.Conversion):
                power = eobj.power
                d = Data(dataset=ds, value=power)
                d.labels = {'Power': power, 'State': eobj.state.name}
                d.region = self.find_region(eobj, d.labels)
                d.node = eobj.name or eobj.id
                d.technology = eobj.eClass.name
                d.sector = eobj.sector.name if eobj.sector else None
                if len(eobj.port) > 0:
                    d.input = eobj.port[0].carrier.name if eobj.port[0].carrier else None
                variable_name = "Power (W)"
                qau = esdl.QuantityAndUnitType(physicalQuantity=esdl.PhysicalQuantityEnum.POWER,
                                               unit=esdl.UnitEnum.WATT, description="Power in W")

            elif isinstance(eobj, esdl.Storage) or isinstance(eobj, esdl.Transport):
                capacity = eobj.capacity
                d = Data(dataset=ds, value=capacity)
                d.labels = {'Capacity': capacity, 'State': eobj.state.name}
                d.region = self.find_region(eobj, d.labels)
                d.node = eobj.name or eobj.id
                d.technology = eobj.eClass.name
                d.sector = eobj.sector.name if eobj.sector else None
                if len(eobj.port) > 0:
                    d.input = eobj.port[0].carrier.name if eobj.port[0].carrier else None
                if isinstance(eobj, esdl.Storage):
                    variable_name = "Capacity (J)"
                    qau = esdl.QuantityAndUnitType(physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                                                   unit=esdl.UnitEnum.JOULE, description="Capacity in J")
                else:
                    variable_name = "Capacity (W)"
                    qau = esdl.QuantityAndUnitType(physicalQuantity=esdl.PhysicalQuantityEnum.POWER,
                                                   unit=esdl.UnitEnum.WATT, description="Capacity in W")

                if isinstance(eobj, esdl.Pipe):
                    length = eobj.length
                    diameter = eobj.diameter.name  # e.g. DN250
                    d = Data(dataset=ds, value=length)
                    d.labels = {'Diameter': diameter, 'State': eobj.state.name}
                    d.region = self.find_region(eobj, d.labels)
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

    def find_region(self, eobj:esdl.Asset, labels: dict):
        if not eobj.area:  # asset is in a AbstractBuilding or compoundAsset
            parent = eobj.containingAsset or eobj.containingBuilding
            region = parent.area.name
            labels['Area scope'] = parent.area.scope.name
        else:
            region = eobj.area.name
            labels['Area scope'] = eobj.area.scope.name
        return region

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

            # A workaround to extract Data.labels column (JSON) keys in SQLite as SQLite does not support json_object_keys
            db_driver_type = get_db_driver_type()
            if db_driver_type == DriverType.SQLITE:
                keys_query = text("""
                    SELECT DISTINCT json_each.key AS keys
                    FROM Data, json_each(Data.labels)
                    WHERE Data.variable_id = :variable_id
                """)
                keys_list = session.execute(keys_query, {'variable_id': v.id}).scalars().all()
            else:
                # PostgreSQL version using text() for raw SQL
                keys_query = text("""
                    SELECT DISTINCT jsonb_object_keys(labels) AS keys
                    FROM "data"
                    WHERE variable_id = :variable_id
                """)
                keys_list = session.execute(keys_query, {'variable_id': v.id}).scalars().all()

            for key in keys_list:
                #print("-", key)
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

    def add_or_update_metadata(self, session: Session, variant_id: str, owner: str) -> MetadataOperationResp:
        """
        Adds or updates DataManager metadata for a given energy system.
        
        :param session: SQLAlchemy session object for database operations.
        :param variant_id: The ID of the variant of the energy system to be added or updated.
        :param owner: Session owner (email)

        :return: MetadataOperationResp contains status and message strings
        """
        log = logger.bind(variant_id=variant_id, owner=owner)
        log.info(f"Adding or updating variant to metadata.")
        
        pm = get_project_manager()
        variant = pm.get_variant_by_id(variant_id)
        log.info("Getting or creating variant snapshot")
        es = pm.get_or_create_variant_snapshot(variant)
        log.info("Retrieved variant snapshot", es_id=es.id)

        if variant is None:
            msg = f"Variant with ID {variant_id} not found."
            log.error(msg)
            return MetadataOperationResp(MetadataCRUDStatus.ERROR.value, msg)
                
        ds_exists = self.same_ds_exists(session, es_id=es.id, dataset_name=es.name, owner=owner)

        warning_msg = ""
        to_overwrite = False
        to_append = False # True if the new dataset has the same es_id but with a different name
        if ds_exists:
            # The same dataset is found, overwrites the existing one.
            warning_msg = f"Dataset {es.name} [{variant_id}] created by {owner} already exists. "
            resp = self.delete_dataset(session, dataset_name=es.name, owner=owner)
            if resp.status == MetadataCRUDStatus.SUCCESS.value:
                to_overwrite = True
            else:
                error_msg = f"{warning_msg} Failed to delete existing dataset: {resp.message}"
                log.error(error_msg)
                return MetadataOperationResp(MetadataCRUDStatus.ERROR.value, error_msg)
        else:
            # Checks if the new record is unique in 'name' + 'owner' (to fulfill data model unique constraint)
            # If not, aborts the operation and returns an error message.
            if self.ds_name_and_owner_is_not_unique(session, dataset_name=es.name, owner=owner):
                error_msg = f"Failed to add dataset {es.name} [{variant_id}]. The name must be unique. Please rename ESDL and try again."
                log.error(error_msg)
                return MetadataOperationResp(MetadataCRUDStatus.ERROR.value, error_msg)
            elif self.ds_with_same_id_but_different_name_exists(session, es_id=variant_id, dataset_name=es.name, owner=owner):
                to_append = True

        try:
            tables = self.process_esdl(es=es, owner=owner)
            session.add_all(tables)
            session.commit()
            # Extracts the DataSet instance from the tables list for postprocessing.
            ds = [d for d in tables if isinstance(d, DataSet)][0]
            self.update_filter_options(session, ds)
            
            if to_overwrite:
                warning_msg += "The dataset is now overwritten with the latest changes."
                log.warning(warning_msg)
                return MetadataOperationResp(MetadataCRUDStatus.WARNING.value, warning_msg)
            elif to_append:
                append_msg = f"Dataset with the same id [{variant_id}] already exists. Successfully appended as a new dataset {es.name}."
                log.warning(append_msg)
                return MetadataOperationResp(MetadataCRUDStatus.WARNING.value, append_msg)
            else:
                success_msg = f"Dataset {es.name} [{variant_id}] has been successfully added."
                log.info(success_msg)
                return MetadataOperationResp(MetadataCRUDStatus.SUCCESS.value, success_msg)
        except Exception as e:
            session.rollback()
            if isinstance(e, IntegrityError):
                msg = f"Failed to add dataset {es.name} [{variant_id}]. The name must be unique. Please rename ESDL and try again."
            else:
                msg = f"An error occurred while adding or updating metadata: {e}"
                import traceback
                traceback.print_exc()
            log.exception(msg)
            return MetadataOperationResp(MetadataCRUDStatus.ERROR.value, msg)

    @staticmethod
    def same_ds_exists(session: Session, es_id: str, dataset_name: str, owner: str) -> bool:
        exists = session.query(DataSet)\
            .where(DataSet.energy_system_id == es_id)\
            .where(DataSet.name == dataset_name)\
            .where(DataSet.created_by == owner)\
            .first() is not None
        return exists
    
    @staticmethod
    def ds_name_and_owner_is_not_unique(session: Session, dataset_name: str, owner: str) -> bool:
        exists = session.query(DataSet)\
            .where(DataSet.name == dataset_name)\
            .where(DataSet.created_by == owner)\
            .first() is not None
        return exists
    
    @staticmethod
    def ds_with_same_id_but_different_name_exists(session: Session, es_id: str, dataset_name: str, owner: str) -> bool:
        exists = session.query(DataSet)\
            .where(DataSet.energy_system_id == es_id)\
            .where(DataSet.name != dataset_name)\
            .where(DataSet.created_by == owner)\
            .first() is not None
        return exists
    
    def delete_dataset(self, session: Session, dataset_name: Optional[str], owner: str) -> MetadataOperationResp:
        """
        Deletes dataset(s) by name and owner, with cascading deletions on related records.

        :param session: SQLAlchemy session object for database operations.
        :param dataset_name: The name of the dataset to delete; if None, all datasets by the owner will be deleted.
        :param owner: The owner of the dataset(s) to delete.

        :return: MetadataOperationResp contains status and message strings
        """
        logger.info(f"Deleting dataset(s) created by {owner} with name {dataset_name}.")
        try:
            query = session.query(DataSet).where(DataSet.created_by == owner)
            if dataset_name:
                query = query.where(DataSet.name == dataset_name)
            
            ds_to_delete = query.all()
            if len(ds_to_delete) == 0:
                msg = f"No dataset(s) found with name {dataset_name} created by {owner}."
                logger.warning(msg)
                return MetadataOperationResp(MetadataCRUDStatus.WARNING.value, msg)

            deleted_ds = []
            for ds in ds_to_delete:
                # TODO: Update data model to enable cascading delete
                session.execute(delete(Data).where(Data.dataset_id == ds.id))
                session.execute(delete(Variable).where(Variable.dataset_id == ds.id))
                session.execute(delete(DataSet).where(DataSet.id == ds.id))
                deleted_ds.append(f"{ds.name} [{ds.energy_system_id}]")
            session.commit()
            msg = f"Dataset(s) {', '.join(deleted_ds)} created by {owner} successfully deleted."
            logger.info(msg)
            return MetadataOperationResp(MetadataCRUDStatus.SUCCESS.value, msg)
        except Exception as e:
            session.rollback()
            msg = f"An error occurred while deleting dataset(s): {e}"
            logger.error(msg)
            return MetadataOperationResp(MetadataCRUDStatus.ERROR.value, msg)

    def get_datasets(self, session: Session, owner: str) -> list:
        """
        Fetches and returns a list of dataset dictionaries created by the owner and ordered by their run_timestamp.
        """
        logger.info(f"Fetching DataManager datasets from owner: {owner}")
        response = []
        datasets: List[DataSet] = session.query(DataSet)\
                                    .where(DataSet.created_by == owner)\
                                    .order_by(DataSet.run_timestamp)\
                                    .all()
        for dataset in datasets:
            timestamp: datetime = dataset.run_timestamp
            response.append({
                'name': dataset.name,
                'id': dataset.id,
                'description': dataset.description,
                'run_timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        return response

    def get_variables(self, session: Session, dataset_ids: List[int]) -> list:
        """
        Fetches and returns a list of variable dictionaries from of the specified dataset IDs.
        """
        logger.info(f"Fetching DataManager variables from dataset ids: {dataset_ids}")
        response = []
        query = session.query(Variable)\
            .where(Variable.dataset_id.in_(dataset_ids))\
            .group_by(Variable.name, Variable.id, Variable.description, Variable.unit, Variable.datatype)\
            .order_by(Variable.name)

        variables: List[Variable] = query.all()
        for variable in variables:
            response.append({
                'name': variable.name,
                'id': variable.id,
                'dataset': variable.dataset.name,
                'description': variable.description,
                'unit': variable.unit,
                'datatype': variable.datatype.name
            })
        return response

    def get_columns(self, session: Session, dataset_ids: List[int], variable_name: str) -> dict:
        """
        Fetches and returns filter options for a specified variable from one or multiple datasets.
        """
        logger.info(f"Fetching DataManager columns from dataset ids: {dataset_ids} and variable: {variable_name}")

        filter_options = session.query(Variable.filter_options)\
            .where(Variable.dataset_id.in_(dataset_ids))\
            .where(Variable.name == variable_name)\
            .all()
        
        response = {}
        if len(filter_options) == 0:
            logger.warning(f"Filter options with variable {variable_name} and dataset_ids {dataset_ids} not found.")
        elif len(filter_options) == 1:
            response = filter_options[0].filter_options
        else:
            # Merge filter options
            merged = filter_options[0].filter_options
            for option in filter_options[1:]:
                filter = option.filter_options
                for key in merged.keys():
                    if key in filter:
                        merged[key]['options'] = list(set(merged[key]['options'] + filter[key]['options']))
                    else:
                        del merged[key]
            response = merged

        # Sorts the elements in the 'options' lists alphabetically.
        sorted_resp = {}
        for key, value in response.items():
            sorted_value = value.copy()
            if "options" in value and isinstance(value["options"], list):
                sorted_value['options'] = sorted(value['options'], key=lambda x: str(x))
            sorted_resp[key] = sorted_value

        return sorted_resp
    
    def query(self,
              session: Session,
              dataset_ids: List[int],
              variable_name: str,
              group_by: List[str],
              filters: Dict[str, List[str]],
              chart_type: ChartType) -> list:
        """
        Queries and returns traces of data based on the specified dataset IDs, variable name, grouping, and filters.

        Note that group_by is ordered: the first element goes on the X axis, the rest goes in the grouping.
        """
        logger.info(f"Querying {chart_type.value} chart traces with dataset_ids: \
                    {dataset_ids}, variable: {variable_name}, group_by: {group_by}, and filters: {filters}")
                
        if len(group_by) == 0:
            group_by = ['year']
        if len(group_by) == 1 and group_by[0] != 'year':
            group_by.insert(0, 'year')
        
        group_by_param = [DataSet.name] + [preprocess_column(group) for group in group_by]

        if 'datetime' in group_by:
            # TODO: refinement needed
            agg_func = func.avg
        else:
            agg_func = func.sum
        
        query = session.query(agg_func(Data.value).label('value'), *group_by_param)\
            .join(Variable, Variable.id == Data.variable_id).join(DataSet, Data.dataset_id == DataSet.id)\
            .where(Variable.name == variable_name)\
            .where(Variable.dataset_id.in_(dataset_ids))\
            .group_by(*group_by_param)
        
        for col, values in filters.items():
            values = [x for x in values if x is not None]   # if all options of a filter are selected, values is null
            if len(values) > 0:  # only filter when some of the values are selected, but not all.
                query = query.where(preprocess_column(col).in_(values))

        df = pd.read_sql_query(query.statement, session.get_bind())

        if chart_type == ChartType.TABLE:
            return self.process_table_trace(df)
        else:
            return self.process_bar_chart_trace(df, dataset_ids, variable_name, group_by)
    
    @staticmethod
    def process_table_trace(df: DataFrame) -> list:
        """
        Processes a DataFrame to create a table trace for visualization.
        """
        # Renames 'name' to 'dataset' and ensures it is the first column
        if 'name' in df.columns:
            df.rename(columns={ 'name' : 'dataset'}, inplace=True)
            dataset_col = df.pop('dataset')
            df.insert(0, 'dataset', dataset_col)

        # Ensures 'value' is the last column
        if 'value' in df.columns:
            val_col = df.pop('value')
            df.insert(len(df.columns), 'value', val_col)

        headerValues = []
        cellValues = []
        for col_name in df.columns.tolist():
            # Header values are formatted as [["column 1"], ["column 2"], ...]
            headerValues.append([f"{col_name}"])
            cellValues.append(df[col_name].tolist())
        
        # Returns table content and keeps minimal table formatting in the backend.  
        trace = [{
            'header': {
                'values': headerValues
            },
            'cells': {
                'values': cellValues
            }
        }]

        return trace
    
    # TODO: separate into profile and bar chart trace functions
    @staticmethod
    def process_bar_chart_trace(df: DataFrame,
                                dataset_ids: List[int],
                                variable_name: str,
                                group_by: List[str]) -> list:
        """
        Processes a DataFrame to create traces for a bar chart visualization.
        """
        traces = []
        if 'datetime' in group_by:  # profile data, so x-axis should have datetime as value
            # TODO: refinement needed
            if group_by == ['datetime'] and len(dataset_ids) == 1:
                # make sure we don't do a group by datetime: we get 8760 categories in the legend
                traces.append({
                    'name': variable_name,
                    'x': list(df['datetime']),
                    'y': list(df['value'])
                })
            else:
                group_by.remove('datetime')  # make sure we never group by datetime
                for name, group in df.groupby(by=group_by, as_index=False):
                    traces.append({
                        'name': f'{name[-2]} - {name[-1]}' if isinstance(name, tuple) else name,
                        'x': list(group['datetime']),
                        'y': list(group['value']),
                    })
        else:
            for name, group in df.groupby(by=group_by[-1], as_index=False):
                traces.append({
                    'name': name[-1] if isinstance(name, tuple) else name,
                    'x': [[str(x) for x in list(group['name'])], [str(x) for x in list(group[group_by[0]])]],
                    'y': list(group['value'])
                })

        return traces
