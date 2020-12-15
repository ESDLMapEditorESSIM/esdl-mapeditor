
from extensions.vue_backend.messages.DLA_table_data_message import DLA_table_data_request, DLA_table_data_response, \
    DLA_set_table_data_request
from pyecore.ecore import EObject, EReference, EClass
from esdl import esdl
from esdl.processing.ESDLQuantityAndUnits import qau_to_string
from esdl.processing import ESDLDataLayer
from dataclasses import asdict


def get_table_data(datalayer: ESDLDataLayer, parent: esdl.Item, table_data: DLA_table_data_request) \
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
        headerList = value.header
        for column in headerList:
            qau_string = qau_to_string(column)
            response.header.append(qau_string)
        for row in value.row:
            response.rows.append(convert_to_float_list(row.value))
    else:
        if table_data.ref_name is esdl.Pump.pumpCurveTable.eClass.name:
            print('Pump curve table requested')

            # create empty table, with correct header: Flow, Head, efficiency.
        else:
            # create empty table with no rows?
            pass
    print('returning table: ', response)
    return response

def set_table_data(parent: esdl.Pump, new_data: DLA_set_table_data_request):
    eclass: EClass = parent.eClass
    reference: EReference = eclass.findEStructuralFeature(new_data.ref_name)
    table: esdl.Table = parent.eGet(new_data.ref_name)
    table.name = new_data.name
    table.description = new_data.description
    # todo table.datasource
    if table is None:
        # create header
        pass
    else:
        row_list = table.row
        row_list.clear() # delete old data and create new
        for row in new_data.rows:
            r = esdl.TableRow()
            r.value = row
            row_list.append(r)
            print('table row:', r.value)


def convert_to_float_list(edouble_list: list):
    return [float(i) for i in edouble_list]


