// ------------------------------------------------------------------------------------------------------------
//  Boundary information from GEIS boundary service
// ------------------------------------------------------------------------------------------------------------
function boundary_info_window() {
    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>Boundary Information:</h1>';

    table = '<table>';
    table = table + '<tr><td width=180>Scope</td>';
    <!-- table = table + '<td><input type="text" width="60" id="scope" value="district"></td></tr>'; -->

    table = table + '<td><select id="scope">';
    table = table + '<option value="country">country</option>';
    table = table + '<option value="province">province</option>';
    table = table + '<option value="region">region</option>';
    table = table + '<option value="municipality" selected>municipality</option>';
    table = table + '<option value="district">district</option>';
    table = table + '<option value="neighbourhood">neighbourhood</option>';
    table = table + '</select></td></tr>';
    table = table + '<tr><td width=180>Identifier</td>';
    table = table + '<td><input type="text" width="60" id="identifier" value="GM0060"></td></tr>';

    table = table + '<tr><td width=180>Divide into subareas</td>';
    table = table + '<td><input type="checkbox" id="cb_subareas" checked></td></tr>';
    table = table + '<tr><td width=180>Subscope</td>';
    <!-- table = table + '<td><input type="text" width="60" id="subscope" value="neighbourhood"></td></tr>'; -->

    table = table + '<td><select id="subscope">';
    table = table + '<option value="country">country</option>';
    table = table + '<option value="province">province</option>';
    table = table + '<option value="region">region</option>';
    table = table + '<option value="municipality">municipality</option>';
    table = table + '<option value="district">district</option>';
    table = table + '<option value="neighbourhood" selected>neighbourhood</option>';
    table = table + '</select></td></tr>';

    table = table + '<tr><td width=180>Initialize energysystem</td>';
    table = table + '<td><input type="checkbox" id="initialize_ES" checked></td></tr>';
    table = table + '<tr><td width=180>Add boundaries to energysystem</td>';
    table = table + '<td><input type="checkbox" id="add_boundary_to_ESDL" disabled></td></tr>';
    table = table + '</table>';
    sidebar_ctr.innerHTML += table;

    sidebar_ctr.innerHTML += '<p><button onclick="sidebar.hide();get_boundary_info(this);">Request</button></p>';

    sidebar_ctr.innerHTML += '<h1>IBIS bedrijventerreien Information:</h1>';
    table = '<table>';
    table = table + '<tr><td width=180>RIN List</td>';
    table = table + '<td><input type="text" width="60" id="rin_list" value="777,779"></td></tr>';
    table = table + '<tr><td width=180>Initialize energysystem</td>';
    table = table + '<td><input type="checkbox" id="initialize_ES2" checked></td></tr>';
    table = table + '<tr><td width=180>Add boundaries to energysystem</td>';
    table = table + '<td><input type="checkbox" id="add_boundary_to_ESDL2" checked></td></tr>';
    table = table + '</table>';
    sidebar_ctr.innerHTML += table;
    sidebar_ctr.innerHTML += '<p><button onclick="sidebar.hide();get_ibis_info(this);">Request</button></p>';

    sidebar.show();
}

function get_boundary_info(obj) {
    identifier = document.getElementById('identifier').value;
    scope = document.getElementById('scope').value;
    subscope_enabled = document.getElementById('cb_subareas').checked;
    subscope = document.getElementById('subscope').value;
    initialize_ES = document.getElementById('initialize_ES').checked;
    add_boundary_to_ESDL = document.getElementById('add_boundary_to_ESDL').checked;

    show_loader();
    socket.emit('get_boundary_info', {identifier: identifier, scope: scope, subscope_enabled: subscope_enabled,
        subscope: subscope, initialize_ES: initialize_ES, add_boundary_to_ESDL: add_boundary_to_ESDL});
}

function get_ibis_info(obj) {
    initialize_ES = document.getElementById('initialize_ES2').checked;
    add_boundary_to_ESDL = document.getElementById('add_boundary_to_ESDL2').checked;
    rin_list = document.getElementById('rin_list').value;

    show_loader();
    socket.emit('ibis_bedrijventerreinen', {rin_list: rin_list,
        initialize_ES: initialize_ES, add_boundary_to_ESDL: add_boundary_to_ESDL});
}