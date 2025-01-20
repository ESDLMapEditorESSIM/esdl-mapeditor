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

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class OwnershipParty:
    id: str
    name: str
    short_name: str


@dataclass
class GetPartiesResp:
    parties: List[OwnershipParty]


@dataclass
class OwnershipAsset:
    id: str
    name: str
    is_owned_by: Optional[OwnershipParty]


@dataclass
class GetAssetsResp:
    assets: List[OwnershipAsset]


@dataclass
class Assignment:
    assigned_asset_ids: List[str]
    revoked_asset_ids: List[str]
