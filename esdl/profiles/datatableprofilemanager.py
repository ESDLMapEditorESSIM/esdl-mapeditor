#  This work is based on original code developed and copyrighted by TNO 2023.
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
from os import environ
from typing import Dict, List
from uuid import uuid4

from pyecore.ecore import EDate

import esdl
from esdl import DataTableProfile
from esdl.profiles.data_configurations.credentials import Credentials
from esdl.profiles.data_configurations.postgresql import PostgresqlConfiguration, DataTableMetaData
# For mapeditor: commented out as no ExcelProfileManger is available
#from esdl.profiles.excelprofilemanager import ExcelProfileManager
from esdl.profiles.profilemanager import ProfileManager, ProfileType, NoProfileLoadedExecption

global_credentials: Dict[str, Credentials] = {}

# add a default credential based on hostname based on environmental variables
if environ.get("DB_HOST", None):
    host = environ.get('DB_HOST', 'localhost')
    global_credentials[host] = Credentials(username=environ.get("DB_USER", None),
                                           password=environ.get("DB_PASSWORD", None))
    print(f"Detected DB credentials for {host}")


class DataTableProfileManager(ProfileManager):
    """
    InfluxDBProfileManager: manages profile data that can be loaded from and saved to InfluxDB (v1 only).
    InfluxDBProfileManager is a subclass of ProfileManager, so it also provides functionality to convert from/to
    different ESDL profiles and to load/save to CSV
    """
    data_table_profile: esdl.DataTableProfile
    metadata: List[DataTableMetaData]

    def __init__(self, data_table_profile: esdl.DataTableProfile = None, source_profile=None):
        """
        Constructor of the InfluxDBProfileManager

        :param data_table_profile: the DataTableProfile to load
        :param source_profile: the source profile of which the data is copied into this profiles manager instance
        """
        super().__init__()
        self.metadata = []
        self.profile_type = ProfileType.DATETIME_LIST

        if data_table_profile:
            self.data_table_profile = data_table_profile
        else:
            self.data_table_profile = esdl.DataTableProfile()

        if source_profile:
            self.convert(source_profile)

    def add_credential(self, credentials_dict: Dict[str, Credentials]):
        global_credentials.update(credentials_dict)

    def set_data_table_profile(self, data_table_profile: esdl.DataTableProfile):
        self.data_table_profile = data_table_profile

    def load_database_configuration(self, configuration: esdl.DatabaseConfiguration = None,
                                    credentials_dict: dict[str, Credentials] = None):
        """
        Loads profile information from a database configuration into
        profile_info and profile_header

        :param configuration: the database configuration, optional, otherwise
                            the one provided in the constructor is used
        :param credentials_dict: optional credentials dict to use to connect to the database
        :return: None
        """
        if not configuration:
            configuration = self.data_table_profile.configuration
        if not configuration:
            raise InvalidDataConfiguration("Missing configuration of DataTableProfile")

        if not credentials_dict:
            credentials_dict = global_credentials

        self.clear_profile()
        self.profile_type = ProfileType.DATETIME_LIST

        if configuration.type == esdl.DatabaseTypeEnum.POSTGRESQL:
            # handle postgres
            postgres = PostgresqlConfiguration(self.data_table_profile, credentials_dict)
            self.profile_data_list, self.profile_header, self.metadata = postgres.load_data()
            postgres.disconnect()
            if len(self.profile_data_list) > 0:
                self.num_profile_items = len(self.profile_data_list[0])
                if self.num_profile_items > 0:
                    dt_index = self.get_profile_name_index(self.data_table_profile.datetimeColumnName)
                    self.start_datetime = self.profile_data_list[0][dt_index]
                    self.end_datetime = self.profile_data_list[-1][dt_index]
        else:
            raise UnsupportedDataConfiguration(
                f"DataConfiguration of type {configuration.type.name} is not yet supported")

    @staticmethod
    def load(data_table_profile: esdl.DataTableProfile,
             credentials_dict: dict[str, Credentials] = None) -> 'DataTableProfileManager':
        """
        Static method to create an instance of DataTableProfileManager using an esdl.DataTableProfile. The data
        referenced to in
        the profile is loaded from the associated DataConfiguration (e.g. DatabaseConfiguration or FileConfiguration)

        Note:
        - uri without extension is used as tableName for CSV files if no tableName is given

        :param data_table_profile: esdl.DataTableProfile that is used as an input profile
        :param credentials_dict: dictionary of credentials to use for authentication with ['id' -> Credentials] mapping, where
        'id' refers to the id of the AbstractDataConfiguration that belongs to these credentials
        """

        if not credentials_dict:
            # use global credentials list
            credentials_dict = global_credentials

        configuration = data_table_profile.configuration

        if configuration is None:
            raise InvalidDataConfiguration("No DataConfiguration provided")
        if isinstance(configuration, esdl.DatabaseConfiguration):
            dtpman = DataTableProfileManager(data_table_profile)
            dtpman.load_database_configuration(configuration, credentials_dict)
            return dtpman
        elif isinstance(configuration, esdl.FileConfiguration):
            # FOR MAPEDITOR, commented out this EXCEL option, as the excel profile manager is not available
            # if configuration.type == esdl.FileTypeEnum.EXCEL:
            #     epm = ExcelProfileManager()
            #     # tableName is used as sheet name (see ecore model documentation)
            #     # NOTE: load_excel ignores currently datetimeColumnName and columnName
            #     epm.load_excel(configuration.uri, data_table_profile.tableName)
            #     dtpman = DataTableProfileManager(data_table_profile, epm)
            #     return dtpman
            #el
            if configuration.type == esdl.FileTypeEnum.CSV:
                dtpman = DataTableProfileManager(data_table_profile)
                dtpman.load_csv(configuration.uri)
                if not data_table_profile.tableName:
                    data_table_profile.tableName = configuration.uri.split('.')[0] if configuration.uri else "csv_file"
                    data_table_profile.tableName = data_table_profile.tableName.split('/')[-1]
                    data_table_profile.tableName = data_table_profile.tableName.split('\\')[-1]
                return dtpman
            else:
                raise UnsupportedDataConfiguration(
                    f"DataConfiguration of type {configuration.type.name} is not yet supported")
        else:
            raise UnsupportedDataConfiguration(
                f"DataConfiguration {configuration} is not yet supported")

    def get_data_table_profile(self, profile_name: str = None, table_name: str = None,
                               schema_name: str = None) -> DataTableProfile | list[DataTableProfile]:
        """Creates an esdl.DataTableProfile instance that refers to the data loaded in this ProfileManager
        :param profile_name: name of the profile (one of the columns retrieved from the database), if None all will be returned
        :param table_name: name of the table, if None the value of self.data_table_profile.tableName will be used
        :param schema_name: name of the schema, if required. Defaults to None
        """

        if len(self.profile_header) == 0:
            raise NoProfileLoadedExecption("No profile loaded, header is empty.")

        datetime_columnname = self.profile_header[0]
        if table_name is None:
            table_name = self.data_table_profile.tableName

        if profile_name: # return only one
            profile_name_index = self.get_profile_name_index(profile_name)
            profile_name = self.profile_header[profile_name_index]

            self.data_table_profile = esdl.DataTableProfile(
                id=str(uuid4()),
                name=profile_name,
                tableName=table_name,
                datetimeColumnName=datetime_columnname,
                columnName=profile_name,
                schema=schema_name,
                startDate=EDate.from_string(self.start_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f%z')),
                endDate=EDate.from_string(self.end_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f%z')),
            )
            if self.metadata and self.metadata[profile_name_index]:
                self.data_table_profile.profileQuantityAndUnit = self.metadata[profile_name_index].qau
                self.data_table_profile.name = self.metadata[profile_name_index].name
            return self.data_table_profile
        else:
            dtp_list = []
            for i, column in enumerate(self.profile_header[1:], start=1):
                dtp = esdl.DataTableProfile(
                    id=str(uuid4()),
                    name=profile_name,
                    tableName=table_name,
                    datetimeColumnName=datetime_columnname,
                    columnName=column,
                    schema=schema_name,
                    startDate=EDate.from_string(self.start_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f%z')),
                    endDate=EDate.from_string(self.end_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f%z')),
                )
                dtp_list.append(dtp)
                if self.metadata and self.metadata[i]:
                    dtp.profileQuantityAndUnit = self.metadata[i].qau
                    dtp.name = self.metadata[i].name
            return dtp_list

    # def save_tags(self, table: str, column_names: list, schema: str = None, tags: dict = None):
    #     """
    #     Saves profile information to InfluxDB
    #
    #     :param table: name of the table where the data must be written to. Table is created when not existing
    #     :param column_names: list of the columns that should be written
    #     :param tags: dictionary with tags and tag values, that should be used when writing this data in a JSON column
    #                 in the database
    #     :param schema: name of the schema, if required.
    #     :return: an esdl.DataTableProfile instance or a list of esdl.DataTableProfile instances in case multiple fields
    #              were specified, with proper references to the data in the database
    #     """
    #     pass

    def save(self, credentials_dict: dict[str, Credentials] = None):
        """
        Saves the current datatable profile to the database
        :return: Data written in the database and an esdl.DataTableProfile that reflects this.
        """

        if not credentials_dict:
            credentials_dict = global_credentials

        if self.data_table_profile.configuration.type == esdl.DatabaseTypeEnum.POSTGRESQL:
            # handle postgres
            postgres = PostgresqlConfiguration(self.data_table_profile, credentials_dict)
            postgres.save_data(self.profile_data_list, self.profile_header)
            postgres.disconnect()
        else:
            raise UnsupportedDataConfiguration(
                f"DataConfiguration {self.data_table_profile.configuration.type.name} is not (yet) supported")


class NoDataException(Exception):
    """Thrown when no profile data can be written to Postgres"""
    pass


class WrongFilterFormatException(Exception):
    """Thrown when filter specification in ESDL profile cannot be parsed"""
    pass

class InvalidDataConfiguration(Exception):
    """Thrown when there is no or invalid DataConfiguration"""
    pass


class UnsupportedDataConfiguration(Exception):
    """Thrown when this DataConfiguration is not supported"""
    pass
