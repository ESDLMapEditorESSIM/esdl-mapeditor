/**
 *  This work is based on original code developed and copyrighted by TNO 2020.
 *  Subsequent contributions are licensed to you by the developers of such code and are
 *  made available to the Project under one or several contributor license agreements.
 *
 *  This work is licensed to you under the Apache License, Version 2.0.
 *  You may obtain a copy of the license at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Contributors:
 *      TNO         - Initial implementation
 *  Manager:
 *      TNO
 */


// ------------------------------------------------------------------------------------------------------------
//  Boundary information from GEIS boundary service
// ------------------------------------------------------------------------------------------------------------
var scopes_list = ["country", "province", "region", "municipality", "district", "neighbourhood"];

// ------------------------------------------------------------------------------------------------------------
//  Get a list of subscopes from a certain scope
// ------------------------------------------------------------------------------------------------------------
function get_subscopes(scope) {
    let result = [];
    let start_copy = false;
    for (let i=0; i<scopes_list.length; i++) {
        if (start_copy) {
            result.push(scopes_list[i]);
        } else {
            if (scope === scopes_list[i]) start_copy = true;
        }
    }
    return result;
}

function add_subscopes(element_id, scope) {
    // update list of possible subboundaries
    let possible_subscopes = get_subscopes(scope);
    let subscope_select = document.getElementById(element_id)
    let list_len = subscope_select.options.length - 1;
    for (let i = list_len; i >= 0; i--) {
        subscope_select.remove(i);
    }

    for (let i=0; i<possible_subscopes.length; i++) {
        let sub_scp = possible_subscopes[i];
        let option = document.createElement("option");
        option.text = sub_scp;
        option.value = sub_scp;
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

    if (filter_type || filter_list) {
        document.getElementById('div-filter').style.display = 'block';
    } else {
        document.getElementById('div-filter').style.display = 'none';
    }
}

function select_area_scope() {
    let selected_scope = document.getElementById('scope').options[document.getElementById('scope').selectedIndex].value;

    add_subscopes('subscope', selected_scope);

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
    if (filter_type === 'province') show_area_list('select_filter_list', 'province', null, null);
    if (filter_type === 'region') show_area_list('select_filter_list', 'region', null, null);
}

function load_options_based_on_filter() {
    selected_scope = document.getElementById('scope').options[document.getElementById('scope').selectedIndex].value;
    filter_type = document.getElementById('select_filter_type').options[document.getElementById('select_filter_type').selectedIndex].value;
    selected_filter = document.getElementById('select_filter_list').options[document.getElementById('select_filter_list').selectedIndex].value;
    show_area_list('boundary_identifier', selected_scope, filter_type, selected_filter);
}

function select_area_subscope() {
    selected_scope = document.getElementById('scope').options[document.getElementById('scope').selectedIndex].value;
    selected_subscope = document.getElementById('subscope').options[document.getElementById('subscope').selectedIndex].value;
    selected_area = document.getElementById('boundary_identifier').options[document.getElementById('boundary_identifier').selectedIndex].value;
    show_area_list('select_subareas', selected_subscope, selected_scope, selected_area)
}

function view_divide_subareas(el) {
    if (el.checked) {
        document.getElementById('div-divide-subareas').style.display = 'block';
        view_select_subareas(document.getElementById('cb_select_subareas'));
    } else {
        document.getElementById('div-divide-subareas').style.display = 'none';
    }
}

function view_select_subareas(el) {
    if (el.checked)
        document.getElementById('tr_select_subareas').style.display = 'table-row';
    else
        document.getElementById('tr_select_subareas').style.display = 'none';
}

function boundary_info_window() {
    sidebar_ctr = sidebar.getContainer();

    if (services_enabled['boundary_service']) {
        sidebar_ctr.innerHTML = '<h1>Boundary Information:</h1>';

        table = '<table>';
        table = table + '<tr><td width=180>Scope</td>';

        table = table + '<td><select id="scope" onchange="select_area_scope();">';
        table = table + '<option value="country">country</option>';
        table = table + '<option value="province" selected>province</option>';
        table = table + '<option value="region">region</option>';
        table = table + '<option value="municipality">municipality</option>';
        table = table + '<option value="district">district</option>';
        table = table + '<option value="neighbourhood">neighbourhood</option>';
        table = table + '</select></td></tr></table>';

        table = table + '<div id="div-filter" class="div-box"><table>';
        table = table + '<tr id="tr_filter_type" style="display: none;"><td width=180>Filter on:</td><td><select id="select_filter_type" width="60" onchange="change_filter_type();"></select></td></tr>';
        table = table + '<tr id="tr_filter_list" style="display: none;"><td width=180>&nbsp;</td><td><select id="select_filter_list" width="60" onchange="load_options_based_on_filter();"></select></td></tr>';
        table = table + '</table></div>';

        table = table + '<div><table>';
        table = table + '<tr><td width=180>Identifier</td><td><select id="boundary_identifier" width="60" onchange="select_area_subscope();"></select></td></tr>';

        table = table + '<tr><td width=180>Divide into sub areas</td><td><input type="checkbox" id="cb_subareas" checked onchange="view_divide_subareas(this);"></td></tr>';
        table = table + '</table></div>';

        table = table + '<div id="div-divide-subareas" class="div-box"><table>';
        table = table + '<tr id="tr_cb_include_toparea"><td width=180>Include top area</td><td><input type="checkbox" id="cb_include_toparea" checked></td></tr>';
        table = table + '<tr id="tr_subscope"><td width=180>Sub scope</td><td><select id="subscope" onchange="select_area_subscope();"></select></td></tr>';
        table = table + '<tr id="tr_cb_select_subareas"><td width=180>Select sub areas</td><td><input type="checkbox" id="cb_select_subareas" onchange="view_select_subareas(this);"></td></tr>';
        table = table + '<tr id="tr_select_subareas" style="display:none;"><td width=180>Selection</td><td><select id="select_subareas" multiple></select></td></tr>';
        table = table + '</table></div>';

        table = table + '<table>';
        table = table + '<tr><td width=180>Initialize energysystem</td>';
        table = table + '<td><input type="checkbox" id="initialize_ES" checked></td></tr>';
        table = table + '<tr><td width=180>Add boundaries to energysystem</td>';
        table = table + '<td><input type="checkbox" id="add_boundary_to_ESDL" disabled></td></tr>';
        table = table + '</table>';

        if (check_role('service_area_service')) {
            table = table + '<table>';
            table = table + '<tr><td width=180>Add service areas from DSOs</td>';
            table = table + '<td><input type="checkbox" id="service_area_dso" checked></td></tr>';
            table = table + '<tr><td width=180>Add DSO stations</td>';
            table = table + '<td><input type="checkbox" id="station_dso" checked></td></tr>';
            table = table + '</table>';
        }

        sidebar_ctr.innerHTML += table;
        sidebar_ctr.innerHTML += '<p><button onclick="sidebar.hide();get_boundary_info(this);">Request</button></p>';
    }

    if (services_enabled['ibis_service']) {
        sidebar_ctr.innerHTML += '<h1>IBIS bedrijventerreinen Information:</h1>';
        table = '<table>';
        table = table + '<tr><td width=180>RIN List</td>';
        table = table + '<td><input type="text" width="60" id="rin_list" value="777,779"></td></tr>';
        table = table + '<tr><td width=180>Initialize energysystem</td>';
        table = table + '<tr><td width=180>Add boundaries to energysystem</td>';
        table = table + '<td><input type="checkbox" id="add_boundary_to_ESDL2" checked></td></tr>';
        table = table + '</table>';
        sidebar_ctr.innerHTML += table;
        sidebar_ctr.innerHTML += '<p><button onclick="sidebar.hide();get_ibis_info();">Request</button></p>';
    }

    sidebar.show();
    if (services_enabled['boundary_service']) {
        select_area_scope();    // Populate all select elements
    }
}

function get_boundary_info(obj) {
//    identifier = document.getElementById('identifier').value;
    identifier = document.getElementById('boundary_identifier').options[document.getElementById('boundary_identifier').selectedIndex].value;
    toparea_name = document.getElementById('boundary_identifier').options[document.getElementById('boundary_identifier').selectedIndex].text;
    scope = document.getElementById('scope').value;
    subscope_enabled = document.getElementById('cb_subareas').checked;
    add_toparea = document.getElementById('cb_include_toparea').checked;
    subscope = document.getElementById('subscope').value;
    select_subareas = document.getElementById('cb_select_subareas').checked;
    selected_subareas = $('#select_subareas').val();
    initialize_ES = document.getElementById('initialize_ES').checked;
    add_boundary_to_ESDL = document.getElementById('add_boundary_to_ESDL').checked;
    add_service_area_info = document.getElementById('service_area_dso').checked;
    add_station_info = document.getElementById('station_dso').checked;

    show_loader();
    socket.emit('get_boundary_info', {identifier: identifier, toparea_name: toparea_name, scope: scope,
        subscope_enabled: subscope_enabled, add_toparea: add_toparea, subscope: subscope,
        select_subareas: select_subareas, selected_subareas: selected_subareas, initialize_ES: initialize_ES,
        add_boundary_to_ESDL: add_boundary_to_ESDL, add_service_area_info: add_service_area_info,
        add_station_info: add_station_info
    });
}

function get_ibis_info(add_boundary_to_ESDL = null) {
    if (document.getElementById('add_boundary_to_ESDL2')) {
        add_boundary_to_ESDL = document.getElementById('add_boundary_to_ESDL2').checked;
    }
    const rin_list = document.getElementById('rin_list').value;

    show_loader();
    socket.emit('ibis_bedrijventerreinen', {rin_list: rin_list,
        add_boundary_to_ESDL: add_boundary_to_ESDL});
}

function get_boundary_service_settings(div) {
    socket.emit('get_boundary_service_settings', function(result) {
        console.log(result);
        div.append($('<h1>').text('Boundary service plugin settings'));

        $table = $('<table>')
            .append($('<tbody>')
                .append($('<tr>')
                    .append($('<td>').attr('width', 250).text('Boundary service year'))
                    .append($('<td>')
                        .append($('<input>')
                            .attr('type', 'text')
                            .attr('id', 'boundary_service_year_input')
                            .attr('value', result['boundaries_year'])
                            .change(function(e) { change_boundaries_setting_param(this); })
                        )
                    )
                )
            );
        div.append($table);
    });
}

function change_boundaries_setting_param(obj) {
    if (obj.id === 'boundary_service_year_input') {
        let year = parseInt(obj.value);
        set_boundary_service_setting('boundaries_year', year);
    }
}

function set_boundary_service_setting(name, value) {
    socket.emit('set_boundary_service_setting', {name: name, value: value});
}

function settings_window_contents() {
    let $div = $('<div>').attr('id', 'boundary_service_settings_window_div');
    get_boundary_service_settings($div);
    return $div;
}

function boundary_service_extension_create(event) {
    if (event.type === 'client_connected') {
    }
    if (event.type === 'settings_menu_items') {
        let menu_items = {
            'value': 'boundary_service_plugin_settings',
            'text': 'Boundary service plugin',
            'settings_func': settings_window_contents,
            'sub_menu_items': []
        };

        return menu_items;
    }
}

$(document).ready(function() {
    extensions.push(function(event) { return boundary_service_extension_create(event) });
});