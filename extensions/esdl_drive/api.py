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
from typing import Optional, TypedDict, Union

import requests

from extensions.session_manager import get_session
from src.settings import esdl_drive_config
from src import log

DRIVE_URL = esdl_drive_config['hostname']
browse_endpoint = "/store/browse"
resource_endpoint = "/store/resource"
drive_name = "ESDl Drive"

logger = log.get_logger(__name__)


class DrivePutParams(TypedDict):
    commitMessage: str
    overwrite: bool


def upload_to_drive(esdl_contents: Union[str, bytes], drive_path: str, putparams: DrivePutParams, headers: Optional[dict] = None) -> requests.Response:
    """
    Upload the specified file to drive.

    Drive_path is the relative path within the drive. It should not include the hostname or drive.
    """
    logger.info(f"Writing to {drive_path}")
    if headers is None:
        token = get_session('jwt-token')
        headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/xml'}
    target_url = f"{DRIVE_URL}/{drive_path}"
    response = requests.put(target_url, data=esdl_contents, headers=headers, params=putparams)
    if response.status_code > 400:
        logger.error( f"Error writing to ESDLDrive: headers={response.headers}, response={response.content}")
    else:
        logger.info(f'Saved successfully to ESDLDrive {drive_path} (HTTP status: {response.status_code}) ')
    return response
