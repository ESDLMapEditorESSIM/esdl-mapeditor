import base64
import traceback
import uuid
from typing import Dict

from flask import Flask, request
from flask_executor import Executor
from flask_socketio import SocketIO
from pyecore.resources import ResourceSet

import esdl
import src.log as log
from esdl import EnergySystem, TimeSeriesProfile, InfluxDBProfile
from esdl.processing.string_uri import StringURI
from esdl.profiles.influxdbprofilemanager import InfluxDBProfileManager, ConnectionSettings
from esdl.project.ProjectManager import load_external_string
from extensions.profiles import Profiles
from extensions.prompt_manager import PromptManager
from extensions.session_manager import set_session, get_project_manager, get_session
from src.process_es_area_bld import process_energy_system, call_process_energy_system
from src.tno.projects.duplicate_detection import (
    DuplicateChoice,
    DuplicatePrompt,
    find_duplicate_variant_collection,
    generate_renamed_esdl_string,
    next_available_name,
)

logger = log.get_logger(__name__)

ESDL_DUPLICATE_INLINE_IMPORT = "esdl_duplicate_inline_import"


def handle_esdl_duplicate_inline_import(choice_key: str, context: dict):
    """Apply user choice for duplicate inline-import prompts."""
    pm = get_project_manager()
    filename = context.get("filename")
    file_content = context.get("file_content")
    if not filename or not file_content:
        logger.warning("Missing context for inline import prompt")
        return

    if choice_key == DuplicateChoice.CANCEL:
        return

    temp_es, _ = load_external_string(name=filename, esdl_string=file_content)

    if choice_key == DuplicateChoice.OVERWRITE:
        duplicate_vc, _, _, _ = find_duplicate_variant_collection(pm, temp_es.id, temp_es.name)
        if duplicate_vc:
            pm.delete_variant(duplicate_vc)
    elif choice_key == DuplicateChoice.RENAME:
        new_name = next_available_name(pm, temp_es.name)
        file_content = generate_renamed_esdl_string(file_content, filename, new_name=new_name)

    variant, parse_info = pm.add_energy_system(StringURI(filename, file_content))
    pm.set_active_variant(variant)
    imported_es = pm.get_energy_system(variant)
    if len(parse_info) > 0:
        info = ""
        for line in parse_info:
            info += line + "\n"
        logger.warning("Warnings while importing {}:\n\n{}".format(filename, info))
    set_session('active_es_id', imported_es.id)
    set_session('es_filename', filename)
    call_process_energy_system.submit(force_update_es_id=imported_es.id)


PromptManager.register_handler(ESDL_DUPLICATE_INLINE_IMPORT, handle_esdl_duplicate_inline_import)


