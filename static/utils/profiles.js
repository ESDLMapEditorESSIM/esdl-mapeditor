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
//  Profiles and Quantity and Units
// ------------------------------------------------------------------------------------------------------------
function add_profile_to_port() {
    port_id = document.getElementById('profile_port_id').value;
    profile_mult_value = document.getElementById('profile_mult_value').value;
    profile_class_select = document.getElementById('profile_class');
    profile_class = profile_class_select.options[profile_class_select.selectedIndex].value;

    profile_type_select = document.getElementById('profile_type');
    profile_type = profile_type_select.options[profile_type_select.selectedIndex].value;

    qaup_type_select = document.getElementById('qau_profile_type');
    qaup_type = qaup_type_select.options[qaup_type_select.selectedIndex].value;

    if (qaup_type == 'predefined_qau') {
        predefined_qau_select = document.getElementById('predef_qau');
        predefined_qau = predefined_qau_select.options[predefined_qau_select.selectedIndex].value;
    } else if (qaup_type == 'custom_qau') {
        cqua_description = document.getElementById('cqau_description').value;
        cqua_quant_select = document.getElementById('cqau_quant');
        cqua_quant = cqua_quant_select.options[cqua_quant_select.selectedIndex];
        cqua_mult_select = document.getElementById('cqau_mult');
        cqua_mult = cqua_mult_select.options[cqua_mult_select.selectedIndex];
        cqua_unit_select = document.getElementById('cqau_unit');
        cqua_unit = cqua_unit_select.options[cqua_unit_select.selectedIndex];
        cqua_pmult_select = document.getElementById('cqau_pmult');
        cqua_pmult = cqua_pmult_select.options[cqua_pmult_select.selectedIndex];
        cqua_punit_select = document.getElementById('cqau_punit');
        cqua_punit = cqua_punit_select.options[cqua_punit_select.selectedIndex];
        cqua_ptunit_select = document.getElementById('cqau_ptunit');
        cqua_ptunit = cqua_ptunit_select.options[cqua_ptunit_select.selectedIndex];

        custom_qau = {
            description: cqua_description,
            physicalQuantity: cqua_quant.value,
            multiplier: cqau_mult.value,
            unit: cqau_unit.value,
            perMultiplier: cqau_pmult.value,
            perUnit: cqau_punit.value,
            perTimeUnit: cqau_ptunit.value
        };
    }

    // profile_class: SingleValue       -- value, predefined_qau, custom_qau
    // profile_class: standard_profiles -- multiplier
    if (profile_class == 'SingleValue') {
        if (qaup_type == 'predefined_qau') {
            socket.emit('command', {cmd: 'add_profile_to_port', port_id: port_id, value: profile_mult_value,
                profile_class: profile_class, profile_type: profile_type, qaup_type: qaup_type, predefined_qau: predefined_qau});
        } else if (qaup_type == 'custom_qau') {
            socket.emit('command', {cmd: 'add_profile_to_port', port_id: port_id, value: profile_mult_value,
                profile_class: profile_class, profile_type: profile_type, qaup_type: qaup_type, custom_qau: custom_qau});
        }
    } else {
        if (qaup_type == 'predefined_qau') {
            socket.emit('command', {cmd: 'add_profile_to_port', port_id: port_id, multiplier: profile_mult_value,
                profile_class: profile_class, profile_type: profile_type, qaup_type: qaup_type, predefined_qau: predefined_qau});
        } else if (qaup_type == 'custom_qau') {
            socket.emit('command', {cmd: 'add_profile_to_port', port_id: port_id, multiplier: profile_mult_value,
                profile_class: profile_class, profile_type: profile_type, qaup_type: qaup_type, custom_qau: custom_qau});
        }
    }
}

function remove_profile_from_port(port_id, profile_id) {
    socket.emit('command', {cmd: 'remove_profile_from_port', port_id: port_id, profile_id: profile_id});
}

function select_profile_class() {
    profile_class_index = document.getElementById('profile_class').selectedIndex;
    profile_class_options = document.getElementById('profile_class').options;
    profile_class = profile_class_options[profile_class_index].value;

    if (profile_class == "SingleValue") {
        document.getElementById('mult_value').innerHTML = 'Value';
    } else {
        document.getElementById('mult_value').innerHTML = 'Multiplier';

        let profiles_info = Object.entries(profiles_plugin.profiles_list['profiles']);
        for (let pr=0; pr<profiles_info.length; pr++) {
            let pi = profiles_info[pr][1];
            if (pi['profile_uiname'] == profile_class && pi['embedUrl'] !== '') {
                $('#div_for_graph_panel').html('<iframe width="100%" height="200px" src="'+pi['embedUrl']+'"></iframme>');
            }
        }

    }
}

