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

import codecs
import csv
import locale
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Any, Optional
from uuid import uuid4

import pytz
from pyecore.ecore import EDate

from esdl import esdl
from esdl.utils.datetime_utils import parse_date


class ProfileType(str, Enum):
    """
    Different profile types
    """
    UNKNOWN = "UNKNOWN"
    # SINGLE_VALUE = "SINGLE_VALUE"
    # VALUE_LIST = "VALUE_LIST"
    DATETIME_LIST = "DATETIME_LIST"
    CSV = "CSV"
    EXCEL = "EXCEL"


class ProfileManager:
    """
    Represents a generic (set of) profile(s). Can be converted into ESDL profiles.
    """

    def __init__(self, source_profile: "ProfileManager" = None):
        self.profile_header: List[str] | None = None  # in case of CSV or Excel based profile data
        self.profile_data_list: List[List[Any]] = []
        self.profile_type:  ProfileType = ProfileType.UNKNOWN
        self.start_datetime: Optional[datetime] = None
        self.end_datetime: Optional[datetime] = None
        self.num_profile_items: int = 0

        if source_profile:
            self.convert(source_profile)

    def convert(self, source: "ProfileManager"):
        """
        Copies all data from one profile instance to another. Is used when creating an InfluxDBProfile from an
        ExcelProfile.

        :param source: source profile where the data is copied from
        """
        self.profile_header = list(source.profile_header)
        self.profile_data_list = list(source.profile_data_list)
        self.profile_type = source.profile_type
        self.start_datetime = source.start_datetime
        self.end_datetime = source.end_datetime
        self.num_profile_items = source.num_profile_items

    def clear_profile(self):
        """
        Clears all profile information.
        """
        self.profile_header = None  # in case of CSV or Excel based profile data
        self.profile_data_list = []
        self.profile_type = ProfileType.UNKNOWN
        self.start_datetime = None
        self.end_datetime = None
        self.num_profile_items = 0

    def _check_data_format_and_size(self, profile_header, profile_data_list):
        num_columns = len(profile_header)
        if num_columns < 2:
            raise UnsupportedProfileInputDataException("profile_header should contain at least two items, " +
                                                       "a datetime column and at least one value column")

        for row in profile_data_list:
            if len(row) != num_columns:
                raise UnsupportedProfileInputDataException("one or more rows in profile_data_list don't contain the " +
                                                           "same amount of columns as the profile_header")
            if not isinstance(row[0], datetime):
                raise UnsupportedProfileInputDataException("first element in one or more rows in profile_data_list " +
                                                           "is not of type datetime")

    def set_profile(self, profile_header, profile_data_list, profile_type: ProfileType):
        """
        Sets the profile information

        :param profile_header: a list with column names, the first column is always the datetime column and also called
                               'datetime' (if you specify a different name, it's replaced by 'datetime')
        :param profile_data_list: a list of lists with values, the first item in the list must be of type datetime
        :param profile_type: the type of the profile
        """

        self._check_data_format_and_size(profile_header, profile_data_list)

        self.profile_header = profile_header
        if self.profile_header[0] != 'datetime':
            self.profile_header[0] = 'datetime'
        self.profile_data_list = profile_data_list
        self.profile_type = profile_type

        self.start_datetime = profile_data_list[0][0]
        self.end_datetime = profile_data_list[-1][0]
        self.num_profile_items = len(self.profile_data_list)

    def load_csv(self, file_path, encoding: str = "utf-8-sig"):
        """
        Reads profile data out of a CSV file.

        :param file_path: the path to the CSV file
        :param encoding: the used encoding in the CSV file (utf-8-sig by default)
        """
        self.clear_profile()
        self.profile_type = ProfileType.CSV

        try:
            csv_file = codecs.open(file_path, encoding=encoding)
            dialect = csv.Sniffer().sniff(csv_file.read(4096))
            csv_file.close()
            csv_file = codecs.open(file_path, encoding=encoding)
            reader = csv.reader(csv_file, dialect)
        except:
            # If format cannot be determined automatically, try ; as a default
            csv_file = codecs.open(file_path, encoding=encoding)
            reader = csv.reader(csv_file, delimiter=';')

        self.profile_header = next(reader)
        self.num_profile_items = 0

        previous_datetime = None
        for row in reader:
            try:
                dt = parse_date(row[0])
            except ValueError:  # ValueError: row in CSV doesn't start with recognizable datetime value, ignore row
                continue

            try:
                aware_dt = pytz.utc.localize(dt)  # Assume timezone is UTC if no TZ was given
            except ValueError:  # ValueError: No naive datetime (tzinfo is already set)
                aware_dt = dt
            row[0] = aware_dt
            for elem_idx in range(1, len(row)):
                try:
                    row[elem_idx] = locale.atof(row[elem_idx])      # Assume float values
                except Exception as e:
                    raise Exception(f"Cannot parse profile value in CSV ({row[elem_idx]})")

            if previous_datetime:
                if previous_datetime == aware_dt:
                    raise DuplicateValueInProfileException(
                        "CSV contains duplicate datetimes ({}). Check timezone and daylight saving".
                        format(aware_dt.strftime('%Y-%m-%dT%H:%M:%S%z'))
                    )
            previous_datetime = aware_dt

            if self.start_datetime is None:
                self.start_datetime = aware_dt

            self.profile_data_list.append(row)
            self.num_profile_items += 1

        self.end_datetime = self.profile_data_list[-1][0]
        csv_file.close()

    def parse_esdl(self, esdl_profile: esdl.TimeSeriesProfile | esdl.DateTimeProfile):
        """
        Parses an ESDL profile and loads the data

        :param esdl_profile: the ESDL profile object (only esdl.TimeSeriesProfile | esdl.DateTimeProfile is supported)
        """
        if not isinstance(esdl_profile, esdl.TimeSeriesProfile) and not isinstance(esdl_profile, esdl.DateTimeProfile):
            raise Exception("Profile types other than esdl.TimeSeriesProfile or esdl.DateTimeProfile are not "
                            "supported yet. Use an InfluxDBProfile instance for esdl.InfluxDBProfile")

        self.clear_profile()
        self.profile_type = ProfileType.DATETIME_LIST

        name = esdl_profile.name if esdl_profile.name else 'NoName profile'
        self.profile_header = ['datetime', name]

        if isinstance(esdl_profile, esdl.TimeSeriesProfile):
            self.start_datetime = esdl_profile.startDateTime
            try:
                aware_dt = pytz.utc.localize(self.start_datetime)  # Assume timezone is UTC if no TZ was given
            except ValueError:  # ValueError: No naive datetime (tzinfo is already set)
                aware_dt = self.start_datetime

            for value in esdl_profile.values:
                self.profile_data_list.append([aware_dt, value])
                aware_dt = aware_dt + timedelta(seconds=esdl_profile.timestep)
                self.num_profile_items += 1
            self.end_datetime = self.profile_data_list[-1][0]

        if isinstance(esdl_profile, esdl.DateTimeProfile):
            if esdl_profile.element:
                for elem in esdl_profile.element:
                    dt = elem.from_
                    try:
                        aware_dt = pytz.utc.localize(dt)  # Assume timezone is UTC if no TZ was given
                    except ValueError:  # ValueError: No naive datetime (tzinfo is already set)
                        aware_dt = dt

                    if self.start_datetime is None:
                        self.start_datetime = aware_dt

                    self.profile_data_list.append([aware_dt, elem.value])
                    self.num_profile_items += 1
                self.end_datetime = self.profile_data_list[-1][0]
            else:
                raise Exception("Empty DateTimeProfile")

    def get_profile_name_index(self, profile_name) -> int:
        """
        Calculates the index of the column in the profile data array based on the column name

        :param profile_name: the name of the profile
        :return: the index of the column in the profile data array
        """
        if profile_name is not None:
            if profile_name in self.profile_header:
                return self.profile_header.index(profile_name)
            else:
                raise UnknownProfileNameException("Unknown profile name")
        else:
            return 1   # first element is datetime, second element is the default (or only) value

    def get_esdl_datetime_profile(self, profile_name=None) -> esdl.DateTimeProfile:
        """
        Generates an esdl.DateTimeProfile from the loaded profile information

        :param profile_name: the name of the profile (only necessary when multiple columns have been loaded)
        :return: the esdl.DateTimeProfile
        """
        esdl.ProfileElement.from_.name = 'from'
        setattr(esdl.ProfileElement, 'from', esdl.ProfileElement.from_)

        if self.profile_type is ProfileType.UNKNOWN:
            raise NoProfileLoadedExecption("Cannot create DateTimeProfile, no profile information is loaded")
        profile_name_index = self.get_profile_name_index(profile_name)

        esdl_dt_profile = esdl.DateTimeProfile(id=str(uuid4()), name=profile_name)
        if profile_name:
            esdl_dt_profile.name = profile_name

        for profile_row in self.profile_data_list:
            elem = esdl.ProfileElement(
                from_=EDate.from_string(str(profile_row[0])),
                value=profile_row[profile_name_index]
            )
            esdl_dt_profile.element.append(elem)

        return esdl_dt_profile

    def get_esdl_timeseries_profile(self, profile_name=None) -> esdl.TimeSeriesProfile:
        """
        Generates an esdl.TimeSeriesProfile from the loaded profile information

        :param profile_name: the name of the column/profile (only necessary when multiple columns have been loaded)
        :return: the esdl.TimeSeriesProfile
        """
        if self.profile_type is ProfileType.UNKNOWN:
            raise NoProfileLoadedExecption("Cannot create TimeSeriesProfile, no profile information is loaded")
        profile_name_index = self.get_profile_name_index(profile_name)

        esdl_ts_profile = esdl.TimeSeriesProfile(id=str(uuid4()), name=profile_name)
        if profile_name:
            esdl_ts_profile.name = profile_name
        esdl_ts_profile.startDateTime = EDate.from_string(str(self.start_datetime))

        if self.num_profile_items > 1:
            # Assume equidistant profile values for now
            esdl_ts_profile.timestep = int((self.profile_data_list[1][0]-self.profile_data_list[0][0]).total_seconds())
        else:
            esdl_ts_profile.timestep = 0

        for profile_row in self.profile_data_list:
            esdl_ts_profile.values.append(profile_row[profile_name_index])

        return esdl_ts_profile


class NoProfileLoadedExecption(Exception):
    """Thrown when no profile information is loaded"""
    pass


class UnknownProfileNameException(Exception):
    """Thrown when an unknown profile name is given"""
    pass


class DuplicateValueInProfileException(Exception):
    """Thrown when input data for a profile contains duplicate datetime values, probably due to a timezone error with
    daylight saving"""
    pass


class UnsupportedProfileInputDataException(Exception):
    """Thrown when input data for a profile is not recognized"""
    pass
