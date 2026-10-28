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

from datetime import datetime

import esdl
import pytz

from esdl.profiles.influxdbprofilemanager import InfluxDBProfileManager as BaseInfluxDBProfileManager
from esdl.profiles.profilemanager import ProfileType
from esdl.utils.datetime_utils import parse_date


class InfluxDBProfileManager(BaseInfluxDBProfileManager):
    start_datetime: datetime | None

    def load_influxdb(
        self,
        measurement: str,
        fields: list[str],
        from_datetime: datetime | None = None,
        to_datetime: datetime | None = None,
        filters: list[dict[str, str]] | None = None,
        groupby_interval_sec: int | None = None,
    ) -> esdl.InfluxDBProfile | list[esdl.InfluxDBProfile] | None:
        """
        Load raw profile data, or bucket averages for MapEditor profile plots.
        Empty buckets are returned as null values.
        """
        if groupby_interval_sec is None:
            return super().load_influxdb(measurement, fields, from_datetime, to_datetime, filters)

        self.clear_profile()
        where_clause_list = []
        if from_datetime and to_datetime:
            influxdb_startdate = from_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
            influxdb_enddate = to_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
            where_clause_list.append("time >= '" + influxdb_startdate + "'")
            where_clause_list.append("time <= '" + influxdb_enddate + "'")

        if filters:
            for filter in filters:
                where_clause_list.append(f"{filter['tag']}='{filter['value']}'")

        fields_string = ",".join([f'mean("{field}") as "{field}"' for field in fields])
        query_string = f'SELECT {fields_string} FROM "{measurement}"'
        if where_clause_list:
            query_string += " WHERE (" + " AND ".join(where_clause_list) + ")"
        query_string += f" GROUP BY time({groupby_interval_sec}s) fill(null)"

        res = self.influxdb_client.query(query_string)
        if not res:
            return None

        for elem in res.get_points():
            dt = parse_date(elem["time"])
            try:
                aware_dt = pytz.utc.localize(dt)
            except ValueError:
                aware_dt = dt

            if self.start_datetime is None:
                self.start_datetime = aware_dt
            self.profile_data_list.append([aware_dt, *[elem[field] for field in fields]])
            self.num_profile_items += 1

        self.end_datetime = self.profile_data_list[-1][0]
        self.profile_header = ["datetime", *fields]
        self.profile_type = ProfileType.DATETIME_LIST
        tags = {filter["tag"]: filter["value"] for filter in filters} if filters else None
        return self.get_esdl_influxdb_profile(measurement, fields, tags)