class ESDLFileImport:
    def __init__(self, flask_app: Flask, socket: SocketIO, executor: Executor):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()
        self.executor = executor

    def register(self):
        logger.info('Registering ESDL File Import extension')

        @self.flask_app.route("/esdl_file_import", methods=['POST'])
        def esdl_file_import():
            with self.flask_app.app_context():
                pm = get_project_manager()

                filename = request.values.get('filename')

                base64_file_contents = request.values.get('file_content')
                base64_file_contents = base64_file_contents.split(',')[1]
                esdlstr_base64_bytes = base64_file_contents.encode('utf-8')
                esdlstr_bytes = base64.b64decode(esdlstr_base64_bytes)
                file_content = esdlstr_bytes.decode('utf-8')

                inline = request.values.get('inline')

                try:
                    if inline == 'true':  # silly js to python conversion
                        logger.info("Importing inline ESDL")
                        # inline_esh = EnergySystemHandler()  # TODO: or use esh.load_external_string()?
                        inline_es, parse_info = load_external_string(name=filename, esdl_string=file_content)
                        inline_es = self.convert_inline_to_influx(inline_es)
                        inline_es.name = inline_es.name.replace(" - In-line Profiles", "")

                        uri = StringURI('es_converted.esdl')
                        es_converted_resource = ResourceSet().create_resource(uri)
                        es_converted_resource.append(inline_es)
                        es_converted_resource.save(uri)
                        file_content = uri.getvalue()
                        logger.debug("Inline ESDL converted to InfluxDB profiles")

                    temp_es, parse_info = load_external_string(name=filename, esdl_string=file_content)
                    duplicate_vc, match_id, match_name, matched_es = find_duplicate_variant_collection(
                        pm, temp_es.id, temp_es.name
                    )
                    if duplicate_vc:
                        user_email = get_session("user-email")
                        details = "\n".join(parse_info) if parse_info else None
                        PromptManager.get_instance().send(DuplicatePrompt(
                            user_email=user_email,
                            continuation_id=ESDL_DUPLICATE_INLINE_IMPORT,
                            match_id=match_id,
                            match_name=match_name,
                            matched_es=matched_es,
                            context={
                                "filename": filename,
                                "file_content": file_content,
                            },
                            details=details,
                        ))
                        return {'status': 'pending_prompt'}, 202

                    variant, parse_info = pm.add_energy_system(StringURI(filename, file_content))
                    pm.set_active_variant(variant)
                    imported_es = pm.get_energy_system(variant)

                    if len(parse_info) > 0:
                        info = ''
                        for line in parse_info:
                            info += line + "\n"
                    set_session('active_es_id', imported_es.id)
                    set_session('es_filename', filename)

                    return {'message': 'ESDL imported'}, 201
                except Exception as e:
                    logger.error("Error importing {}: {}".format(filename, e))
                    PromptManager.get_instance().send_error(
                        user_email=get_session("user-email"),
                        title=f"Error importing {filename}",
                        exception=e,
                        details=traceback.format_exc(),
                    )
                    return {'status': 'error_prompt_sent'}, 200


        @self.socketio.on("process_imported_energysystem", namespace='/esdl')
        def process_imported_energysystem():
            call_process_energy_system.submit()

    @staticmethod
    def convert_asset_inline_profiles_to_influx(asset: esdl.Asset) -> esdl.Asset:
        area = esdl.Area(id=str(uuid.uuid4()), name="Service result", asset=[asset])
        energy_system = esdl.EnergySystem(
            id=str(uuid.uuid4()),
            name="Service result",
            energySystemInformation=esdl.EnergySystemInformation(
                id=str(uuid.uuid4()),
                profiles=esdl.Profiles(id=str(uuid.uuid4())),
            ),
            instance=[
                esdl.Instance(
                    id=str(uuid.uuid4()),
                    name="Service result",
                    area=area,
                )
            ],
        )
        ESDLFileImport.convert_inline_to_influx(energy_system)
        area.asset.remove(asset)
        return asset

    @staticmethod
    def convert_inline_to_influx(inline_es: EnergySystem) -> EnergySystem:
        inline_esi = inline_es.energySystemInformation

        prof_servers = Profiles.get_instance().get_profiles_settings()["profiles_servers"]
        if len(prof_servers) == 0:
            raise Exception("No profiles servers found in profiles settings.")
        prof_server = prof_servers[0]  # TODO: ugly and potentially incorrect
        influxdb_settings = ConnectionSettings(
            host=prof_server["host"],
            port=int(prof_server["port"]),
            database=prof_server["database"],
            username=prof_server["username"],
            password=prof_server["password"],
            ssl=prof_server.get("ssl_enabled", False),
            verify_ssl=prof_server.get("ssl_enabled", False),
        )

        handled_profiles: Dict[str, esdl.InfluxDBProfile] = {}
        prof_manager = InfluxDBProfileManager(influxdb_settings)
        existing_profiles: dict[str, tuple[str, str]] = {}
        result = prof_manager.influxdb_client.query("SHOW FIELD KEYS")
        for (measurement_name, _), fields in result.items():
            for field in fields:
                field_key = field["fieldKey"]
                existing_profiles[f"{measurement_name}_{field_key}"] = (measurement_name, field_key)

        def _create_influxdb_profile(prof: TimeSeriesProfile, multiplier: float | None = None):
            prof_manager.parse_esdl(prof)
            # profile_header[1] should now be prof.name which is a concatenation of measurement and field
            # if this profile was converted from an InfluxDBProfile to TimeSeriesProfile.
            field_name = prof_manager.profile_header[1]
            field_name_split = field_name.split("_")
            measurement = inline_esi.id.replace("-", "_")

            # If the profile is based on a default profile we don't need to save it to the database,
            # and we can create a profile directly.
            if field_name.startswith("standard_profiles_point"):
                field_name = "_".join(field_name_split[3:])
                measurement = "_".join(field_name_split[:3])
                influx_profile = prof_manager.get_esdl_influxdb_profile(measurement, [field_name])
            # TODO: elif field_name.startswith("standard_profiles"):
            elif field_name.startswith("bedrijfstijden_profielen"):
                field_name = "_".join(field_name_split[2:])
                measurement = "_".join(field_name_split[:2])
                influx_profile = prof_manager.get_esdl_influxdb_profile(measurement, [field_name])
            elif field_name.startswith("KIP_EH_profielen_point"):
                field_name = "_".join(field_name_split[4:])
                measurement = "_".join(field_name_split[:4])
                influx_profile = prof_manager.get_esdl_influxdb_profile(measurement, [field_name])
            # TODO: elif field_name.startswith("KIP_EH_profielen"):
            else:
                if prof.name in existing_profiles:
                    measurement, field_name = existing_profiles[prof.name]
                    influx_profile = prof_manager.get_esdl_influxdb_profile(
                        measurement, [field_name]
                    )
                else:
                    # Unknown profiles need their own series in the database.
                    # TODO: we could create a panel for these profiles...
                    field_name = f"{(prof.id or str(uuid.uuid4()))}"
                    prof_manager.profile_header[1] = field_name
                    influx_profile = prof_manager.save_influxdb(
                        measurement=measurement,
                        field_names=[prof_manager.profile_header[1]],
                    )
            influx_profile.name = prof.name  # equal to f"{measurement}_{field_name}" for standard profiles and a UUID for custom profiles
            influx_profile.profileType = prof.profileType
            if prof.profileQuantityAndUnit is not None:
                influx_profile.profileQuantityAndUnit = prof.profileQuantityAndUnit.deepcopy()
            if multiplier is not None:
                influx_profile.multiplier = multiplier
            # Fix to fix temporary fix in profile manager that removes http from host
            if not influx_profile.host.startswith("http"):
                influx_profile.host = f"http://{influx_profile.host}"
            handled_profiles[prof.name] = influx_profile

        def _convert_profile_for_port(port: esdl.Port):
            port_profiles_remove = []
            port_profiles_add = []

            def add_handled_profile(handled_profile: esdl.InfluxDBProfile, multiplier: float):
                influx_profile = InfluxDBProfile(
                    id=str(uuid.uuid4()),
                    name=handled_profile.name,
                    host=handled_profile.host,
                    port=handled_profile.port,
                    database=handled_profile.database,
                    measurement=handled_profile.measurement,
                    field=handled_profile.field,
                    filters=handled_profile.filters,
                    startDate=handled_profile.startDate,
                    endDate=handled_profile.endDate,
                    multiplier=multiplier,
                    profileType=handled_profile.profileType,
                )
                if handled_profile.profileQuantityAndUnit is not None:
                    quantity = handled_profile.profileQuantityAndUnit.deepcopy()
                    quantity.id = str(uuid.uuid4())
                    influx_profile.profileQuantityAndUnit = quantity
                port_profiles_add.append(influx_profile)

            for profile in port.profile:
                if isinstance(profile, esdl.TimeSeriesProfile):
                    profile_name = profile.name

                    if profile_name not in handled_profiles:
                        _create_influxdb_profile(profile, multiplier=None)

                    handled_influx_profile = handled_profiles[profile_name]
                    assert isinstance(handled_influx_profile, esdl.InfluxDBProfile)
                    add_handled_profile(handled_influx_profile, multiplier=1.0)
                    port_profiles_remove.append(profile)
                elif isinstance(profile, esdl.ProfileReference):
                    # Reference of ProfileReference should be TimeSeriesProfile
                    if not isinstance(profile.reference, esdl.TimeSeriesProfile):
                        return

                    referenced_profile: esdl.TimeSeriesProfile = profile.reference
                    profile_name = referenced_profile.name

                    if profile_name not in handled_profiles:
                        _create_influxdb_profile(referenced_profile, profile.multiplier)

                    handled_influx_profile = handled_profiles[profile_name]
                    assert isinstance(handled_influx_profile, esdl.InfluxDBProfile)
                    add_handled_profile(handled_influx_profile, multiplier=profile.multiplier)
                    port_profiles_remove.append(profile)

            # Update port profiles after iterating to avoid changing the list while iterating
            for profile in port_profiles_add:
                port.profile.append(profile)
            for profile in port_profiles_remove:
                port.profile.remove(profile)

        def _convert_asset_profiles(asset: esdl.Asset):
            if hasattr(asset, 'port'):
                in_ports = [port for port in asset.port if isinstance(port, esdl.InPort)]
                for in_port in in_ports:
                    _convert_profile_for_port(in_port)

                out_ports = [port for port in asset.port if isinstance(port, esdl.OutPort)]
                for out_port in out_ports:
                    _convert_profile_for_port(out_port)

            if hasattr(asset, 'asset'):  # Recursively convert profiles of sub-assets
                for sub_asset in asset.asset:
                    _convert_asset_profiles(sub_asset)

        global_timeseries_profiles = [profile for profile in inline_esi.profiles.profile if isinstance(profile, esdl.TimeSeriesProfile)]
        for timeseries_profile in global_timeseries_profiles:
            if timeseries_profile.name not in handled_profiles:
                _create_influxdb_profile(timeseries_profile, multiplier=None)

        # Start conversion of the energy system
        # Convert profiles of each asset to InfluxDB profiles
        for area in inline_es.eAllContents():
            if isinstance(area, esdl.Area):
                for area_asset in area.asset:
                    _convert_asset_profiles(area_asset)
        # The TimeSeriesProfiles referenced in the assets should all be converted now, so we can remove them
        # (and for sake of completeness add InfluxDBProfiles in their place
        global_timeseries_profiles = [profile for profile in inline_esi.profiles.profile if isinstance(profile, esdl.TimeSeriesProfile)]
        for timeseries_profile in global_timeseries_profiles:
            if timeseries_profile.name not in handled_profiles:
                _create_influxdb_profile(timeseries_profile, multiplier=None)

            global_influx_profile = handled_profiles[timeseries_profile.name]
            assert isinstance(global_influx_profile, esdl.InfluxDBProfile)
            inline_esi.profiles.profile.append(global_influx_profile)
            inline_esi.profiles.profile.remove(timeseries_profile)

        return inline_es
