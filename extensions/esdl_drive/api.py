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
from typing import Any, Dict, Optional, TypedDict, Union

import requests

from extensions.session_manager import get_session
from src.settings import esdl_drive_config
from src import log

DRIVE_URL = esdl_drive_config["hostname"]
browse_endpoint = "/store/browse"
resource_endpoint = "/store/resource"
drive_name = "ESDl Drive"

logger = log.get_logger(__name__)


class EsdlDriveException(Exception):
    pass


class DrivePutParams(TypedDict):
    commitMessage: str
    overwrite: bool


def upload_to_drive(
    esdl_contents: Union[str, bytes],
    drive_path: str,
    putparams: DrivePutParams,
    headers: Optional[dict[str, str]] = None,
) -> requests.Response:
    """
    Upload the specified file to drive.

    Drive_path is the relative path within the drive. It should not include the hostname or drive.
    """
    logger.info(f"Writing to {drive_path}")
    if headers is None:
        headers = get_drive_post_headers()
    target_url = drive_path
    if DRIVE_URL not in target_url:
        target_url = f"{DRIVE_URL}{resource_endpoint}{drive_path}"

    response = requests.put(
        target_url, data=esdl_contents, headers=headers, params=putparams
    )
    if response.status_code > 400:
        logger.error(
            f"Error writing to ESDLDrive: headers={response.headers}, response={response.content}"
        )
    else:
        logger.info(
            f"Saved successfully to ESDLDrive {drive_path} (HTTP status: {response.status_code}) "
        )
    return response


class GetNodeDriveItem(TypedDict):
    # Name
    text: str
    # Path
    id: str
    icon: str
    type: str
    writable: bool
    children: bool


def get_node_drive(
    path: str,
    headers: Optional[dict[str, str]] = None,
) -> list[GetNodeDriveItem]:
    """
    Browse the ESDL Drive.
    """
    return do_browse_drive("get_node", path, headers=headers)


def do_browse_drive(
    operation: str,
    path: str,
    depth: Optional[int] = None,
    headers: Optional[dict[str, str]] = None,
) -> list[dict[str, Any]]:
    """
    Browse the ESDL Drive.
    """
    if headers is None:
        headers = get_drive_headers()
    params = dict(
        operation=operation,
        id=path,
        depth=depth,
    )
    response = requests.get(
        f"{DRIVE_URL}{browse_endpoint}", params=params, headers=headers
    )
    if not response.ok:
        raise EsdlDriveException(f"Failed communicating with ESDL Drive: {response.status_code}")
    return response.json()


def get_drive_headers() -> Dict[str, str]:
    token = get_session("jwt-token")
    headers = {"Authorization": f"Bearer {token}"}
    return headers


def get_drive_post_headers() -> Dict[str, str]:
    """
    Build authorization header for the ESDL drive.
    """
    headers = get_drive_headers()
    headers["Content-Type"] = "application/xml"
    return headers
