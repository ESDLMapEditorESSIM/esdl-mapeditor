
from extensions.vue_backend.messages.DLA_table_data_message import DLA_table_data_request, DLA_table_data_response, \
    DLA_set_table_data_request, ColumnHeader
from pyecore.ecore import EReference, EClass
from esdl import esdl
from esdl.processing.ESDLQuantityAndUnits import qau_to_string
from typing import List
from src.log import get_logger

log = get_logger(__name__)

def get_table_data(datalayer, parent: esdl.Item, table_data: DLA_table_data_request) \
        -> DLA_table_data_response:
    """
    param: datalayer - to check for global QaU
    param: parent - the parent object (e.g. asset) that contains the Table reference for which we want the data
    param: table_data - DLA_table_data_request that contains the reference name and type

    returns: DLA_table_data_response dataclass with header and row
    """
    eclass: EClass = parent.eClass
    reference: EReference = eclass.findEStructuralFeature(table_data.ref_name)
    value: esdl.Table = parent.eGet(table_data.ref_name)

    response = DLA_table_data_response()
    if not reference.eType.eClass.name == table_data.ref_type:
        print("Not a Table reference!")
        return response

    if value is not None:
        response.name = value.name
        response.description = value.description
        headerList: List[esdl.AbstractQuantityAndUnit] = value.header
        for column in headerList:
            if isinstance(column, esdl.QuantityAndUnitType):
                qau_string = qau_to_string(column)
                h = ColumnHeader(title=qau_string, id=column.id)
            elif isinstance(column, esdl.QuantityAndUnitReference):
                qau_string = qau_to_string(column.reference)
                h = ColumnHeader(title=qau_string, id=column.reference.id)
            response.header.append(h)
        for row in value.row:
            response.rows.append(convert_to_float_list(row.value))
    else:
        if isinstance(parent, esdl.Pump) and table_data.ref_name == esdl.Pump.pumpCurveTable.name:
            # create empty table, with correct header: Flow, Head, efficiency from global QuA
            print('New Pump curve table requested')
            flow_qau = datalayer.get_or_create_qau('flow')
            head_qau = datalayer.get_or_create_qau('head')
            efficiency_qau = datalayer.get_or_create_qau('efficiency')
            response.header.append(ColumnHeader(title=qau_to_string(flow_qau), id=flow_qau.id))
            response.header.append(ColumnHeader(title=qau_to_string(head_qau), id=head_qau.id))
            response.header.append(ColumnHeader(title=qau_to_string(efficiency_qau), id=efficiency_qau.id))
            response.rows.append([0.0] * len(response.header))  # first empty row
            response.name = "Pump curve data"
        if isinstance(parent, esdl.CheckValve) and table_data.ref_name == esdl.CheckValve.flowCoefficient.name:
            print('New flow coefficient table requested')
            position_qau = datalayer.get_or_create_qau('position')
            kv_qau = datalayer.get_or_create_qau('kv_coefficient')
            response.header.append(ColumnHeader(title=qau_to_string(position_qau), id=position_qau.id))
            response.header.append(ColumnHeader(title=qau_to_string(kv_qau), id=kv_qau.id))
            response.rows.append([0.0] * len(response.header))  # first empty row
            response.name = "Flow coefficient data"
        else:
            # create empty table with no rows?
            pass
    print('returning table: ', response)
    return response

def set_table_data(datalayer, parent: esdl.Item, new_data: DLA_set_table_data_request):
    #eclass: EClass = parent.eClass
    #reference: EReference = eclass.findEStructuralFeature(new_data.ref_name)
    table: esdl.Table = parent.eGet(new_data.ref_name)

    # todo table.datasource

    if table is None:
        # todo data source
        table = esdl.Table(name=new_data.name, description=new_data.description)
        parent.eSet(new_data.ref_name, table)
        # create header
        headerList = table.header
        if isinstance(parent, esdl.Pump) and new_data.ref_name == esdl.Pump.pumpCurveTable.name:
            flow_qau = datalayer.get_or_create_qau('flow')
            head_qau = datalayer.get_or_create_qau('head')
            efficiency_qau = datalayer.get_or_create_qau('efficiency')
            headerList.append(esdl.QuantityAndUnitReference(reference=flow_qau))
            headerList.append(esdl.QuantityAndUnitReference(reference=head_qau))
            headerList.append(esdl.QuantityAndUnitReference(reference=efficiency_qau))
        if isinstance(parent, esdl.CheckValve) and new_data.ref_name == esdl.CheckValve.flowCoefficient.name:
            position_qau = datalayer.get_or_create_qau('position')
            kv_qau = datalayer.get_or_create_qau('kv_coefficient')
            headerList.append(esdl.QuantityAndUnitReference(reference=position_qau))
            headerList.append(esdl.QuantityAndUnitReference(reference=kv_qau))

        table.name = new_data.name
        table.description = new_data.description
        # assume headers haven't changed
        row_list = table.row
        row_list.clear() # delete old data and create new
        for row in new_data.rows:
            r = esdl.TableRow()
            r.value.extend(convert_to_float_list(row))
            row_list.append(r)
            print('table row:', r.value)
        print()
    else:
        log.error('Can\'t update table: Not a pump or incorrect reference for pump curve table')


def convert_to_float_list(edouble_list: list):
    return [float(i) for i in edouble_list]


