from enum import Enum

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
import sqlalchemy as sa

from extensions.data_manager import db


class DataType(Enum):
    SINGLE_VALUE = 0
    PROFILE = 1
    FLOW = 2


class BaseModel(db.Model):
    """
    A base model containing an ID primary key
    """

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)


class TimedBaseModel(BaseModel):
    """Adds created and updated columns"""

    __abstract__ = True

    created = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class DataSet(TimedBaseModel):
    __tablename__ = "dataset"
    """ Describes data sets that exists of variables and data"""
    name = db.Column(db.String, nullable=False)  # name should be unique per owner (created_by)
    description = db.Column(db.String)  # short description of this dataset
    model = db.Column(db.String)  # which model generated this dataset
    run_timestamp = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now()
    )  # when was this dataset created
    created_by = db.Column(db.String, nullable=False)  # who created this dataset
    public = db.Column(db.Boolean, nullable=False, default=False)  # defines if a model is publicly accessible
    security = db.Column(JSONB)  # arbitrary access control e.g. { 'owner': 'joost', shared_with': ['ewoud', 'edwin', 'wester']}
    energy_system_id = db.Column(db.String, nullable=False)  # reference to the energy system id if using an ESDL file

    __table_args__ = (
        sa.UniqueConstraint('name', 'created_by', name='owner_unique_ds'),
    )

    def __init__(
        self,
        name: str,
        created_by: str,
        description: str = None,
        model: str = None,
        energy_system_id: str = None,
    ):
        self.name = name
        self.description = description
        self.model = model
        self.created_by = created_by
        self.energy_system_id = energy_system_id


class Variable(BaseModel):
    __tablename__ = "variable"
    """ Describes a variable and its metadata """
    dataset_id = db.Column(db.Integer, db.ForeignKey(DataSet.id), nullable=False)
    dataset = db.relationship(DataSet, cascade="all, delete")
    name = db.Column(db.String, nullable=False)  # variable name belonging to this dataset, machine-readable
    unit = db.Column(db.String, nullable=False)  # unit of variable (e.g. PJ, MWh, MW)
    quantity = db.Column(db.String, nullable=False)  # quantity (e.g. Energy, Power, COST, FLOW_RATE)
    datatype = db.Column(sa.Enum(DataType))
    description = db.Column(db.String, nullable=True)  # human description of this variable (e.g. Primary energy mix)
    input_description = db.Column(db.String, nullable=True)  # human description of the input field in data (e.g. Fuel)
    output_description = db.Column(db.String, nullable=True)  # human description of the output (e.g. Energy carrier)
    labels = db.Column(JSONB)  # extra labels for this variable
    filter_options = db.Column(JSONB)

    def __init__(
        self,
        name: str,
        unit: str,
        quantity: str,
        datatype: DataType,
        description: str = None,
        input_description: str = None,
        output_description: str = None,
    ):
        self.name = name
        self.unit = unit
        self.quantity = quantity
        self.datatype = datatype
        if description is not None:
            self.description = description
        if input_description is not None:
            self.input_description = input_description
        if output_description is not None:
            self.output_description = output_description


class Data(BaseModel):
    """
    Describes the actual data
    """

    __tablename__ = "data"
    dataset_id = db.Column(db.Integer, db.ForeignKey(DataSet.id), nullable=False)
    dataset = db.relationship(DataSet, cascade="all, delete")
    variable_id = db.Column(db.Integer, db.ForeignKey(Variable.id), nullable=False)
    variable = db.relationship(Variable, cascade="all, delete")
    value = db.Column(db.Float, nullable=True)
    sector = db.Column(db.String)  # TODO: add hierarchy, for now using | as separator
    region = db.Column(db.String)  # TODO: add hierarchy, for now using | as separator, JSON would also be an option?
    node = db.Column(db.String)  # fromNode for FLOW data
    to_node = db.Column(db.String)  # for FLOW data
    output = db.Column(db.String)  # output (e.g. Electricity as Energy Carrier)
    input = db.Column(db.String)  # input (e.g. Wind as Fuel)
    technology = db.Column(db.String)
    year = db.Column(db.Integer)  # year as integer, e.g. 2030, 2040
    datetime = db.Column(db.DateTime)  # for timeseries data
    labels = db.Column(JSONB)  # extra labels for this datapoint using JSON
