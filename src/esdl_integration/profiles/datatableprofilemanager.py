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
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from uuid import uuid4

from pyecore.ecore import EDate

import esdl
from esdl import DataTableProfile
from src.esdl_integration.profiles.credentials import Credentials
from src.esdl_integration.profiles.postgresql import (
    PostgresqlConfiguration,
    DataTableMetaData,
)
from esdl.profiles.profilemanager import (
    ProfileManager,
    ProfileType,
    NoProfileLoadedExecption,
)

# For mapeditor: commented out as no ExcelProfileManager is available
# from esdl.profiles.excelprofilemanager import ExcelProfileManager

global_credentials: Dict[str, Credentials] = {}

# add a default credential based on hostname based on environmental variables
if environ.get("DB_HOST", None):
    host = environ.get("DB_HOST", "localhost")
    global_credentials[host] = Credentials(
        username=environ.get("DB_USER", None), password=environ.get("DB_PASSWORD", None)
    )
    print(f"Detected DB credentials for {host}")


class DataTableProfileManager(ProfileManager):
    """
    DataTableProfileManager: manages profile data that can be loaded from and saved to Postgres or InfluxDB.
    DataTableProfileManager is a subclass of ProfileManager, so it also provides functionality to convert from/to
    different ESDL profiles and to load/save to CSV
    """

    data_table_profile: esdl.DataTableProfile
    metadata: List[DataTableMetaData]

    def __init__(
        self, data_table_profile: esdl.DataTableProfile = None, source_profile=None
    ):
        """
        Constructor of the DataTableProfileManager

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

    def load_database_configuration(
        self,
        configuration: esdl.DatabaseConfiguration = None,
        credentials_dict: dict[str, Credentials] = None,
    ):
        """
        Loads profile data from a database configuration into
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
            postgres = PostgresqlConfiguration(
                self.data_table_profile, credentials_dict
            )
            self.profile_data_list, self.profile_header, self.metadata = (
                postgres.load_data()
            )
            postgres.disconnect()
            if len(self.profile_data_list) > 0:
                self.num_profile_items = len(self.profile_data_list[0])
                if self.num_profile_items > 0:
                    dt_index = self.get_profile_name_index(
                        self.data_table_profile.datetimeColumnName
                    )
                    self.start_datetime = self.profile_data_list[0][dt_index]
                    self.end_datetime = self.profile_data_list[-1][dt_index]
        else:
            raise UnsupportedDataConfiguration(
                f"DataConfiguration of type {configuration.type.name} is not yet supported"
            )

    def get_profile_with_multiplier(
        self, column_based: bool = False
    ) -> List[List[float]]:
        """
        Return the loaded profile data with the configured multiplier applied to a column or all
        columns (if columnName is not set). The datetime column is returned unchanged as the first
        column.

        :param column_based: If True, return data grouped by column instead of row. If False, return row-based data.
        :return: A list of columns, where the first column is the datetime values and
                subsequent columns are scaled numeric data columns.
        :raises NoProfileLoadedExecption: If no profile data has been loaded.
        """

        if len(self.profile_header) == 0:
            raise NoProfileLoadedExecption("No profile loaded, header is empty.")

        # Default to 1.0 if not explicitly set.
        multiplier = self.data_table_profile.multiplier

        # Default to 'datetime' if not explicitly set.
        dt_col_name = self.data_table_profile.datetimeColumnName
        dt_index = self.profile_header.index(dt_col_name)

        if self.data_table_profile.columnName is not None:
            # A single column case
            col_names = [self.data_table_profile.columnName]
        else:
            # Multi-column mode: all columns except datetime
            col_names = [c for c in self.profile_header if c != dt_col_name]

        scaled_profile_data = []

        # Process row-based structure
        for row in self.profile_data_list:
            dt_value = row[dt_index]
            scaled_row = [dt_value]

            for col_name in col_names:
                col_index = self.profile_header.index(col_name)
                value = row[col_index]
                scaled_row.append(value * multiplier)

            scaled_profile_data.append(scaled_row)

        # Convert to column-based if requested
        if column_based:
            return [list(col) for col in zip(*scaled_profile_data)]

        return scaled_profile_data

    @staticmethod
    def load(
        data_table_profile: esdl.DataTableProfile,
        credentials_dict: dict[str, Credentials] = None,
    ) -> "DataTableProfileManager":
        """
        Static method to create an instance of DataTableProfileManager using an esdl.DataTableProfile. The data
        referenced in the profile is loaded from the associated DataConfiguration, such as a DatabaseConfiguration
        or FileConfiguration.

        :param data_table_profile: esdl.DataTableProfile that is used as an input profile
        :param credentials_dict: dictionary of credentials to use for authentication with ['id' -> Credentials] mapping,
         where 'id' refers to the id of the AbstractDataConfiguration that belongs to these credentials

        Note:
        - for FileConfigurations: uri without extension is used as tableName for CSV files if no tableName is given
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
            #     # TODO: load_excel ignores currently datetimeColumnName and columnName
            #     epm.load_excel(configuration.uri, data_table_profile.tableName)
            #     dtpman = DataTableProfileManager(data_table_profile, epm)
            #     return dtpman
            if configuration.type == esdl.FileTypeEnum.CSV:
                dtpman = DataTableProfileManager(data_table_profile)
                dtpman.load_csv(configuration.uri)
                if not data_table_profile.tableName:
                    data_table_profile.tableName = (
                        configuration.uri.split(".")[0]
                        if configuration.uri
                        else "csv_file"
                    )
                    data_table_profile.tableName = data_table_profile.tableName.split(
                        "/"
                    )[-1]
                    data_table_profile.tableName = data_table_profile.tableName.split(
                        "\\"
                    )[-1]
                return dtpman
            else:
                raise UnsupportedDataConfiguration(
                    f"DataConfiguration of type {configuration.type.name} is not yet supported"
                )
        else:
            raise UnsupportedDataConfiguration(
                f"DataConfiguration {configuration} is not yet supported"
            )

    @staticmethod
    def query(
        data_table_profile: esdl.DataTableProfile,
        credentials_dict: Optional[Dict[str, Credentials]],
        table_name: str,
        column_name: str,
        schema: Optional[str] = None,
        datetime_column_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        additional_filters: Optional[Dict[str, Any]] = None,
        multiplier: Optional[float] = None,
        downsample_bucket_sec: Optional[int] = None,
        column_based: bool = False,
    ) -> Tuple[List[List[float]], List[str], List[esdl.QuantityAndUnitType]]:
        """
        Query data from a PostgreSQL-backed DataTableProfile using the associated
        DatabaseConfiguration. This method acts as the high-level API for retrieving
        profile data, applying optional filtering, scaling, and downsampling.

        Data is NOT stored inside this class, but passed directly
        to the caller.

        :param data_table_profile: The esdl.DataTableProfile describing the data source and default query parameters.
        :param credentials_dict: Optional mapping of configuration ID → Credentials. If None, global credentials are used.
        :param table_name: Name of the database table to query.
        :param column_name: Name of the single value column to retrieve.
        :param schema: Optional schema name. If None, the default schema is used.
        :param datetime_column_name: Optional override for the datetime column name. If None, the profile's datetime column is used.
        :param start_date: Optional start datetime for filtering.
        :param end_date: Optional end datetime for filtering.
        :param additional_filters: Optional (key, value) set of additional filters applied in the SQL WHERE clause.
        :param multiplier: Optional scaling factor applied to the value column. If None, the profile's default multiplier is used.
        :param downsample_bucket_sec: Optional bucket size (in seconds) for time-based downsampling using AVG().
        :param column_based: If True, results are returned column-based instead of row-based.

        :return: Tuple with: List of data (column-based if configured), header names,
                QuantityAndUnit if available for each header
        """
        if not credentials_dict:
            # use global credentials list
            credentials_dict = global_credentials

        configuration = data_table_profile.configuration
        if isinstance(configuration, esdl.DatabaseConfiguration):
            if configuration.type == esdl.DatabaseTypeEnum.POSTGRESQL:
                postgres = PostgresqlConfiguration(data_table_profile, credentials_dict)

                dt_column_name = (
                    datetime_column_name
                    if datetime_column_name is not None
                    else data_table_profile.datetimeColumnName
                )

                profile_data_list, profile_header, metadata = postgres.load_data_custom(
                    schema=schema,
                    table_name=table_name,
                    datetime_column_name=dt_column_name,
                    column_name=column_name,
                    start_date=start_date,
                    end_date=end_date,
                    additional_filters=additional_filters,
                    multiplier=multiplier,
                    downsample_bucket_sec=downsample_bucket_sec,
                    column_based=column_based,
                )
                qaus = [m.qau if m else None for m in metadata]
                postgres.disconnect()
                return profile_data_list, profile_header, qaus
            elif configuration.type == esdl.DatabaseTypeEnum.INFLUXDB:
                # TODO: support Influxdb
                pass
            else:
                raise UnsupportedDataConfiguration(
                    f"DataConfiguration of type {configuration.type.name} "
                    f"is not yet supported for direct querying"
                )
        else:
            raise UnsupportedDataConfiguration(
                f"DataConfiguration of type {configuration.type.name} "
                f"is not yet supported for direct querying"
            )

    def get_data_table_profile(
        self, profile_name: str = None, table_name: str = None, schema_name: str = None
    ) -> DataTableProfile | list[DataTableProfile]:
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

        if profile_name:  # return only one
            profile_name_index = self.get_profile_name_index(profile_name)
            profile_name = self.profile_header[profile_name_index]

            self.data_table_profile = esdl.DataTableProfile(
                id=str(uuid4()),
                name=profile_name,
                tableName=table_name,
                datetimeColumnName=datetime_columnname,
                columnName=profile_name,
                schema=schema_name,
                startDate=EDate.from_string(
                    self.start_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
                ),
                endDate=EDate.from_string(
                    self.end_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
                ),
            )
            if self.metadata and self.metadata[profile_name_index]:
                self.data_table_profile.profileQuantityAndUnit = self.metadata[
                    profile_name_index
                ].qau
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
                    startDate=EDate.from_string(
                        self.start_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
                    ),
                    endDate=EDate.from_string(
                        self.end_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
                    ),
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

    def save(self, credentials_dict: dict[str, Credentials] = None, drop=True):
        """
        Saves the current datatable profile to the database

        :param credentials_dict: Dict with Credentials to connect to the database, or use global defined credentials
        :param drop: Drop data in the referenced table before writing data (default=True)
        """

        if not credentials_dict:
            credentials_dict = global_credentials

        if (
            self.data_table_profile.configuration.type
            == esdl.DatabaseTypeEnum.POSTGRESQL
        ):
            # handle postgres
            postgres = PostgresqlConfiguration(
                self.data_table_profile, credentials_dict
            )
            postgres.save_data(
                self.profile_data_list, self.profile_header, overwrite=drop
            )
            postgres.disconnect()
        else:
            raise UnsupportedDataConfiguration(
                f"DataConfiguration {self.data_table_profile.configuration.type.name} is not (yet) supported"
            )


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
