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
import csv
import os
import subprocess
from uuid import uuid4

from geo.Geoserver import Geoserver

from extensions.settings_storage import SettingsStorage, SettingType
from src.wms_layers import LAYERS_SETTING, LAYERS_GROUP_SETTING
from dotenv import load_dotenv

load_dotenv()


def _get_identifier(setting_type: SettingType, project_name: str) -> str | None:
    if setting_type is None:
        return
    elif setting_type == SettingType.PROJECT:
        if project_name is not None:
            identifier = project_name.replace(' ', '_')
        else:
            identifier = 'unnamed project'
    elif setting_type == SettingType.SYSTEM:
        identifier = SettingsStorage.SYSTEM_NAME_IDENTIFIER
    else:
        return None
    return identifier


def load_wms_layer_postgis(postgres_host: str, postgres_port: str, postgres_user: str, postgres_password: str,
                           postgres_db: str, file_path: str, table_name: str) -> bool:
    if file_path.endswith(tuple(os.environ.get('RASTER_EXTENSIONS').replace(" ", "").split(","))):
        linux_file_path = file_path.replace("C:", "/mnt/c").replace("\\", "/")
        command = f'wsl raster2pgsql -c -I -F -s 28992 -t 100x100 "{linux_file_path}" public.{table_name} | ' \
                  f'PGPASSWORD={postgres_password} psql -U {postgres_user} -d {postgres_db} -h {postgres_host}' \
                  f' -p {postgres_port}'
        subprocess.check_call(command)
    else:
        result = subprocess.run(
            f'ogr2ogr -f PostgreSQL "PG:host={postgres_host} port={postgres_port} user={postgres_user}'
            f' password={postgres_password} dbname={postgres_db}" "{file_path}" -nln {table_name}',
            shell=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print("stdout:", result.stdout)
        if result.stderr:
            print("stderr:", result.stderr)
            return False
    return True


def connect_to_geoserver(geo_server_url: str, geoserver_admin_user: str, geoserver_admin_password: str) -> Geoserver:
    print("Connecting to geoserver", geo_server_url)
    geo = Geoserver(
        service_url=geo_server_url,
        username=geoserver_admin_user,
        password=geoserver_admin_password,
    )
    return geo


def add_wms_group(layer_groups: dict, parent_uuid: str, setting_type: SettingType, project_name: str,
                  description: str) -> str:
    for group_id, group in layer_groups.items():
        if description == group['description'] and group_id in layer_groups[parent_uuid]['child_ids']:
            return group_id  # layer group already exits
    if setting_type == SettingType.SYSTEM:
        project_name = SettingType.SYSTEM.value
    group = {
        "setting_type": setting_type.value,
        "project_name": project_name,
        "description": description,
        "child_ids": []
    }
    group_uuid = str(uuid4())
    layer_groups[group_uuid] = group
    layer_groups[parent_uuid]['child_ids'].append(group_uuid)
    return group_uuid


def add_wms_layer(wms_layers: dict, parent_group: dict, setting_type: SettingType, project_name: str, description: str,
                  url: str, layer_name: str,
                  legend_url: str):
    if setting_type == SettingType.SYSTEM:
        project_name = SettingType.SYSTEM.value
    layer = {
        "description": description,
        "url": url,
        "layer_name": layer_name,
        "setting_type": setting_type.value,
        "project_name": project_name,
        "legend_url": legend_url,
        "layer_ref": None,
        "visible": False
    }
    layer_uuid = str(uuid4())
    wms_layers[layer_uuid] = layer
    parent_group['child_ids'].append(layer_uuid)


def load_layers():
    # connect to geoserver
    geo = connect_to_geoserver(os.environ.get('GEOSERVER_URL'), os.environ.get('GEOSERVER_ADMIN_USER'),
                               os.environ.get('GEOSERVER_ADMIN_PASSWORD'))

    geo.create_workspace(workspace=os.environ.get('GEOSERVER_WORKSPACE'))

    geo.create_featurestore(
        store_name=os.environ.get('GEOSERVER_STORENAME'),
        workspace=os.environ.get('GEOSERVER_WORKSPACE'),
        db=os.environ.get('POSTGRES_DB'),
        host=os.environ.get('POSTGRES_HOST_INTERNAL'),
        port=int(os.environ.get('POSTGRES_PORT_INTERNAL')),
        pg_user=os.environ.get('POSTGRES_USER'),
        pg_password=os.environ.get('POSTGRES_PASSWORD'),
    )

    # get project wms layers and groups
    settings_storage = SettingsStorage(database_uri=f"mongodb://{os.environ.get('MONGO_URL')}")
    setting_type = SettingType(os.environ.get('SETTING_TYPE'))
    identifier = _get_identifier(setting_type, os.environ.get('PROJECT_NAME'))
    if setting_type == SettingType.SYSTEM:
        root_key = 'system_root_group'
    else:
        root_key = f"{identifier}_root_group"

    if settings_storage.has(setting_type, identifier, LAYERS_SETTING):
        wms_layers = settings_storage.get(setting_type, identifier, LAYERS_SETTING)
    else:
        wms_layers = {}
    if settings_storage.has(setting_type, identifier, LAYERS_GROUP_SETTING):
        layer_groups = settings_storage.get(setting_type, identifier, LAYERS_GROUP_SETTING)
    else:
        if setting_type == SettingType.SYSTEM:
            description = "Standard Layers"
        else:
            description = f"Project Layers for {identifier}"
        layer_groups = {root_key: {
            "setting_type": "project",
            "project_name": identifier,
            "description": description,
            "is_root": True,
            "child_ids": [],
            "readonly": False
        }}

    # add base folder
    base_folder_name = os.path.normpath(os.environ.get('FOLDER_PATH')).split(os.path.sep)[-1]
    base_folder_uuid = add_wms_group(layer_groups, root_key, setting_type, os.environ.get('PROJECT_NAME'),
                                     base_folder_name)

    with open(os.environ.get('LIST_TO_IMPORT_FILE'), newline='') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in csv_reader:
            print(row)
            file_path = row[0].strip()  # remove newline characters
            print(f"processing '{file_path}'")

            path_in_base_folder = os.path.relpath(file_path, os.environ.get('FOLDER_PATH'))
            path_parts = os.path.normpath(path_in_base_folder).split(os.path.sep)
            parent_folders = path_parts[:-1]
            layer_name, _ = os.path.splitext(path_parts[-1].lower().replace('&', ''))

            style_file_path = row[1].strip()
            if os.path.isfile(style_file_path):
                style_name = os.path.basename(style_file_path).replace(".sld", "")
            else:
                style_file_path = None
                style_name = layer_name + '_style'

            # check if already loaded in geoserver
            layer = geo.get_layer(layer_name, os.environ.get('GEOSERVER_WORKSPACE'))
            if layer:
                if isinstance(layer, str):
                    print(f"Error loading '{layer_name}': {layer}")
                    geoserver_upload_successful = False
                else:
                    print(f"'{layer_name}' already loaded in geoserver, skipping")
                    geoserver_upload_successful = True
            else:
                if file_path.endswith(tuple(os.environ.get('RASTER_EXTENSIONS').replace(" ", "").split(","))):
                    postgis_upload_successful = True  # raster not to postgis
                else:
                    # upload to postgis
                    postgis_upload_successful = load_wms_layer_postgis(
                        os.environ.get('POSTGRES_HOST'), os.environ.get('POSTGRES_PORT'),
                        os.environ.get('POSTGRES_USER'),
                        os.environ.get('POSTGRES_PASSWORD'), os.environ.get('POSTGRES_DB'), file_path, layer_name
                    )
                # postgis_upload_successful=True
                if postgis_upload_successful:
                    # upload to geoserver
                    if style_file_path:
                        geo.upload_style(path=style_file_path,
                                         name=style_name,
                                         workspace=os.environ.get('GEOSERVER_WORKSPACE'))
                    if file_path.endswith(tuple(os.environ.get('RASTER_EXTENSIONS').replace(" ", "").split(","))):
                        geo.create_coveragestore(layer_name=layer_name,
                                                 path=file_path,
                                                 workspace=os.environ.get('GEOSERVER_WORKSPACE'))
                        if not style_file_path:
                            geo.create_coveragestyle(raster_path=file_path,
                                                     style_name=style_name,
                                                     workspace=os.environ.get('GEOSERVER_WORKSPACE'),
                                                     color_ramp='nipy_spectral',
                                                     opacity=0.5)
                        geo.publish_style(layer_name=layer_name,
                                          style_name=style_name,
                                          workspace=os.environ.get('GEOSERVER_WORKSPACE'))
                    else:
                        geo.publish_featurestore(workspace=os.environ.get('GEOSERVER_WORKSPACE'),
                                                 store_name=os.environ.get('GEOSERVER_STORENAME'),
                                                 pg_table=layer_name)
                    geoserver_upload_successful = True

            if geoserver_upload_successful:
                # load folders and WMS layers into mongodb for mapeditor tree
                parent_folder_uuid = base_folder_uuid
                for folder_name in parent_folders:
                    parent_folder_uuid = add_wms_group(layer_groups, parent_folder_uuid, setting_type,
                                                       os.environ.get('PROJECT_NAME'), folder_name)
                add_wms_layer(
                    wms_layers,
                    layer_groups[parent_folder_uuid],
                    setting_type,
                    os.environ.get('PROJECT_NAME'),
                    layer_name,
                    f"{os.environ.get('GEOSERVER_URL')}/wms",
                    layer_name,
                    f"{os.environ.get('GEOSERVER_URL')}/wms/ows?service=WMS&request=GetLegendGraphic&"
                    f"FORMAT=image/png&LAYER={layer_name}&LEGEND_OPTIONS=fontsize:10;fontname:serif;fontColor:505050"
                )
            else:
                print(f"===== ERROR loading '{layer_name}' into postgis/geoserver, skipping layer")

    print(wms_layers)
    print(layer_groups)
    settings_storage.set(setting_type, identifier, LAYERS_SETTING, wms_layers)
    settings_storage.set(setting_type, identifier, LAYERS_GROUP_SETTING, layer_groups)


if __name__ == "__main__":
    load_layers()
