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
from utils.datetime_utils import parse_date
import src.settings as settings
import esdl

logger = log.get_logger(__name__)


def send_alert(message):
    logger.warn(message)
    emit('alert', message, namespace='/esdl')


def get_panel_service_datasource(database, host=None):
    if host:
        ps_influxdb_host = host
    else:
        ps_influxdb_host = settings.panel_service_config['profile_database_protocol'] + "://" + \
                       settings.panel_service_config['profile_database_host'] + ":" + \
                       settings.panel_service_config['profile_database_port']
    logger.debug("Get_panel_service_datasource: db=" + database + " host="+ps_influxdb_host)

    # Try to find the datasource
    ps_influxdb_name = None
    url = settings.panel_service_config["internal_url"] + "/influxdbs/"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            result = json.loads(r.text)

            for idb in result["influxdbs"]:
                if idb["url"] == ps_influxdb_host and idb["database"] == database:
                    logger.debug("Datasource found: {}".format(idb["name"]))
                    ps_influxdb_name = idb["name"]
                    break
    except Exception as e:
        print('Exception: ' + str(e))
        send_alert('Error accessing Panelservice API: ' + str(e))

    # Create a datasource if it's not available
    if not ps_influxdb_name:
        logger.debug("No datasource found, creating new one")
        ps_influxdb_name = "PS_"+settings.panel_service_config['profile_database_host']+"_"+database
        payload = {
            "name": ps_influxdb_name,
            "url": ps_influxdb_host,
            "database_name": database,
            "basic_auth_user": settings.panel_service_config["profile_database_upload_user"],
            "basic_auth_password": settings.panel_service_config["profile_database_upload_password"]
        }

        try:
            r = requests.post(url, json=payload)
            if r.status_code == 201:
                result = json.loads(r.text)
                logger.debug("New datasource created:")
                logger.debug(result)
            else:
                logger.debug("Error creating datasource - status code: " + str(r.status_code))
                ps_influxdb_name = None
        except Exception as e:
            ps_influxdb_name = None
            print('Exception: ' + str(e))
            send_alert('Error accessing Panelservice API: ' + str(e))

    return ps_influxdb_name


def create_panel(graph_title, axis_title, host, database, measurement, field, filters, qau, prof_aggr_type, start_datetime, end_datetime):
    ps_influxdb_name = get_panel_service_datasource(database, host)
    if not ps_influxdb_name:
        logger.error("Could not find or create a datasource")
        return None
    logger.debug("Creating panel using datasource: {}".format(ps_influxdb_name))
    if not isinstance(filters, list):
        filters = [filters]

    if isinstance(start_datetime, datetime.datetime):
        sdt = start_datetime
    else:
        sdt = parse_date(start_datetime)
    if isinstance(end_datetime, datetime.datetime):
        edt = end_datetime
    else:
        edt = parse_date(end_datetime)

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
            {"format": axis_format}
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
        print('Exception: ' + str(e))
        send_alert('Error accessing Panelservice API: ' + str(e))

    logger.debug('Panel created with embedUrl: '+str(embedUrl))
    return embedUrl
