// ------------------------------------------------------------------------------------------------------------
//  Boundary information from GEIS boundary service
// ------------------------------------------------------------------------------------------------------------
var boundaries_list = ["country", "province", "region", "municipality", "district", "neighbourhood"];

function get_subboundaries(scope) {
    let result = [];
    let start_copy = false;
    for (let i=0; i<boundaries_list.length; i++) {
        if (start_copy) {
            result.push(boundaries_list[i]);
        } else {
            if (scope === boundaries_list[i]) start_copy = true;
        }
    }
    return result;
}

function add_subboundaries(element_id, scope) {
    // update list of possible subboundaries
    let possible_subboundaries = get_subboundaries(scope);
    let subscope_select = document.getElementById(element_id)
    let list_len = subscope_select.options.length - 1;
    for (let i = list_len; i >= 0; i--) {
        subscope_select.remove(i);
    }

    for (let i=0; i<possible_subboundaries.length; i++) {
        let sub_bndr = possible_subboundaries[i];
        let option = document.createElement("option");
        option.text = sub_bndr;
        option.value = sub_bndr;
        subscope_select.add(option);
    }
    subscope_select.selectedIndex = 0;
}

function show_filter_row(filter_type, filter_list) {
    if (filter_type) {
        document.getElementById('tr_filter_type').style.display = 'table-row';
    } else {
        document.getElementById('tr_filter_type').style.display = 'none';
    }

    if (filter_list) {
        document.getElementById('tr_filter_list').style.display = 'table-row';
    } else {
        document.getElementById('tr_filter_list').style.display = 'none';
    }
}

function select_area_scope() {
    let selected_scope = document.getElementById('scope').options[document.getElementById('scope').selectedIndex].value;

    add_subboundaries('subscope', selected_scope);

    // show/hide filter rows and
    if (selected_scope === 'municipality') {
        show_filter_row(true, true);

        let select_element = document.getElementById('select_filter_type');
        let list_len = select_element.options.length - 1;
        for(let i = list_len; i >= 0; i--) {
            select_element.remove(i);
        }

        let option = document.createElement("option");
        option.text = 'province';
        option.value = 'province';
        select_element.add(option);
        option = document.createElement("option");
        option.text = 'region';
        option.value = 'region';
        select_element.add(option);
        select_element.selectedIndex = 0;       // select first option ('province')

        change_filter_type();
    } else if (selected_scope === 'district' || selected_scope === 'neighbourhoud') {
        show_filter_row(false, true);

        let select_element = document.getElementById('select_filter_type');
        let list_len = select_element.options.length - 1;
        for(let i = list_len; i >= 0; i--) {
            select_element.remove(i);
        }

        let option = document.createElement("option");
        option.text = 'municipality';
        option.value = 'municipality';
        select_element.add(option);
        select_element.selectedIndex = 0;       // select first option ('municipality')

        change_filter_type();
    } else {
        show_filter_row(false, false);
        change_area_scope('boundary_identifier', 'scope');
    }
}

function change_filter_type() {
    filter_type = document.getElementById('select_filter_type').options[document.getElementById('select_filter_type').selectedIndex].value;
    if (filter_type === 'province') show_area_list(document.getElementById('select_filter_list'), 'province', null, null);
    if (filter_type === 'region') show_area_list(document.getElementById('select_filter_list'), 'region', null, null);
}

function load_options_based_on_filter() {
    selected_scope = document.getElementById('scope').options[document.getElementById('scope').selectedIndex].value;
    filter_type = document.getElementById('select_filter_type').options[document.getElementById('select_filter_type').selectedIndex].value;
    selected_filter = document.getElementById('select_filter_list').options[document.getElementById('select_filter_list').selectedIndex].value;
    show_area_list(document.getElementById('boundary_identifier'), selected_scope, filter_type, selected_filter);
}

function boundary_info_window() {
    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>Boundary Information:</h1>';

    table = '<table>';
    table = table + '<tr><td width=180>Scope</td>';
    <!-- table = table + '<td><input type="text" width="60" id="scope" value="district"></td></tr>'; -->

    table = table + '<td><select id="scope" onchange="select_area_scope();">';
    table = table + '<option value="country">country</option>';
    table = table + '<option value="province">province</option>';
    table = table + '<option value="region">region</option>';
    table = table + '<option value="municipality" selected>municipality</option>';
    table = table + '<option value="district">district</option>';
    table = table + '<option value="neighbourhood">neighbourhood</option>';
    table = table + '</select></td></tr>';

    table = table + '<tr id="tr_filter_type" style="display: none;"><td width=180>Filter on:</td><td><select id="select_filter_type" width="60" onchange="change_filter_type();"></select></td></tr>';
    table = table + '<tr id="tr_filter_list" style="display: none;"><td width=180>&nbsp;</td><td><select id="select_filter_list" width="60" onchange="load_options_based_on_filter();"></select></td></tr>';

    table = table + '<tr><td width=180>Identifier</td>';
//    table = table + '<td><input type="text" width="60" id="identifier" value="GM0060"></td></tr>';
    table = table + '<td><select id="boundary_identifier" width="60"></select></td></tr>';

    table = table + '<tr><td width=180>Divide into subareas</td>';
    table = table + '<td><input type="checkbox" id="cb_subareas" checked></td></tr>';
    table = table + '<tr><td width=180>Subscope</td>';
    <!-- table = table + '<td><input type="text" width="60" id="subscope" value="neighbourhood"></td></tr>'; -->

    table = table + '<td><select id="subscope"></select></td></tr>';

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
    select_area_scope();    // Populate all select elements
}

function get_boundary_info(obj) {
//    identifier = document.getElementById('identifier').value;
    identifier = document.getElementById('boundary_identifier').options[document.getElementById('boundary_identifier').selectedIndex].value;
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