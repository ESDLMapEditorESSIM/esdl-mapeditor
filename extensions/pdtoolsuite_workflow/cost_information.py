import base64
from werkzeug.http import parse_options_header
import os
from typing import Tuple
from flask import Flask, jsonify, request
import requests

from extensions.session_manager import get_session, get_project_manager
from src.log import get_logger
from src.esdl_config import ESDL_COST_SERVICE_HOST

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 30

# TODO: put this here, or embed in the pdtoolsuite_workflow.py file?

class CostInformation:
    def __init__(self, flask_app: Flask):
        self.flask_app = flask_app
        self.register()

    def register(self):
        logger.info('Registering CostInformation extension')

        @self.flask_app.route("/cost_information/template", methods=["POST"])
        def generate_cost_information_template():
            url = f"{ESDL_COST_SERVICE_HOST}/cost-information/generate"
            active_es_id = get_session("active_es_id")
            pm = get_project_manager()

            base64_es = base64.b64encode(
                pm.energy_system_to_string(active_es_id).encode("utf-8")
            ).decode()
            payload = dict(
                energysystem=base64_es,
            )

            r = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
            return jsonify(r.json())

        @self.flask_app.route("/cost_information/template/progress/<process_id>", methods=["GET"])
        def get_cost_information_template_generate_progress(process_id: str):
            status, progress = _get_progress(process_id)

            if status == "running":
                return dict(
                    progress=progress,
                    message="Generating cost information template. Please don't close this screen.",
                )
            elif status == "finished":
                content, filename = _download_result(process_id)
                base64_file = base64.b64encode(content).decode()

                return jsonify(dict(
                    base64file=base64_file,
                    filename=filename,
                    progress=100,
                    message="Cost information template generated successfully. It should be downloaded automatically.",
                )), 200
            else:
                return dict(
                    progress="err",
                    message="Error while generating cost information template.",
                )

        @self.flask_app.route("/cost_information/template/upload", methods=["POST"])
        def upload_cost_information_template():
            base64_file = request.json["base64_file"]
            cost_information_upload_file = base64.b64decode(base64_file, b"-_")
            url = f"{ESDL_COST_SERVICE_HOST}/cost-information/parse"
            active_es_id = get_session("active_es_id")
            pm = get_project_manager()
            base64_es = base64.b64encode(
                pm.energy_system_to_string(active_es_id).encode("utf-8")
            ).decode()
            files = dict(
                energysystem=base64_es,
                template_excel=cost_information_upload_file,
            )

            r = requests.post(url, files=files, timeout=DEFAULT_TIMEOUT)
            return jsonify(r.json())


        @self.flask_app.route("/cost_information/template/upload/progress/<process_id>", methods=["GET"])
        def get_cost_information_template_upload_progress(process_id: str):
            status, progress = _get_progress(process_id)

            if status == "running":
                return dict(
                    progress=progress,
                    message="Uploading cost information template. Please don't close this screen.",
                )
            elif status == "finished":
                content, filename = _download_result(process_id)
                pm = get_project_manager()
                pm.add_from_string(filename, content.decode("utf-8"))

                return jsonify(dict(
                    filename=filename,
                    progress=100,
                    message="Cost information template uploaded successfully. It should be become visible as new ESDL layer automatically.",
                )), 200
            else:
                return dict(
                    progress="err",
                    message="Error while uploading cost information template.",
                )


def _get_progress(process_id: str) -> Tuple[str, int]:
    url = f"{ESDL_COST_SERVICE_HOST}/cost-information/{process_id}/progress"
    r = requests.get(url, timeout=DEFAULT_TIMEOUT)
    response = r.json()
    logger.info("Response", json=response)
    
    status = response.get("status", "error")
    progress = response.get("progress", 0)

    return status, progress


def _download_result(process_id: str) -> Tuple[bytes, str]:
    url = f"{ESDL_COST_SERVICE_HOST}/cost-information/{process_id}/result"
    r = requests.get(url, timeout=DEFAULT_TIMEOUT)
    parsed_header = parse_options_header(r.headers["Content-Disposition"])[-1]
    filename = os.path.basename(parsed_header["filename"])
    return r.content, filename
