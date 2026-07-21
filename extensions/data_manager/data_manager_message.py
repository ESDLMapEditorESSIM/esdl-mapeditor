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

@dataclass
class SaveGraphConfigsRequestBody:
    configs: List[dict]

class ChartType(Enum):
    CHART = "chart"
    TABLE = "table"
    LDC = "ldc"
    HIST = "hist"

class ProfileVizType(Enum):
    PROFILE = "Profile"
    AGGREGATED = "Aggregated"

class ProfileAggInterval(Enum):
    WEEK = "Week"
    MONTH = "Month"
    QUARTER = "Quarter"
    YEAR = "Year"

class ProfileAggFunc(Enum):
    """
    Aggregation functions to be applid on group_by categories or time interval.
    """
    COUNT = "Count"
    MAX = "Max"
    MIN = "Min"
    SUM = "Sum"
    MEAN = "Mean"

@dataclass
class ProfileQueryOptions:
    viz_type: ProfileVizType
    data_range: List[str]
    group_by_enabled: bool
    group_by_agg_func: Optional[ProfileAggFunc]
    """Function to be applied when aggregating on group_by categories."""
    max_datapoints: Optional[int]
    """If specified, downsample profile data to approximately the given value."""
    agg_interval: Optional[ProfileAggInterval]
    agg_func: Optional[ProfileAggFunc]
    """Function to be applied when aggregating on time interval."""

@dataclass
class QueryRequestBody:
    dataset_ids: List[int]
    variable_name: str
    group_by: List[str]
    filters: Dict[str, List[str]]
    chart_type: ChartType
    profile: Optional[ProfileQueryOptions]