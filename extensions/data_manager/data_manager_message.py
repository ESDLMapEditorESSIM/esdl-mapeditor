from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


@dataclass
class MetadataUpdateRequestBody:
    es_id: str
    energyUnit: str

@dataclass
class MetadataDeleteRequestBody:
    dataset_name: Optional[str]

@dataclass
class MetadataOperationResp:
    status: str
    message: str

@dataclass
class GetVariablesRequestBody:
    dataset_ids: List[int]

@dataclass
class GetColumnsRequestBody:
    dataset_ids: List[int]
    variable_name: str

class ChartType(Enum):
    BAR = "bar"
    TABLE = "table"

@dataclass
class QueryRequestBody:
    dataset_ids: List[int]
    variable_name: str
    group_by: List[str]
    filters: Dict[str, List[str]]
    chart_type: ChartType