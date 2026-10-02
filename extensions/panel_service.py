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

from flask_socketio import emit
import requests
import json
import src.log as log
import datetime
from esdl.utils.datetime_utils import parse_date
import src.settings as settings
import esdl

logger = log.get_logger(__name__)


def send_alert(message):
    logger.warn(message)
    emit('alert', message, namespace='/esdl')


def _panel_service_profile_host(profile_host: str) -> str:
    """
    Return the InfluxDB host as seen by panel-service and Grafana.

    MapEditor may reach the profile database through PROFILE_DATABASE_HOST, such as localhost in local development.
    Panel-service and Grafana may run elsewhere, such as Docker, and then need PANEL_SERVICE_PROFILE_DB_HOST
    instead.
    """
    profile_db_host = settings.profile_database_config['host']
    panel_db_host = settings.panel_service_config['profile_database_host']
    if not profile_db_host or not panel_db_host:
        return profile_host

    profile_db_port = settings.profile_database_config['port']
    profile_db_url = '{}://{}:{}'.format(
        settings.profile_database_config['protocol'], profile_db_host, profile_db_port
    )
    if profile_host not in [profile_db_host, profile_db_host + ':' + profile_db_port, profile_db_url]:
        return profile_host

    return '{}://{}:{}'.format(
        settings.panel_service_config['profile_database_protocol'],
        panel_db_host,
        settings.panel_service_config['profile_database_port'],
    )


def get_panel_service_datasource(database: str, host: str | None = None, username: str | None = None,
                                 password: str | None = None) -> str | None:
    """
    Create or get the name of the grafana datasource belonging to the database / host combination
    If you don't specify a host, the defaults from the config are taken (influxdb that is part of the MapEditor stack)
    """
    if host:
        ps_influxdb_host = host
        ps_influxdb_user = username
        ps_influxdb_password = password
    else:
        ps_influxdb_host = settings.panel_service_config['profile_database_protocol'] + "://" + \
                       settings.panel_service_config['profile_database_host'] + ":" + \
                       settings.panel_service_config['profile_database_port']
        ps_influxdb_user = settings.panel_service_config["profile_database_upload_user"]
        ps_influxdb_password = settings.panel_service_config["profile_database_upload_password"]

    logger.debug("Get_panel_service_datasource: db=" + database + " host="+ps_influxdb_host)

    # Try to find the datasource
    ps_influxdb_name = None
    url = settings.panel_service_config["internal_url"] + "/influxdbs/"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            result = json.loads(r.text)

            datasource_host = _panel_service_profile_host(ps_influxdb_host)
            for idb in result["influxdbs"]:
                if idb["url"] == datasource_host and idb["database"] == database:
                    logger.debug("Datasource found: {}".format(idb["name"]))
                    ps_influxdb_name = idb["name"]
                    break
    except Exception as e:
        logger.exception("Error accessing Panelservice API")
        send_alert('Error accessing Panelservice API: ' + str(e))

    # Create a datasource if it's not available
    if not ps_influxdb_name:
        logger.debug("No datasource found, creating new one")

        datasource_host = _panel_service_profile_host(ps_influxdb_host)
        host_for_datasource_name = datasource_host.replace("//", "").replace(":", "-")
        ps_influxdb_name = "PS_" + host_for_datasource_name + "_" + database
        payload = {
            "name": ps_influxdb_name,
            "url": datasource_host,
            "database_name": database
        }
        if ps_influxdb_user is not None:
            payload["basic_auth_user"] = ps_influxdb_user
        if ps_influxdb_password is not None:
            payload["basic_auth_password"] = ps_influxdb_password

        try:
            r = requests.post(url, json=payload)
            if r.status_code == 201:
                result = json.loads(r.text)
                logger.debug("New datasource created:")
                logger.debug(result)
            else:
                logger.debug("Error creating datasource", datasource_name=ps_influxdb_name, status_code=str(r.status_code), message=r.json()["message"])
                ps_influxdb_name = None
        except Exception as e:
            ps_influxdb_name = None
            logger.exception("Error accessing Panelservice API")
            send_alert('Error accessing Panelservice API: ' + str(e))

    return ps_influxdb_name


def convert_filters(filters):
    """ Converts filters to the right format for the panel service"""
    if filters is None or filters == "":
        filters = []
    elif isinstance(filters, str):
        filters = filters.split(' AND ')
    elif not isinstance(filters, list):
        filters = [filters]

    return filters


def convert_datetimes(start_datetime, end_datetime):
    """ Converts datetimes to the right format for the panel service"""
    if isinstance(start_datetime, datetime.datetime):
        sdt = start_datetime
    else:
        sdt = parse_date(start_datetime)
    if isinstance(end_datetime, datetime.datetime):
        edt = end_datetime
    else:
        edt = parse_date(end_datetime)

    return sdt, edt


