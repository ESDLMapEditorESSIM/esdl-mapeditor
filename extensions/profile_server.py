#  This work is based on original code developed and copyrighted by TNO 2025.
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

from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import List, Any

from influxdb import InfluxDBClient
from logging import getLogger

from esdl import esdl
from esdl.profiles.data_configurations.credentials import Credentials
from esdl.profiles.datatableprofilemanager import DataTableProfileManager
from esdl.profiles.profilemanager import ProfileType
from utils.datetime_utils import parse_date

logger = getLogger(__name__)


class ProfileServerTypeEnum(Enum):
    INFLUXDB = "INFLUXDB"
    POSTGRESQL = "POSTGRESQL"


@dataclass
class InfluxDBConnectionSettings:
    host: str
    port: int
    username: str
    password: str
    database: str
    ssl: bool = False

@dataclass
class PostgreSQLConnectionSettings:
    host: str
    port: int
    username: str
    password: str
    database: str
    ssl: bool = False


class ProfileServer(ABC):
    def __init__(self):
        self.data = None
        self.client = None


class PostgreSQLServer(ProfileServer):
    def __init__(self, connection_settings: PostgreSQLConnectionSettings):
        super().__init__()

        self.profile_header = None
        self.profile_data_list = None
        self.profile_type: ProfileType = None

        self.connection_settings = connection_settings
        self.data_table_profile_manager = None

    def connect(self):
        configuration = esdl.DatabaseConfiguration(
            id="postgres_profile_server_mapeditor",
            database=self.connection_settings.database,
            type=esdl.DatabaseTypeEnum.POSTGRESQL,
            host=self.connection_settings.host,
            port=self.connection_settings.port,
            tls=self.connection_settings.ssl,
        )
        credentials_dict = Credentials.create_dict(
            id="postgres_profile_server_mapeditor",
            username=self.connection_settings.username,
            password=self.connection_settings.password
        )

        self.data_table_profile_manager = DataTableProfileManager()
        self.data_table_profile_manager.data_table_profile.configuration = configuration
        self.data_table_profile_manager.add_credential(credentials_dict)

    def convert_data(self, data, table_name):
        """
        Converts the data into a format that is required by the Postgres database write method

        Input data has format: [{
            "time": "<<datetime string>>",
            "fields": {
                "<<fieldname_1>>": "<<value_1>>",
                ...
            }
        }]
        """
        if len(data) > 0:
            self.profile_header = list()
            self.profile_data_list = list()

            # Use the fields from the first element in the data list as information for the header
            self.profile_header = ["datetime"]
            self.profile_header.extend([k for k in data[0]["fields"].keys()])

            for d in data:
                profile_data_element = list()
                profile_data_element.append(parse_date(d["time"]))

                for k, v in d["fields"].items():
                    profile_data_element.append(v)
                self.profile_data_list.append(profile_data_element)

            self.profile_type = ProfileType.DATETIME_LIST

            # TODO: fix this fixed QaU
            self.data_table_profile_manager.data_table_profile.profileQuantityAndUnit = \
                esdl.QuantityAndUnitType(description="Ratio", id="Ratio_unitless",
                                         physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                                         unit=esdl.UnitEnum.PERCENT)

            self.data_table_profile_manager.data_table_profile.tableName = table_name
            self.data_table_profile_manager.set_profile(self.profile_header, self.profile_data_list, self.profile_type)

    def write_data(self):
        self.data_table_profile_manager.save()


class InfluxDBServer(ProfileServer):
    def __init__(self, connection_settings: InfluxDBConnectionSettings):
        super().__init__()

        self.connection_settings = connection_settings

    def connect(self):
        """
        Connects to the InfluxDB database and creates database if database does not exist yet.
        """
        self.client = InfluxDBClient(
            host=self.connection_settings.host,
            port=self.connection_settings.port,
            username=self.connection_settings.username,
            password=self.connection_settings.password,
            database=self.connection_settings.database,
            ssl=self.connection_settings.ssl
        )

        available_databases = self.client.get_list_database()
        # if database not in client.get_list_database():
        if not (any(db['name'] == self.connection_settings.database for db in available_databases)):
            logger.debug('Database does not exist, creating a new one')
            self.client.create_database(self.connection_settings.database)

    def convert_data(self, data: List[dict[str, Any]], measurement: str):
        """
        Converts data to a format that is compatible with InfluxDB
        """
        self.data = list()

        for d in data:
            self.data.append({
                'measurement': measurement,
                **d,
            })

    def drop_measurement(self, measurement: str) -> None:
        """
        Drop an existing measurement before replacing all profile rows.
        """
        self.client.drop_measurement(measurement)

    def write_data(self):
        self.client.write_points(points=self.data, database=self.connection_settings.database, batch_size=100)
