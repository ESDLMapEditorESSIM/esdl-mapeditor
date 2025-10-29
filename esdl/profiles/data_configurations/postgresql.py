import logging
from dataclasses import dataclass
from logging import warning, error
from typing import Any, Optional, List, Tuple

import psycopg
from psycopg import Connection, sql

from esdl import esdl, QuantityAndUnitType, PhysicalQuantityEnum
from esdl.profiles.data_configurations.credentials import Credentials
from esdl.units.parser import unit_to_string, build_qau_from_unit_string

# table name used for storing metadata that is not in the table
META_DATA_TABLE_NAME = "datatable_metadata"
META_DATA_TABLE_COLUMNS = ["table_name", "column_name",  "physical_quantity", "unit", "profile_name"]
META_DATA_TABLE_COLUMN_LENGTH = [64, 64, 32, 32, 255]  # VARCHAR lengths
META_DATA_TABLE_NOT_NULL = [True, True, False, False, False]

@dataclass
class DataTableMetaData:
    qau: Optional[QuantityAndUnitType]
    name: Optional[str]

# set to True to enable debugging of SQL statements
DEBUG_SQL = False

class PostgresqlConfiguration:
    """
    Implementation of PostgreSQL configuration for DataTableProfile
    DatabaseConfiguration(type=esdl.DatabaseTypeEnum.POSTGRESQL)
    """
    connection: Optional[Connection]
    datatable_profile: esdl.DataTableProfile

    def __init__(self, datatable_profile: esdl.DataTableProfile, credentials_dict: dict[str, Credentials]):
        self.datatable_profile = datatable_profile
        self.connection: Optional[Connection] = None
        self.credentials_dict = credentials_dict
        self._connect_postgres(datatable_profile, credentials_dict)


    def _connect_postgres(self, datatable_profile: esdl.DataTableProfile, credentials_dict: dict[str, Credentials]):
        try:
            configuration = datatable_profile.configuration
            # try on id of configuration
            credential = credentials_dict.get(configuration.id, None)
            if credential is None:
                # try on host name
                credential = credentials_dict.get(configuration.host, None)
                if credential is None:
                    raise InvalidCredentials(f"DataConfiguration '{configuration.id}' is has no associated credentials"
                                               f" to use for connecting to the Postgres database")

            if DEBUG_SQL:
                print(f'Connecting to Postgres database at {credential.username}@{configuration.host}:'
                  f'{configuration.port or 5432}/{configuration.database}')
            self.connection = psycopg.connect(user=credential.username,
                                               password=credential.password,
                                               host=configuration.host,
                                               port=configuration.port or 5432,
                                               dbname=configuration.database,
                                               )
        except Exception as e:
            print("Error while connecting to PostgreSQL: ", e)
            if self.connection and not self.connection.closed:
                self.connection.close()
                raise e
        return self.connection

    def get_connection(self):
        return self.connection


    def disconnect(self):
        if self.connection:
            self.connection.close()

    def load_data(self) -> Tuple[List[List[any]], List[str], List[DataTableMetaData]]:
        """
        Returns a tuple of profile_values[[]], header[], List[DataTableMetaData] with data loaded from Postgres
        """
        if not self.connection:
            raise Exception('PostgreSQL connection not established')
        # if not self.datatable_profile.columnName:
        #     raise InvalidDataTableProfile('DataTableProfile columnName not defined')


        with self.connection.cursor() as cursor:
            if self.datatable_profile.schema:
                table = self.datatable_profile.schema + "." + self.datatable_profile.tableName
            else:
                table = self.datatable_profile.tableName

            # warning: this is unquoted SQL...
            if self.datatable_profile.filter:
                where = f"WHERE {self.datatable_profile.filter}"
            else:
                where = ""

            if self.datatable_profile.columnName:
                # todo make this safe SQL
                cursor.execute(f'SELECT '
                               f'{self.datatable_profile.datetimeColumnName},{self.datatable_profile.columnName} '
                               f'FROM {table} {where};')
            else:
                cursor.execute(f'SELECT * FROM {table} {where};')
            result = cursor.fetchall()
            # process results
            columns = cursor.description
            column_names = [c.name for c in columns]
            datetime_column_index = [c.type_display for c in columns].index('timestamp')
            dt_colum = column_names.pop(datetime_column_index)
            header = [dt_colum, *column_names]

            profile_values = []
            for row in result:
                copy = list(row)
                datetime = copy.pop(datetime_column_index)
                profile_values.append([datetime, *copy])
            metadata: List[DataTableMetaData] = []
            for c in [dt_colum, *column_names]:
                dtmd = self.load_meta_data(c)
                metadata.append(dtmd)

            return profile_values, header, metadata

    def load_meta_data(self, column_name: str = None) -> None | DataTableMetaData:
        """
        Loads metadata from meta_data table
        :return: configures
        """
        if not self.connection:
            raise Exception('PostgreSQL connection not established')
        with self.connection.cursor() as cursor:
            if self.datatable_profile.schema:
                table = sql.Identifier(self.datatable_profile.schema, META_DATA_TABLE_NAME)
            else:
                table = sql.Identifier(META_DATA_TABLE_NAME)

            columns = [sql.Identifier(c) for c in META_DATA_TABLE_COLUMNS]
            query = sql.SQL("SELECT {fields} FROM {table} WHERE table_name=%s AND column_name=%s").format(
                fields=sql.SQL(', ').join(columns),
                table=table
            )
            if DEBUG_SQL:
                print(query.as_string(cursor))

            if self.datatable_profile.columnName:
                column_name = self.datatable_profile.columnName
            try:
                cursor.execute(query, (self.datatable_profile.tableName, column_name))
                result = cursor.fetchone()
                if result:
                    result_dict = dict(zip(META_DATA_TABLE_COLUMNS, result))
                    if result_dict["unit"] or result_dict["physical_quantity"]:
                        qau = build_qau_from_unit_string(result_dict["unit"], result_dict["physical_quantity"])
                        if DEBUG_SQL:
                            print(f'QaU metadata found: {result_dict["unit"]} in {result_dict["physical_quantity"]}')
                        self.datatable_profile.profileQuantityAndUnit = qau
                    if result_dict["profile_name"]:
                        self.datatable_profile.name = result_dict["profile_name"]
                    return DataTableMetaData(qau, result_dict["profile_name"])
                else:
                    warning(f"No metadata found for table {table.as_string()} and column '{column_name or self.datatable_profile.columnName}'"
                          f" in database '{self.datatable_profile.configuration.database}', cannot derive unit")
                    return None
            except Exception as e:
                warning(
                    f"No metadata found for table {table.as_string()} and column '{column_name or self.datatable_profile.columnName}'"
                    f" in database '{self.datatable_profile.configuration.database}', cannot derive units")



    def save_data(self, profile_values: List[List[Any]], header: List[str]):
        """
        Saves data to Postgres. It will insert all the columns in the profile_values by default.
        :param profile_values:
        :param header:
        :return:
        """
        if not self.connection:
            raise Exception('PostgreSQL connection not established')
        if not self.datatable_profile.tableName:
            raise InvalidDataTableProfile(f"Missing tableName in DataTableProfile with id={self.datatable_profile.id}")

        if self.datatable_profile.schema:
            table = sql.Identifier(self.datatable_profile.schema, self.datatable_profile.tableName)
        else:
            table = sql.Identifier(self.datatable_profile.tableName)

        # COMMENT ON COLUMN essim_run_20250804.csv_data_table.column2 IS 'unit=PJ';

        with self.connection.cursor() as cursor:
            non_datetime_columns = list(header)
            try:
                non_datetime_columns.remove(self.datatable_profile.datetimeColumnName)
            except ValueError as e:
                logging.error(f"Cannot find datetime column '{self.datatable_profile.datetimeColumnName}' in dataset, ")
                logging.error(f"configure using esdl.DataTableProfile.datetimeColumnName")
                exit(1)
            insert_columns = [f'"{c}" DOUBLE PRECISION' for c in non_datetime_columns]
            insert_columns.insert(0, f'"{self.datatable_profile.datetimeColumnName}" TIMESTAMP')
            insert_column_statement = ",\n".join(insert_columns)
            # create schema and table if not exists
            if self.datatable_profile.schema:
                query = sql.SQL('CREATE SCHEMA IF NOT EXISTS {schema}').format(schema=sql.Identifier(self.datatable_profile.schema))
                if DEBUG_SQL:
                    print(query.as_string(cursor))
                cursor.execute(query)
            sql_string = f"CREATE TABLE IF NOT EXISTS " + "{table}" + f" ({insert_column_statement})"
            query = sql.SQL(sql_string).format(table=table)
            if DEBUG_SQL:
                print(query.as_string(cursor))
            cursor.execute(query)
            self.connection.commit()


            columns = sql.SQL(', ').join(sql.Identifier(h) for h in header)
            query = sql.SQL("COPY {table} ({columns}) FROM STDIN").format(table=table, columns=columns)
            if DEBUG_SQL:
                print(query.as_string(cursor))
            with cursor.copy(query) as copy:
                for row in profile_values:
                    copy.write_row(row)


            # Set extra information in tableName_metadata table (in same schema)
            # such as Unit, Quantity, multiplier, and name of profile (and id?)

            for column_name in header:
                self.save_meta_data(self.datatable_profile, column_name)
            self.connection.commit()

    def save_meta_data(self, datatable_profile: esdl.DataTableProfile, column_name: str = None):
        """
        Meta data format in schema
        | table name | column_name | Unit | Quantity | description |
        :param datatable_profile: the data table profile including unit information and description
        :param column_name: [optional] the column name if not set in the datatable profile
                (when inserting multiple columns)
        :return: None
        """
        qau = datatable_profile.profileQuantityAndUnit
        if qau is None or qau.unit is None or qau.unit == esdl.UnitEnum.NONE or \
            qau.physicalQuantity is None or qau.physicalQuantity is esdl.PhysicalQuantityEnum.UNDEFINED:
            raise InvalidDataTableProfile(f"Missing Quantity and unit information for DataTableProfile with id={datatable_profile.id}")
        if column_name == datatable_profile.datetimeColumnName:
            qau = QuantityAndUnitType(id="time", unit=esdl.UnitEnum.NONE, physicalQuantity=esdl.PhysicalQuantityEnum.TIME)


        if self.datatable_profile.schema:
            table = sql.Identifier(self.datatable_profile.schema, META_DATA_TABLE_NAME)
        else:
            table = sql.Identifier(META_DATA_TABLE_NAME)

        # META_DATA_TABLE_COLUMNS = ["table_name", "column_name",  "quantity", "unit", "description"]
        insert_columns = [f"{c} VARCHAR({n}) {'NOT NULL' if nn else ''}"
                          for c,n,nn in zip(META_DATA_TABLE_COLUMNS,
                                            META_DATA_TABLE_COLUMN_LENGTH,
                                            META_DATA_TABLE_NOT_NULL)]
        insert_column_statement = ",\n".join(insert_columns)
        sql_string = "CREATE TABLE IF NOT EXISTS {table}" + \
                      f" ({insert_column_statement} " + \
                      f", PRIMARY KEY ({META_DATA_TABLE_COLUMNS[0]},{META_DATA_TABLE_COLUMNS[1]}))"
        with self.connection.cursor() as cursor:
            # create metadata table if not exists
            query = sql.SQL(sql_string).format(table=table)
            if DEBUG_SQL:
                print(query.as_string(cursor))
            cursor.execute(query)

            # insert data if not exists
            upsert_sql = "INSERT INTO {table} " + f"({','.join(META_DATA_TABLE_COLUMNS)}) VALUES " + \
                        f"({','.join( ['%s'] * len(META_DATA_TABLE_COLUMNS) )})" +\
                        f" ON CONFLICT ({','.join(META_DATA_TABLE_COLUMNS[:2])} ) DO UPDATE SET ({','.join(META_DATA_TABLE_COLUMNS[2:])}) = " + \
                         "(" + ','.join([f'EXCLUDED.{column}' for column in META_DATA_TABLE_COLUMNS[2:]]) + ")"
            # TODO: add update statement on conflict / support Upsert
            query = sql.SQL(upsert_sql).format(table=table)
            if DEBUG_SQL:
                print(query.as_string(cursor))
            unit_string = unit_to_string(qau)
            if datatable_profile.columnName:
                insert_column_name = datatable_profile.columnName
            else:
                insert_column_name = column_name
            try:
                cursor.execute(query, (datatable_profile.tableName,
                                   insert_column_name,
                                   qau.physicalQuantity.name,
                                   unit_string,
                                   datatable_profile.name))
            except Exception as e:
                error("Error", e)








class InvalidCredentials(Exception):
    """Thrown when no credentials are provided for connecting to PostgreSQL."""
    pass

class InvalidDataTableProfile(Exception):
    """Thrown when the DataTableProfile is not complete"""
    pass