def determine_axis_format(qau):
    if qau:
        if qau.unit == esdl.UnitEnum.from_string("WATT") and qau.multiplier is None and qau.perUnit is None:
            axis_format = "watt"
        elif qau.physicalQuantity == esdl.PhysicalQuantityEnum.from_string("TEMPERATURE") and \
                qau.unit == esdl.UnitEnum.from_string("DEGREES_CELSIUS"):
            axis_format = "celsius"
        elif qau.physicalQuantity == esdl.PhysicalQuantityEnum.from_string("PRESSURE") and \
                qau.unit == esdl.UnitEnum.from_string("BAR"):
            axis_format = "pressurebar"
        # elif qau.physicalQuantity == esdl.PhysicalQuantityEnum.from_string("SPEED") and \
        #         qau.unit == esdl.UnitEnum.from_string("METRE") and \
        #         qau.perTimeUnit == esdl.TimeUnitEnum.from_string("SECOND"):
        #     axis_format = "velocityms"
        else:
            axis_format = "none"
    else:
        axis_format = "percent"

    return axis_format


def determine_datasource_name(host, database, datasource):
    if host is None and database is None and datasource is None:
        ps_influxdb_name = None
        logger.error("Specify either host and database or datasource")
    elif not datasource:
        ps_influxdb_name = get_panel_service_datasource(database, host, "", "")
        if not ps_influxdb_name:
            logger.error("Could not find or create a datasource")
    else:
        ps_influxdb_name = datasource

    if ps_influxdb_name:
        logger.debug("Creating panel using datasource: {}".format(ps_influxdb_name))

    return ps_influxdb_name


def create_panel(graph_title, axis_title, measurement, field, filters, qau, prof_aggr_type, start_datetime, end_datetime, host=None, database=None, datasource=None):
    if isinstance(qau, esdl.QuantityAndUnitReference):
        qau = qau.reference
    ps_influxdb_name = determine_datasource_name(host, database, datasource)
    filters = convert_filters(filters)
    sdt, edt = convert_datetimes(start_datetime, end_datetime)
    axis_format = determine_axis_format(qau)

    payload = {
        "title": graph_title,
        "start": sdt.strftime("%Y-%m-%dT%H:%M:%S.000%z"),    # "2015-01-01T00:00:00.000+0100",
        "end": edt.strftime("%Y-%m-%dT%H:%M:%S.000%z"),      # "2016-01-01T01:00:00.000+0100",
        "influxdb_name": ps_influxdb_name,
        "influx_queries": [
            {
                "measurement": measurement,
                "field": field,
                "function": prof_aggr_type,
                "filters": filters,
                "yaxis": "left"
            }
        ],
        "yaxes": [
            {
                "format": axis_format,
                "min": None,
            }
        ],
        "thresholds": [
        ],
        "theme": "light",
        "grafana_graph_params": {
            "lineWidth": 1
        }
    }

    url = settings.panel_service_config["internal_url"] + "/graphs/"
    try:
        r = requests.post(url, json=payload)
        if r.status_code == 201:
            result = json.loads(r.text)
            logger.debug("Panel created:")
            logger.debug(result)
            embedUrl = result['embed_url']
        else:
            logger.debug("Error creating panel, status_code={}".format(r.status_code))
            embedUrl = None

    except Exception as e:
        embedUrl = None
        logger.exception("Error accessing Panelservice API")
        send_alert('Error accessing Panelservice API: ' + str(e))

    logger.debug('Panel created with embedUrl: '+str(embedUrl))
    return embedUrl


def create_panel_multiple(graph_title, axis_title, dataset_info, qau, start_datetime, end_datetime, host=None, database=None, datasource=None):
    # dataset_info: measurement, field, prof_aggr_type, filters
    if isinstance(qau, esdl.QuantityAndUnitReference):
        qau = qau.reference

    ps_influxdb_name = determine_datasource_name(host, database, datasource)
    sdt, edt = convert_datetimes(start_datetime, end_datetime)
    axis_format = determine_axis_format(qau)

    payload = {
        "title": graph_title,
        "start": sdt.strftime("%Y-%m-%dT%H:%M:%S.000%z"),    # "2015-01-01T00:00:00.000+0100",
        "end": edt.strftime("%Y-%m-%dT%H:%M:%S.000%z"),      # "2016-01-01T01:00:00.000+0100",
        "influxdb_name": ps_influxdb_name,
        "influx_queries": [
        ],
        "yaxes": [
            {
                "format": axis_format,
                "min": None,
            }
        ],
        "thresholds": [
        ],
        "theme": "light",
        "grafana_graph_params": {
            "lineWidth": 1
        }
    }

    for dsi in dataset_info:
        f = dsi["filters"]
        f = convert_filters(f)

        influxdb_query = {
            "measurement": dsi["measurement"],
            "field": dsi["field"],
            "function": dsi["prof_aggr_type"],
            "alias": dsi["alias"],
            "filters": f,
            "yaxis": "left"
        }
        payload["influx_queries"].append(influxdb_query)

    url = settings.panel_service_config["internal_url"] + "/graphs/"
    try:
        r = requests.post(url, json=payload)
        if r.status_code == 201:
            result = json.loads(r.text)
            logger.debug("Panel created:")
            logger.debug(result)
            embedUrl = result['embed_url']
        else:
            logger.debug("Error creating panel, status_code={}".format(r.status_code))
            embedUrl = None

    except Exception as e:
        embedUrl = None
        logger.exception("Error accessing Panelservice API")
        send_alert('Error accessing Panelservice API: ' + str(e))

    logger.debug('Panel created with embedUrl: '+str(embedUrl))
    return embedUrl
