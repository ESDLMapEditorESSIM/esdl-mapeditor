import logging
from dataclasses import dataclass
from datetime import datetime
from logging import warning, error
from typing import Any, Optional, List, Tuple, Dict

import psycopg
from psycopg import Connection, sql

from esdl import esdl, QuantityAndUnitType
from esdl.profiles.data_configurations.credentials import Credentials
from esdl.units.parser import unit_to_string, build_qau_from_unit_string

# table name used for storing metadata that is not in the table
META_DATA_TABLE_NAME = "datatable_metadata"
META_DATA_TABLE_COLUMNS = [
    "table_name",
    "column_name",
    "physical_quantity",
    "unit",
    "profile_name",
]
META_DATA_TABLE_COLUMN_LENGTH = [64, 64, 32, 32, 255]  # VARCHAR lengths
META_DATA_TABLE_NOT_NULL = [True, True, True, False, False]

# set to True to enable debugging of SQL statements
DEBUG_SQL = False


@dataclass
class DataTableMetaData:
    qau: Optional[QuantityAndUnitType]
    name: Optional[str]


class PostgresqlConfiguration:
    """
    Implementation of PostgreSQL configuration for DataTableProfile
    DatabaseConfiguration(type=esdl.DatabaseTypeEnum.POSTGRESQL)
    """

    connection: Optional[Connection]
    datatable_profile: esdl.DataTableProfile

    def __init__(
        self,
        datatable_profile: esdl.DataTableProfile,
        credentials_dict: dict[str, Credentials],
    ):
        self.datatable_profile = datatable_profile
        self.connection: Optional[Connection] = None
        self.credentials_dict = credentials_dict
        self._connect_postgres(datatable_profile, credentials_dict)

    def _connect_postgres(
        self,
        datatable_profile: esdl.DataTableProfile,
        credentials_dict: dict[str, Credentials],
    ):
        try:
            configuration = datatable_profile.configuration
            # try on id of configuration
            credential = credentials_dict.get(configuration.id, None)
            if credential is None:
                # try on host name
                credential = credentials_dict.get(configuration.host, None)
                if credential is None:
                    raise InvalidCredentials(
                        f"DataConfiguration '{configuration.id}' is has no associated credentials"
                        f" to use for connecting to the Postgres database"
                    )

            if DEBUG_SQL:
                print(
                    f"Connecting to Postgres database at {credential.username}@{configuration.host}:"
                    f"{configuration.port or 5432}/{configuration.database}"
                )
            self.connection = psycopg.connect(
                user=credential.username,
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

    def load_data(
        self, additional_filters: Dict[str, Any] = None, column_based: bool = False
    ) -> Tuple[List[List[any]], List[str], List[DataTableMetaData | None]]:
        """
        Load data from the configured table using the DataTableProfile settings.
        Supports querying a single column or all columns. The datetime column is
        always returned as the first column.

        :param additional_filters: (key,value) set of additional filters for the query in the WHERE clause
        :param column_based: if True, data is returned by column instead of row
        :return: a tuple of profile_values[[]], header[], List[DataTableMetaData] with data loaded from Postgres.
        the datetime column is always returned as first column
        """
        if not self.connection:
            raise Exception("PostgreSQL connection not established")

        with self.connection.cursor() as cursor:
            if self.datatable_profile.schema:
                table_ident = sql.Identifier(
                    self.datatable_profile.schema, self.datatable_profile.tableName
                )
            else:
                table_ident = sql.Identifier(self.datatable_profile.tableName)

            dt_ident = sql.Identifier(self.datatable_profile.datetimeColumnName)
            # column is None if we want to query all columns
            col_ident = (
                sql.Identifier(self.datatable_profile.columnName)
                if self.datatable_profile.columnName
                else None
            )

            where_sql, params = PostgresqlConfiguration._build_where_clause(
                dt_ident,
                self.datatable_profile.startDate,
                self.datatable_profile.endDate,
                additional_filters,
            )

            if self.datatable_profile.columnName:
                query = sql.SQL("SELECT {dt}, {col} FROM {tbl} {where}").format(
                    dt=dt_ident, col=col_ident, tbl=table_ident, where=where_sql
                )
            else:
                # Fallback to select all columns
                query = sql.SQL("SELECT * FROM {tbl} {where}").format(
                    tbl=table_ident, where=where_sql
                )

            if DEBUG_SQL:
                print(query.as_string(cursor))

            cursor.execute(query, params)
            result = cursor.fetchall()

            # process results
            profile_values, header = PostgresqlConfiguration._process_query_results(
                cursor, result, self.datatable_profile.datetimeColumnName, column_based
            )
            metadata = [self.load_meta_data(c) for c in header]

            return profile_values, header, metadata

    def load_data_custom(
        self,
        schema: Optional[str],
        table_name: str,
        datetime_column_name: str,
        column_name: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        additional_filters: Optional[Dict[str, Any]],
        multiplier: Optional[float],
        downsample_bucket_sec: Optional[int],
        column_based: bool,
    ) -> Tuple[List[List[any]], List[str], List[DataTableMetaData | None]]:
        """
        Execute a flexible SQL query against a PostgreSQL table, supporting a SINGLE
        value column, datetime filtering, optional downsampling, and additional
        equality-based filters.

        :param schema: Optional schema name.
        :param table_name: Name of the table to query.
        :param datetime_column_name: Name of the datetime column.
        :param column_name: Name of the data column to query.
        :param start_date: Optional start datetime for filtering.
        :param end_date: Optional end datetime for filtering.
        :param additional_filters: Optional dict of column=value filters for the WHERE clause.
        :param multiplier: Optional multiplier for scaling profile value.
        :param downsample_bucket_sec: If provided, results are grouped into fixed-size
                                    time buckets and averaged.
        :param column_based: If True, return data grouped by column instead of row.

        :return: A tuple of (profile_values, header, metadata).
        """
        if not self.connection:
            raise Exception("PostgreSQL connection not established")

        with self.connection.cursor() as cursor:
            if schema:
                table_ident = sql.Identifier(schema, table_name)
            else:
                table_ident = sql.Identifier(table_name)

            dt_ident = sql.Identifier(datetime_column_name)
            col_ident = sql.Identifier(column_name)

            # Scale profile value if multiplier is given;
            # otherwise, DataTableProfile assigned multiplier or default value (1.0) is used.
            multiplier = (
                multiplier
                if multiplier is not None
                else self.datatable_profile.multiplier
            )

            where_sql, params = PostgresqlConfiguration._build_where_clause(
                dt_ident, start_date, end_date, additional_filters
            )

            # Downsampled query by grouping them into fixed-size buckets.
            if downsample_bucket_sec:
                query = sql.SQL(
                    """
                    SELECT
                        to_timestamp(
                            floor(extract(epoch from {dt}) / %s) * %s
                        )::timestamp AS {dt},
                        AVG({col} * %s) AS {col}
                    FROM {tbl}
                    {where}
                    GROUP BY 1
                    ORDER BY 1
                """
                ).format(dt=dt_ident, col=col_ident, tbl=table_ident, where=where_sql)
                params = [
                    downsample_bucket_sec,
                    downsample_bucket_sec,
                    multiplier,
                    *params,
                ]

            # Fallback to normal query
            else:
                query = sql.SQL(
                    "SELECT {dt}, ({col} * %s) AS {col} FROM {tbl} {where}"
                ).format(dt=dt_ident, col=col_ident, tbl=table_ident, where=where_sql)
                params = [multiplier, *params]

            if DEBUG_SQL:
                print(query.as_string(cursor))

            cursor.execute(query, params)
            result = cursor.fetchall()

            profile_values, header = PostgresqlConfiguration._process_query_results(
                cursor, result, datetime_column_name, column_based
            )

            metadata = [self.load_meta_data(c) for c in header]

            return profile_values, header, metadata

    @staticmethod
    def _build_where_clause(
        dt_ident,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        additional_filters: Dict[str, Any] = None,
    ) -> Tuple[Any, List]:
        """
        A utility function to build a SQL WHERE clause for datetime range and simple equality filters.

        :param dt_ident: psycopg2 SQL identifier for the datetime column.
        :param start_date: Optional start datetime for filtering.
        :param end_date: Optional end datetime for filtering.
        :param additional_filters: Optional dict of column=value filters.
        :return: A tuple of (where_sql, params_list).
        """
        if additional_filters is not None and not isinstance(additional_filters, dict):
            raise TypeError("additional_filters must be a dict or None")

        where_clauses = []
        params = []

        dt_str_format = "%Y-%m-%dT%H:%M:%SZ"

        if start_date:
            where_clauses.append(sql.SQL("{dt} >= %s").format(dt=dt_ident))
            params.append(start_date.strftime(dt_str_format))

        if end_date:
            where_clauses.append(sql.SQL("{dt} <= %s").format(dt=dt_ident))
            params.append(end_date.strftime(dt_str_format))

        # NOTE: 'OR' or more complex filtering is not supported yet.
        if additional_filters:
            for col, val in additional_filters.items():
                where_clauses.append(
                    sql.SQL("{col} = %s").format(col=sql.Identifier(col))
                )
                params.append(val)

        where_sql = (
            sql.SQL(" WHERE ") + sql.SQL(" AND ").join(where_clauses)
            if where_clauses
            else sql.SQL("")
        )

        return where_sql, params

    @staticmethod
    def _process_query_results(
        cursor, result: List, datetime_column_name: str, column_based: bool
    ) -> Tuple[List[List], List[str]]:
        """
        Reorder results so the datetime column is always first.
        Supports row-based or column-based output.
        """
        columns = cursor.description
        column_names = [c.name for c in columns]

        try:
            dt_index = column_names.index(datetime_column_name)
        except ValueError:
            dt_index = 0

        dt_col = column_names.pop(dt_index)
        header = [dt_col, *column_names]

        profile_values = [[] for _ in range(len(header))] if column_based else []

        for row in result:
            row_list = list(row)
            dt_val = row_list.pop(dt_index)
            ordered = [dt_val, *row_list]

            if not column_based:
                profile_values.append(ordered)
            else:
                for i, val in enumerate(ordered):
                    profile_values[i].append(val)

        return profile_values, header

    def load_meta_data(self, column_name: str = None) -> None | DataTableMetaData:
        """
        Loads metadata from meta_data table

        :return: configures
        """
        if not self.connection:
            raise Exception("PostgreSQL connection not established")
        with self.connection.cursor() as cursor:
            if self.datatable_profile.schema:
                table = sql.Identifier(
                    self.datatable_profile.schema, META_DATA_TABLE_NAME
                )
            else:
                table = sql.Identifier(META_DATA_TABLE_NAME)

            columns = [sql.Identifier(c) for c in META_DATA_TABLE_COLUMNS]
            query = sql.SQL(
                "SELECT {fields} FROM {table} WHERE table_name=%s AND column_name=%s"
            ).format(fields=sql.SQL(", ").join(columns), table=table)
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
                        qau = build_qau_from_unit_string(
                            result_dict["unit"], result_dict["physical_quantity"]
                        )
                        if DEBUG_SQL:
                            print(
                                f'QaU metadata found: {result_dict["physical_quantity"]} in {result_dict["unit"]}'
                            )
                        self.datatable_profile.profileQuantityAndUnit = qau
                    if result_dict["profile_name"]:
                        self.datatable_profile.name = result_dict["profile_name"]
                    return DataTableMetaData(qau, result_dict["profile_name"])
                else:
                    warning(
                        f"No metadata found for table {table.as_string()} and column '{column_name or self.datatable_profile.columnName}'"
                        f" in database '{self.datatable_profile.configuration.database}', cannot derive unit"
                    )
                    return None
            except Exception as e:
                warning(
                    f"No metadata found for table {table.as_string()} and column '{column_name or self.datatable_profile.columnName}'"
                    f" in database '{self.datatable_profile.configuration.database}', cannot derive units"
                )

    def save_data(
        self, profile_values: List[List[Any]], header: List[str], overwrite: bool = True
    ):
        """
        Saves data to Postgres. It will insert all the columns in the profile_values by default.

        :param profile_values:
        :param header:
        :param overwrite: If True, truncate the existing table rows and insert new ones.
        :return:
        """
        if not self.connection:
            raise Exception("PostgreSQL connection not established")
        if not self.datatable_profile.tableName:
            raise InvalidDataTableProfile(
                f"Missing tableName in DataTableProfile with id={self.datatable_profile.id}"
            )

        if self.datatable_profile.schema:
            table = sql.Identifier(
                self.datatable_profile.schema, self.datatable_profile.tableName
            )
        else:
            table = sql.Identifier(self.datatable_profile.tableName)

        # COMMENT ON COLUMN essim_run_20250804.csv_data_table.column2 IS 'unit=PJ';

        with self.connection.cursor() as cursor:
            non_datetime_columns = list(header)
            try:
                non_datetime_columns.remove(self.datatable_profile.datetimeColumnName)
            except ValueError as e:
                logging.error(
                    f"Cannot find datetime column '{self.datatable_profile.datetimeColumnName}' in dataset, "
                )
                logging.error(
                    f"configure using esdl.DataTableProfile.datetimeColumnName"
                )
                raise e
            insert_columns = [f'"{c}" DOUBLE PRECISION' for c in non_datetime_columns]
            insert_columns.insert(
                0, f'"{self.datatable_profile.datetimeColumnName}" TIMESTAMP'
            )
            insert_column_statement = ",\n".join(insert_columns)

            # create schema and table if not exists
            if self.datatable_profile.schema:
                query = sql.SQL("CREATE SCHEMA IF NOT EXISTS {schema}").format(
                    schema=sql.Identifier(self.datatable_profile.schema)
                )
                if DEBUG_SQL:
                    print(query.as_string(cursor))
                cursor.execute(query)

            sql_string = (
                "CREATE TABLE IF NOT EXISTS {table}" + f" ({insert_column_statement})"
            )
            query = sql.SQL(sql_string).format(table=table)
            if DEBUG_SQL:
                print(query.as_string(cursor))
            cursor.execute(query)
            # create index on table datetime column
            sql_string = r"CREATE INDEX IF NOT EXISTS {index_name} ON {table} USING btree ({column_name})"
            query = sql.SQL(sql_string).format(
                index_name=sql.Identifier(
                    f"{self.datatable_profile.tableName}_metadata_datetime_idx"
                ),
                table=table,
                column_name=sql.Identifier(self.datatable_profile.datetimeColumnName),
            )
            cursor.execute(query)
            self.connection.commit()

            if overwrite:
                query = sql.SQL("TRUNCATE TABLE {table}").format(table=table)
                if DEBUG_SQL:
                    print(query.as_string(cursor))
                cursor.execute(query)

            columns = sql.SQL(", ").join(sql.Identifier(h) for h in header)
            query = sql.SQL("COPY {table} ({columns}) FROM STDIN").format(
                table=table, columns=columns
            )
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

    def save_meta_data(
        self, datatable_profile: esdl.DataTableProfile, column_name: str = None
    ):
        """
        Meta data format in schema
        | table name | column_name | Unit | Quantity | description |

        :param datatable_profile: the data table profile including unit information and description
        :param column_name: [optional] the column name if not set in the datatable profile
                (when inserting multiple columns)
        :return: None
        """
        qau = datatable_profile.profileQuantityAndUnit
        if qau is None or qau.unit is None or qau.physicalQuantity is None:
            raise InvalidDataTableProfile(
                f"Missing Quantity and unit information for DataTableProfile with id={datatable_profile.id}"
            )
        if column_name == datatable_profile.datetimeColumnName:
            qau = QuantityAndUnitType(
                id="time",
                unit=esdl.UnitEnum.NONE,
                physicalQuantity=esdl.PhysicalQuantityEnum.TIME,
            )

        if self.datatable_profile.schema:
            table = sql.Identifier(self.datatable_profile.schema, META_DATA_TABLE_NAME)
        else:
            table = sql.Identifier(META_DATA_TABLE_NAME)

        # META_DATA_TABLE_COLUMNS = ["table_name", "column_name",  "quantity", "unit", "description"]
        insert_columns = [
            f"{c} VARCHAR({n}){' NOT NULL' if nn else ''}"
            for c, n, nn in zip(
                META_DATA_TABLE_COLUMNS,
                META_DATA_TABLE_COLUMN_LENGTH,
                META_DATA_TABLE_NOT_NULL,
            )
        ]
        insert_column_statement = ",\n".join(insert_columns)
        sql_string = (
            "CREATE TABLE IF NOT EXISTS {table}"
            + f" ({insert_column_statement}"
            + f", PRIMARY KEY ({META_DATA_TABLE_COLUMNS[0]},{META_DATA_TABLE_COLUMNS[1]}))"
        )
        with self.connection.cursor() as cursor:
            # create metadata table if not exists
            query = sql.SQL(sql_string).format(table=table)
            if DEBUG_SQL:
                print(query.as_string(cursor))
            cursor.execute(query)

            # insert data if not exists
            upsert_sql = (
                "INSERT INTO {table} "
                + f"({','.join(META_DATA_TABLE_COLUMNS)}) VALUES "
                + f"({','.join( ['%s'] * len(META_DATA_TABLE_COLUMNS) )})"
                + f" ON CONFLICT ({','.join(META_DATA_TABLE_COLUMNS[:2])} ) DO UPDATE SET ({','.join(META_DATA_TABLE_COLUMNS[2:])}) = "
                + "("
                + ",".join(
                    [f"EXCLUDED.{column}" for column in META_DATA_TABLE_COLUMNS[2:]]
                )
                + ")"
            )

            query = sql.SQL(upsert_sql).format(table=table)
            if DEBUG_SQL:
                print(query.as_string(cursor))
            unit_string = unit_to_string(qau)
            if datatable_profile.columnName:
                insert_column_name = datatable_profile.columnName
            else:
                insert_column_name = column_name
            try:
                cursor.execute(
                    query,
                    (
                        datatable_profile.tableName,
                        insert_column_name,
                        qau.physicalQuantity.name,
                        unit_string,
                        datatable_profile.name,
                    ),
                )
            except Exception as e:
                error("Error", e)


class InvalidCredentials(Exception):
    """Thrown when no credentials are provided for connecting to PostgreSQL."""

    pass


class InvalidDataTableProfile(Exception):
    """Thrown when the DataTableProfile is not complete"""

    pass
