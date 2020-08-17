from flask_socketio import emit
import requests
import json
from utils.datetime_utils import parse_date
import settings


def send_alert(message):
    print(message)
    emit('alert', message, namespace='/esdl')


def get_panel_service_datasource(database):
    ps_influxdb_host = settings.profile_database_config['protocol'] + "://" + \
                       settings.profile_database_config['host'] + ":" + \
                       settings.profile_database_config['port']

    # Try to find the datasource
    ps_influxdb_name = None
    url = settings.panel_service_config["internal_url"] + "/influxdbs/"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            result = json.loads(r.text)

            for idb in result["influxdbs"]:
                if idb["url"] == ps_influxdb_host and idb["database"] == database:
                    ps_influxdb_name = idb["name"]
                    break
    except Exception as e:
        print('Exception: ' + str(e))
        send_alert('Error accessing Panelservice API: ' + str(e))

    # Create a datasource if it's not available
    if not ps_influxdb_name:
        ps_influxdb_name = "PS_"+settings.profile_database_config['host']+"_"+database
        payload = {
            "name": ps_influxdb_name,
            "url": ps_influxdb_host,
            "database_name": database,
            "basic_auth_user": settings.profile_database_config["upload_user"],
            "basic_auth_password": settings.profile_database_config["upload_password"]
        }

        try:
            r = requests.post(url, json=payload)
            if r.status_code == 201:
                result = json.loads(r.text)
                print(result)
        except Exception as e:
            ps_influxdb_name = None
            print('Exception: ' + str(e))
            send_alert('Error accessing Panelservice API: ' + str(e))

    return ps_influxdb_name


def create_panel(graph_title, axis_title, database, measurement, field, start_datetime, end_datetime):
    ps_influxdb_name = get_panel_service_datasource(database)
    sdt = parse_date(start_datetime)
    edt = parse_date(end_datetime)

    payload = {
        "title": graph_title,
        "start": sdt.strftime("%Y-%m-%dT%H:%M:%S.000%z"),    # "2015-01-01T00:00:00.000+0100",
        "end": edt.strftime("%Y-%m-%dT%H:%M:%S.000%z"),      # "2016-01-01T01:00:00.000+0100",
        "influxdb_name": ps_influxdb_name,
        "influx_queries": [
            {
                "measurement": measurement,
                "field": field,
                "function": "sum",
                "yaxis": "left"
            }
        ],
        "yaxes": [
            {"format": "percent"}
        ],
        "thresholds": [
        ],
        "theme": "light",
        "grafana_graph_params": {
            "lineWidth": 1
        }
    }

    print(payload)
    url = settings.panel_service_config["internal_url"] + "/graphs/"
    try:
        r = requests.post(url, json=payload)
        if r.status_code == 201:
            result = json.loads(r.text)
            print(result)
            embedUrl = result['embed_url']
        else:
            embedUrl = None

    except Exception as e:
        embedUrl = None
        print('Exception: ' + str(e))
        send_alert('Error accessing Panelservice API: ' + str(e))

    print(embedUrl)
    return embedUrl