function select_qau_profile_type() {
    qaup_type_index = document.getElementById('qau_profile_type').selectedIndex;
    qaup_type_options = document.getElementById('qau_profile_type').options;
    qaup_type = qaup_type_options[qaup_type_index].value;

    document.getElementById('qau_row').style.display = 'none';
    document.getElementById('cqau_row1').style.display = 'none';
    document.getElementById('cqau_row2').style.display = 'none';
    document.getElementById('cqau_row3').style.display = 'none';
    document.getElementById('cqau_row4').style.display = 'none';
    document.getElementById('cqau_row5').style.display = 'none';
    document.getElementById('cqau_row6').style.display = 'none';
    document.getElementById('cqau_row7').style.display = 'none';
    if (qaup_type == 'predefined_qau') {
       document.getElementById('qau_row').style.display = '';
    }
    if (qaup_type == 'custom_qau') {
       document.getElementById('cqau_row1').style.display = '';
       document.getElementById('cqau_row2').style.display = '';
       document.getElementById('cqau_row3').style.display = '';
       document.getElementById('cqau_row4').style.display = '';
       document.getElementById('cqau_row5').style.display = '';
       document.getElementById('cqau_row6').style.display = '';
       document.getElementById('cqau_row7').style.display = '';
    }
}

function port_profile_info_window(port_profile_info) {
    const profile_info_list = port_profile_info['profile_info'];
    const viewer_context = window.port_profile_viewer_context;
    const port_id = port_profile_info['port_id'];
    let show_profile_viewer = false;

    const sidebar_ctr = window.sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>Current profiles of port:</h1>';

    if (profile_info_list.length > 0) {
        let table = '<table id="profiles_table">';
        table += '<tr><td>&nbsp;</td><td><b>Name</b></td><td><b>Value</b></td><td><b>Unit</b></td></tr>';
        for (let p=0; p<profile_info_list.length; p++) {
            let profile_info = profile_info_list[p];
            let profile_class = profile_info['class'];
            let profile_type = profile_info['type'];
            let profile_name = profile_info['uiname'];
            let profile_id = profile_info['id'];
            let profile_value_or_multiplier = 0;

            if (profile_class === 'SingleValue') {
                profile_value_or_multiplier = profile_info['value'];
                profile_uiname = 'SingleValue';
            } else if (profile_class === 'InfluxDBProfile') {
                profile_value_or_multiplier = (+profile_info['multiplier']).toFixed(4);
                show_profile_viewer = true;
            } else if (profile_class === 'DataTableProfile') {
                show_profile_viewer = true;
            } else if (profile_class === 'DateTimeProfile') {
                profile_value_or_multiplier = 0;
                profile_uiname = 'DateTimeProfile';
            }

            table += '<tr><td><button onclick="document.getElementById(\'profiles_table\').deleteRow('+(p+1)+');remove_profile_from_port(\'' + port_id + '\', \''+ profile_id +
                '\');">Del</button></td><td><p title="'+profile_class+'">'+profile_name+'</p></td><td>'+profile_value_or_multiplier+'</td><td>' +
                profile_type +'</td></tr>';

            if (profile_class == 'InfluxDBProfile' && profile_info['embedUrl']) {
                table += '<tr><td colspan="4"><iframe width="100%" height="200px" src="'+profile_info['embedUrl']+'"></iframme></td></tr>';
            }
        }
        table += '</table>';
        sidebar_ctr.innerHTML += table;
    } else {
        sidebar_ctr.innerHTML += 'No profiles yet';
    }

    sidebar_ctr.innerHTML += '<div id="port_profile_viewer_button"></div>';
    sidebar_ctr.innerHTML += '<h1>Add profile to port:</h1>';
    let table = '<table>';

    table += '<tr><input type="hidden" id="profile_port_id" value="'+port_id+'"><td width=180>Profile class</td>';
    let $select = $('<select>').attr('id', 'profile_class');
    $select.append($('<option>').val('SingleValue').text('Single Value').attr('selected', 'selected'));
    let group_list = profiles_plugin.profiles_list['groups'];
    let profile_info = Object.entries(profiles_plugin.profiles_list['profiles']);
    for (let gr=0; gr<group_list.length; gr++) {
        let $optgroup = $('<optgroup>').attr('label', group_list[gr].name);
        for (let pr=0; pr<profile_info.length; pr++) {
            if (group_list[gr].setting_type == profile_info[pr][1].setting_type) {
                if (profile_info[pr][1].setting_type == 'project' &&
                    profile_info[pr][1].project_name != group_list[gr].project_name) continue;

                let $option = $('<option>').val(profile_info[pr][1].profile_uiname).text(profile_info[pr][1].profile_uiname);
                $optgroup.append($option);
            }
        }
        $select.append($optgroup);
    }
    table += '<td>'+$select.prop('outerHTML')+'</td></tr>';
    // table += '</select></td></tr>';

    table += '<tr id="mov_row"><td id="mult_value" width=180>Value</td>';
    table += '<td><input type="text" width="60" id="profile_mult_value" value=""></td></tr>';

    table += '<tr id="profile_type_row"><td width=180>Profile type</td>';
    table += '<td><select id="profile_type"><option value="INPUT" selected>Input</option>';
    table += '<option value="OUTPUT">Output</option>';
    table += '<option value="UNDEFINED">Undefined</option>';
    table += '</td></tr>';

    table += '<tr id="type_row"><td width=180>Quantity and Unit type</td>';
    table += '<td><select id="qau_profile_type" onchange="select_qau_profile_type();"><option value="predefined_qau" selected>Predefined quantity and units</option>';
    table += '<option value="custom_qau">Custom quantity and units</option>';
    table += '</td></tr>';

    table += '<tr id="qau_row"><td width=180>Quantity and Unit</td>';
    table += '<td><select id="predef_qau">';
    for (q=0; q<quantity_and_units_info["predefined_qau"].length; q++) {
        table += '<option value="'+quantity_and_units_info["predefined_qau"][q]["id"]+'">'+quantity_and_units_info["predefined_qau"][q]["description"]+'</option>';
    }
    table += '</select></td></tr>';

    table += '<tr id="cqau_row1" style="display:none"><td width=180>Description</td>' +
        '<td><input type="text" width="180" id="cqau_description" value=""></td></tr>';
    table += '<tr id="cqau_row2" style="display:none"><td width=180>Quantity</td><td><select id="cqau_quant">';
    for (q=0; q<quantity_and_units_info["generic"]["physicalQuantity"]["options"].length; q++) {
        table += '<option value="'+quantity_and_units_info["generic"]["physicalQuantity"]["options"][q]+'">'+
            quantity_and_units_info["generic"]["physicalQuantity"]["options"][q]+'</option>';
    }
    table += '</select></td></tr>';
    table += '<tr id="cqau_row3" style="display:none"><td width=180>Multiplier</td><td><select id="cqau_mult">';
    for (q=0; q<quantity_and_units_info["generic"]["multiplier"]["options"].length; q++) {
        table += '<option value="'+quantity_and_units_info["generic"]["multiplier"]["options"][q]+'">'+
            quantity_and_units_info["generic"]["multiplier"]["options"][q]+'</option>';
    }
    table += '</select></td></tr>';
    table += '<tr id="cqau_row4" style="display:none"><td width=180>Unit</td><td><select id="cqau_unit">';
    for (q=0; q<quantity_and_units_info["generic"]["unit"]["options"].length; q++) {
        table += '<option value="'+quantity_and_units_info["generic"]["unit"]["options"][q]+'">'+
            quantity_and_units_info["generic"]["unit"]["options"][q]+'</option>';
    }
    table += '</select></td></tr>';
    table += '<tr id="cqau_row5" style="display:none"><td width=180>PerMultiplier</td><td><select id="cqau_pmult">';
    for (q=0; q<quantity_and_units_info["generic"]["perMultiplier"]["options"].length; q++) {
        table += '<option value="'+quantity_and_units_info["generic"]["perMultiplier"]["options"][q]+'">'+
            quantity_and_units_info["generic"]["perMultiplier"]["options"][q]+'</option>';
    }
    table += '</select></td></tr>';
    table += '<tr id="cqau_row6" style="display:none"><td width=180>PerUnit</td><td><select id="cqau_punit">';
    for (q=0; q<quantity_and_units_info["generic"]["perUnit"]["options"].length; q++) {
        table += '<option value="'+quantity_and_units_info["generic"]["perUnit"]["options"][q]+'">'+
            quantity_and_units_info["generic"]["perUnit"]["options"][q]+'</option>';
    }
    table += '</select></td></tr>';
    table += '<tr id="cqau_row7" style="display:none"><td width=180>PerTimeUnit</td><td><select id="cqau_ptunit">';
    for (q=0; q<quantity_and_units_info["generic"]["perTimeUnit"]["options"].length; q++) {
        table += '<option value="'+quantity_and_units_info["generic"]["perTimeUnit"]["options"][q]+'">'+
            quantity_and_units_info["generic"]["perTimeUnit"]["options"][q]+'</option>';
    }
    table += '</select></td></tr>';


    table += '</table>'
    sidebar_ctr.innerHTML += table;
    sidebar_ctr.innerHTML += '<button onclick="sidebar.hide();add_profile_to_port();">Add</button>';

    sidebar_ctr.innerHTML += '<p><div id="div_for_graph_panel"></div></p>';

    if (show_profile_viewer && viewer_context) {
        let viewer_button = $('<button>').text('Show in Port Profile Viewer').click(function() {
            window.activate_port_profile_viewer(viewer_context['es_id'], viewer_context['asset_id']);
        });
        $('#port_profile_viewer_button').append(viewer_button);
    }

    sidebar.show();

    $('#profile_class').change(function() {select_profile_class();});
}