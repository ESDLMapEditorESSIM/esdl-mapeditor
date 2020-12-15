from dataclasses import dataclass, field
from typing import List, Any
from extensions.vue_backend.messages.identifier_message import Identifier

@dataclass
class DLA_table_data_request:
    """ defines the message that is send from the frontend to get table data """
    parent_id: Identifier
    ref_name: str
    ref_type: str

@dataclass
class DLA_table_data_response:
    """ defines the message that is send from the frontend to get table data """
    name: str = None
    description: str = None
    header: List = field(default_factory=list)
    rows: List[List[float]] = field(default_factory=list)
    datasource: str = None

@dataclass
class DLA_set_table_data_request:
    """ defines the message that is send from the frontend to set table data """
    parent_id: Identifier
    ref_name: str
    ref_type: str
    name: str
    description: str
    header: List
    rows: List[List[Any]]
