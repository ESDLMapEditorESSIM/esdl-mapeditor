from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

@dataclass
class MetadataUpdateRequestBody:
    es_id: str

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
    CHART = "chart"
    TABLE = "table"

class ProfileVizType(Enum):
    PROFILE = "Profile"
    AGGREGATED = "Aggregated"

class ProfileAggInterval(Enum):
    WEEK = "Week"
    MONTH = "Month"
    QUARTER = "Quarter"
    YEAR = "Year"

class ProfileAggFunc(Enum):
    COUNT = "Count"
    MAX = "Max"
    MIN = "Min"
    SUM = "Sum"
    MEAN = "Mean"

@dataclass
class ProfileQueryOptions:
    viz_type: ProfileVizType
    data_range: List[str]
    agg_interval: Optional[ProfileAggInterval]
    agg_func: Optional[ProfileAggFunc]

@dataclass
class QueryRequestBody:
    dataset_ids: List[int]
    variable_name: str
    group_by: List[str]
    filters: Dict[str, List[str]]
    chart_type: ChartType
    profile: Optional[ProfileQueryOptions]