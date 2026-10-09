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
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

import pytz
from pyecore.ecore import EDate

import esdl
from esdl.profiles.profilemanager import ProfileManager, UnknownProfileNameException, ProfileType
from influxdb import InfluxDBClient

from esdl.utils.datetime_utils import parse_date


@dataclass
class ConnectionSettings:
    """
    The ConnectionSettings class represents all required settings that are required to connect to an
    InfluxDB server
    """
    host: str
    """hostname of the InfluxDB server to connect to"""
    port: int
    """port to connect to"""
    username: str | None
    """username of the user that has permission to access the database"""
    password: str | None
    """password of the user"""
    database: str
    """database to connect to"""
    ssl: bool
    """indicates whether or not to use SSL when connecting to the InfluxDB server"""
    verify_ssl: bool
    """indicates wether or not to verify SSL certificates"""


class InfluxDBProfileManager(ProfileManager):
    """
    InfluxDBProfileManager: manages profile data that can be loaded from and saved to InfluxDB (v1 only).
    InfluxDBProfileManager is a subclass of ProfileManager, so it also provides functionality to convert from/to
    different ESDL profiles and to load/save to CSV
    """
    def __init__(self, settings: ConnectionSettings, source_profile=None):
        """
        Constructor of the InfluxDBProfileManager

        :param settings: connection settings to connect to the InfluxDB server
        :param source_profile: the source profile of which the data is copied into this profiles manager instance
        """
        super().__init__()

        # Temporary fix, for ESDL profiles that have HTTP(S) in the hostname
        settings.host = settings.host.replace("http://", "").replace("https://", "")

        self.database_settings = settings
        self.influxdb_client = InfluxDBClient(
            host=settings.host,
            port=settings.port,
            username=settings.username,
            password=settings.password,
            database=settings.database,
            ssl=settings.ssl,
            verify_ssl=settings.verify_ssl
        )

        # Only create database if the user has rights to do so
        try:
            if settings.database not in [db['name'] for db in self.influxdb_client.get_list_database()]:
                self.influxdb_client.create_database(settings.database)
        except:
            pass

        # If the user cannot list the measurements, the database probably doesn't exist (or connection is wrong)
        if not self.influxdb_client.get_list_measurements():
            print (f"ERROR: user {settings.username} is not allowed to list the measurements for database "
                   + f"{settings.database} on host {settings.host}")
            return

        if source_profile:
            self.convert(source_profile)
            if isinstance(source_profile, InfluxDBProfileManager):
                self.database_settings = source_profile.database_settings

    def load_influxdb(self, 
                      measurement: str,
                      fields: list,
                      from_datetime: datetime = None,
                      to_datetime: datetime = None,
                      filters: list = None,
                      groupby_interval_sec: int = None):
        """
        Loads profile information from InfluxDB

        :param measurement: the name of the measurement to use in InfluxDB
        :param fields: a list of field names that need to be loaded from InfluxDB
        :param from_datetime: the start datetime (included in the data)
        :param to_datetime: the end datetime (included in the data)
        :param filters: a list of dictionaries with 'tag' and 'value' keys, that can be used to filter on the data
        :param groupby_interval_sec: optional groupby interval in second; if not `None`, `mean()` as an aggregation function is applied to field values
        :return: None
        """
        self.clear_profile()

        where_clause_list = list()
        if from_datetime and to_datetime:
            influxdb_startdate = from_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
            influxdb_enddate = to_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

            where_clause_list.append("time >= '" + influxdb_startdate + "'")
            where_clause_list.append("time <= '" + influxdb_enddate + "'")

        if filters:
            for filter in filters:
                where_clause_list.append(f"{filter['tag']}='{filter['value']}'")

        fields_string = ','.join(['"'+field+'"' for field in fields])
        if groupby_interval_sec is not None:
            fields_string = ','.join([f"mean(\"{field}\") as \"{field}\""  for field in fields])

        query_string = f"SELECT {fields_string} FROM \"{measurement}\""
        
        if where_clause_list:
            query_string += " WHERE (" + " AND ".join(where_clause_list) + ")"

        if groupby_interval_sec is not None:
            query_string += f" GROUP BY time({groupby_interval_sec}s) fill(null)"

        res = self.influxdb_client.query(query_string)

        if res:
            res_list = res.get_points()
            for elem in res_list:
                dt = parse_date(elem['time'])

                try:
                    aware_dt = pytz.utc.localize(dt)  # Assume timezone is UTC if no TZ was given
                except ValueError:  # ValueError: No naive datetime (tzinfo is already set)
                    aware_dt = dt

                row = [aware_dt]
                if self.start_datetime is None:
                    self.start_datetime = aware_dt

                for f in fields:
                    row.append(elem[f])

                self.profile_data_list.append(row)
                self.num_profile_items += 1

            self.end_datetime = self.profile_data_list[-1][0]
            header = ['datetime']
            header.extend(fields)
            self.profile_header = header
            self.profile_type = ProfileType.DATETIME_LIST

            tags = None
            if filters:
                tags = dict()
                for filter in filters:
                    tags[filter['tag']] = filter['value']
            return self.get_esdl_influxdb_profile(measurement, fields, tags)
        else:
            return None

    @staticmethod
    def _parse_esdl_profile_filters(esdl_filters):
        if esdl_filters is None or esdl_filters == "":
            return []

        filter_str_list = esdl_filters.split(" AND ")
        filter_list = list()
        for f in filter_str_list:
            try:
                [key, value] = f.split("=")
                if key is not None and key != "" and value is not None and value != "":
                    filter_list.append({"key": key, "value": value})
                else:
                    raise WrongFilterFormatException("Filter specification in ESDL profile cannot be parsed")
            except:
                raise WrongFilterFormatException("Filter specification in ESDL profile cannot be parsed")

        return filter_list

    @staticmethod
    def create_esdl_influxdb_profile_manager(
            esdl_profile: esdl.InfluxDBProfile,
            username: str = None,
            password: str = None,
            use_ssl: bool = False,
            verify_ssl: bool = False):
        """
        method to create an instance of InfluxDBProfileManager using an esdl.InfluxDBProfile. The data referenced to in
        the profile is loaded from InfluxDB

        :param esdl_profile: esdl.InfluxDBProfile that is used as an input profile
        :param username: username to be used to connect to the InfluxDB server mentioned in the esdl.InfluxDBProfile,
                         defaults to None
        :param password: password to be used to connect to the InfluxDB server mentioned in the esdl.InfluxDBProfile,
                         defaults to None
        :param use_ssl: indicates if HTTPS should be used instead of HTTP to connect to the InfluxDB server, defaults
                        to False
        :param verify_ssl: verify SSL certificates for HTTPS requests, defaults to False
        """
        conn_settings = ConnectionSettings(
            host=esdl_profile.host,
            port=esdl_profile.port,
            database=esdl_profile.database,
            username=username,
            password=password,
            ssl=use_ssl,
            verify_ssl=verify_ssl
        )

        prof = InfluxDBProfileManager(conn_settings)
        prof.load_influxdb(
            measurement=esdl_profile.measurement,
            fields=[esdl_profile.field],
            from_datetime=esdl_profile.startDate,
            to_datetime=esdl_profile.endDate,
            filters=InfluxDBProfileManager._parse_esdl_profile_filters(esdl_profile.filters),
        )

        return prof

    @staticmethod
    def _create_esdl_filters_from_tags_dict(tags: dict = None):
        if not tags:
            return ""
        else:
            filter_list = list()

            for k, v in tags.items():
                filter_list.append(f"{k}='{v}'")

            return " AND ".join(filter_list)

    def get_esdl_influxdb_profile(self, measurement: str, field_names: list, tags: dict = None, profile_type: str = None):
        """
        Creates an esdl.InfluxDBProfile instance (or a list of instances) that refers to the data in the database.
        Is called by load_influxdb and save_influxdb

        :param measurement: name of the InfluxDB measurement where the data must be written to
        :param field_names: list of the fields that should be written to InfluxDB
        :param tags: dictionary with tags and tag values, that should be used when writing this data to InfluxDB
        :param profile_type: the type of the profile, defaults to None (deprecated, use QuantityAndUnits instead)
        :return: an esdl.InfluxDBProfile instance or a list of esdl.InfluxDBProfile instances in case multiple fields
                 were specified, with proper references to the data in the database
        """
        profile_list = list()
        for field in field_names:
            esdl_profile = esdl.InfluxDBProfile(
                id=str(uuid4()),
                host=self.database_settings.host,
                port=self.database_settings.port,
                database=self.database_settings.database,
                measurement=measurement,
                field=field,
                filters=InfluxDBProfileManager._create_esdl_filters_from_tags_dict(tags),
                startDate=EDate.from_string(self.start_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f%z')),
                endDate=EDate.from_string(self.end_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f%z')),
                profileType=profile_type,
            )
            profile_list.append(esdl_profile)

        if len(profile_list) == 1:
            return profile_list[0]
        else:
            return profile_list

    def save_influxdb(self, measurement: str, field_names: list, tags: dict = None, profile_type: str = None):
        """
        Saves profile information to InfluxDB

        :param measurement: name of the InfluxDB measurement where the data must be written to
        :param field_names: list of the fields that should be written to InfluxDB
        :param tags: dictionary with tags and tag values, that should be used when writing this data to InfluxDB
        :param profile_type: the type of the profile, defaults to None (deprecated, use QuantityAndUnits instead)
        :return: an esdl.InfluxDBProfile instance or a list of esdl.InfluxDBProfile instances in case multiple fields
                 were specified, with proper references to the data in the database
        """
        json_body = []
        if not measurement or measurement == "":
            raise NoDataException("Measurement name is not specified, so no data can be written to InfluxDB")
        if not field_names:
            raise NoDataException("No field names are specified, so no data can be written to InfluxDB")
        if tags and not isinstance(tags, dict):
            raise WrongTagsFormatException("The tags parameter should be a dictionary with tag names as keys")
        for profile_row in self.profile_data_list:
            dt_string = profile_row[0].strftime('%Y-%m-%dT%H:%M:%S%z')
            fields = {}
            for fld_name in field_names:
                if fld_name in self.profile_header:
                    idx = self.profile_header.index(fld_name)
                    fields[self.profile_header[idx]] = profile_row[idx]
                else:
                    raise UnknownProfileNameException(
                        f"Given field name ({fld_name}) is not recognized as a profile name"
                    )

            if fields:
                data = {
                    "measurement": measurement,
                    "time": dt_string,
                    "fields": fields
                }
                if tags:
                    data["tags"] = tags

                json_body.append(data)

        if json_body:
            self.influxdb_client.write_points(points=json_body, database=self.database_settings.database, batch_size=100)
            return self.get_esdl_influxdb_profile(measurement, field_names, tags=tags, profile_type=profile_type)

        else:
            return None


class NoDataException(Exception):
    """Thrown when no profile data can be written to InfluxDB"""
    pass


class WrongFilterFormatException(Exception):
    """Thrown when filter specification in ESDL profile cannot be parsed"""
    pass


class WrongTagsFormatException(Exception):
    """Thrown when the tags parameter has the wrong structure"""
    pass


class ConnectionSettingsRetrivalError(Exception):
    pass