// ------------------------------------------------------------------------------------------------------------
//  Carriers and commodities
// ------------------------------------------------------------------------------------------------------------
//var carrier_list = [];

//function update_carrier_list(carr_list) {
//    carrier_list = carr_list;
    // console.log(carr_list);

//    var select = document.getElementById('carrier_select');
//    select.innerHTML = '';
//    for (i=0; i<carrier_list.length; i++) {
//        var option = document.createElement("option");
//        if (i==0) { option.classList.add("ui-state-active"); }
//        option.text = carrier_list[i]['name']
//        option.value = carrier_list[i]['id']
//        select.add(option, null);
//    }
//    $("#carrier_select").selectmenu("refresh");    // to update the selectmenu based on the selected value
// }

setCarrier = function(e) {
    asset_id = e.relatedTarget.id;
    // console.log(asset_id);

    carrier_index = document.getElementById("carrier_select").selectedIndex;
    carrier_options = document.getElementById("carrier_select").options;
    carrier_id = carrier_options[carrier_index].value;

    // console.log(carrier_id);
    socket.emit('command', {cmd: 'set_carrier', asset_id: asset_id, carrier_id: carrier_id});
}

function add_carrier() {
    carr_type_index = document.getElementById('add_carrier_type').selectedIndex;
    carr_type_options = document.getElementById('add_carrier_type').options;
    carr_type = carr_type_options[carr_type_index].value;

    carr_name = document.getElementById('add_carrier_name').value;
    if (carr_type == 'en_carr') {
        carr_emission = document.getElementById('add_carrier_emission').value;
        carr_encont = document.getElementById('add_carrier_encont').value;

        carr_encunit_index = document.getElementById('add_carrier_encunit').selectedIndex;
        carr_encunit_options = document.getElementById('add_carrier_encunit').options;
        carr_encunit = carr_encunit_options[carr_encunit_index].value;

        carr_sofm_index = document.getElementById('add_carrier_sofm').selectedIndex;
        carr_sofm_options = document.getElementById('add_carrier_sofm').options;
        carr_sofm = carr_sofm_options[carr_sofm_index].value;

        carr_rentype_index = document.getElementById('add_carrier_rentype').selectedIndex;
        carr_rentype_options = document.getElementById('add_carrier_rentype').options;
        carr_rentype = carr_rentype_options[carr_rentype_index].value;

        socket.emit('command', {cmd: 'add_carrier', type: carr_type, name: carr_name, emission: carr_emission,
            encont: carr_encont, encunit: carr_encunit, sofm: carr_sofm, rentype: carr_rentype});
    }
    if (carr_type == 'el_comm') {
        carr_voltage = document.getElementById('add_carrier_voltage').value;
        socket.emit('command', {cmd: 'add_carrier', type: carr_type, name: carr_name, voltage: carr_voltage});
    }
    if (carr_type == 'g_comm') {
        carr_pressure = document.getElementById('add_carrier_pressure').value;
        socket.emit('command', {cmd: 'add_carrier', type: carr_type, name: carr_name, pressure: carr_pressure});
    }
    if (carr_type == 'h_comm') {
        carr_suptemp = document.getElementById('add_carrier_suptemp').value;
        carr_rettemp = document.getElementById('add_carrier_rettemp').value;
        socket.emit('command', {cmd: 'add_carrier', type: carr_type, name: carr_name, suptemp: carr_suptemp,
            rettemp: carr_rettemp});
    }
    if (carr_type == 'en_comm') {
        socket.emit('command', {cmd: 'add_carrier', type: carr_type, name: carr_name});
    }
}

function select_other_carrier() {
    carr_type_index = document.getElementById('add_carrier_type').selectedIndex;
    carr_type_options = document.getElementById('add_carrier_type').options;
    carr_type = carr_type_options[carr_type_index].value;

    document.getElementById('voltage_row').style.display = 'none';
    document.getElementById('pressure_row').style.display = 'none';
    document.getElementById('suptemp_row').style.display = 'none';
    document.getElementById('rettemp_row').style.display = 'none';
    document.getElementById('emission_row').style.display = 'none';
    document.getElementById('encont_row').style.display = 'none';
    document.getElementById('sofm_row').style.display = 'none';
    document.getElementById('rentype_row').style.display = 'none';

    if (carr_type == 'en_carr') {
        document.getElementById('emission_row').style.display = '';
        document.getElementById('encont_row').style.display = '';
        document.getElementById('sofm_row').style.display = '';
        document.getElementById('rentype_row').style.display = '';
    }
    if (carr_type == 'el_comm') {
        document.getElementById('voltage_row').style.display = '';
    }
    if (carr_type == 'g_comm') {
        document.getElementById('pressure_row').style.display = '';
    }
    if (carr_type == 'h_comm') {
        document.getElementById('suptemp_row').style.display = '';
        document.getElementById('rettemp_row').style.display = '';
    }
    if (carr_type == 'en_comm') {
    }
}

function change_color(obj, carrier_id) {
    color = obj.value;
//    console.log(value);
//    console.log(carrier_id);
    set_carrier_color(active_layer_id, carrier_id, color);
    socket.emit('command', {cmd: 'redraw_connections'});
}

function energy_carrier_info() {
    sidebar_ctr = sidebar.getContainer();
    sidebar_ctr.innerHTML = '<h1>Energy Carriers and Commodities:</h1>';

    carrier_list = get_carrier_list(active_layer_id);
    carrier_info_mapping = get_carrier_info_mapping(active_layer_id);

    if (carrier_list) {
        table = '<table>';
        table += '<tr><td>&nbsp;</td><td><b>Name</b></td><td><b>Type</b></td><td><b>Color</b></td></tr>';
        for (i=0; i<carrier_list.length; i++) {
            // type, id, name
            table += '<tr><td><button onclick="remove_carrier(\'' + carrier_list[i]['id'] +
                '\');">Del</button></td><td title="' + carrier_list[i]['id'] + '">' + carrier_list[i]['name'] + '</td><td>' +
                carrier_list[i]['type'] + '</td><td><input type="color" value="'+carrier_info_mapping[carrier_list[i]['id']]['color'] +'" onchange="change_color(this, \''+carrier_list[i]['id']+'\')"></td></tr>';

         //       <i class="color_select" style="background:' + carrier_info_mapping[carrier_list[i]['id']]['color'] + '"></i></td></tr>';
        }
        table += '</table>';
        sidebar_ctr.innerHTML += table;
    }

    sidebar_ctr.innerHTML += '<h2>Add carrier:</h2>';
    table = '<table>';
    table += '<tr><td width=180>Carrier type</td><td><select id="add_carrier_type" onchange="select_other_carrier();">';
    table += '<option value="en_carr">Energy carrier</option>';
    table += '<option value="el_comm">Electricity commodity</option>';
    table += '<option value="g_comm">Gas commodity</option>';
    table += '<option value="h_comm">Heat commodity</option>';
    table += '<option value="en_comm">Energy commodity</option>';
    table += '</select></td>';

    table += '<tr><td>Name</td><td><input type="text" width="60" id="add_carrier_name"></td></tr>';
    table += '<tr id="voltage_row" style="display:none"><td>Voltage</td><td><input type="text" width="20" id="add_carrier_voltage"></td></tr>';
    table += '<tr id="pressure_row" style="display:none"><td>Pressure</td><td><input type="text" width="20" id="add_carrier_pressure"></td></tr>';
    table += '<tr id="suptemp_row" style="display:none"><td>Supply temperature</td><td><input type="text" width="20" id="add_carrier_suptemp"></td></tr>';
    table += '<tr id="rettemp_row" style="display:none"><td>Return temperature</td><td><input type="text" width="20" id="add_carrier_rettemp"></td></tr>';
    table += '<tr id="emission_row"><td>Emission [kg/GJ]</td><td><input type="text" width="20" id="add_carrier_emission"></td></tr>';
    table += '<tr id="encont_row"><td>Energy content</td><td><input type="text" width="20" id="add_carrier_encont">';
    table += '<select id="add_carrier_encunit">';
    table += '<option value="MJpkg">MJ/kg</option>';
    table += '<option value="MJpNm3">MJ/Nm3</option>';
    table += '<option value="MJpMJ">MJ/MJ</option>';
    table += '</select></td></tr>';
    table += '<tr id="sofm_row"><td>State of matter</td><td><select id="add_carrier_sofm">';
    table += '<option value="UNDEFINED">UNDEFINED</option>';
    table += '<option value="SOLID">SOLID</option>';
    table += '<option value="LIQUID">LIQUID</option>';
    table += '<option value="GASEOUS">GASEOUS</option>';
    table += '</select></td></tr>';
    table += '<tr id="rentype_row"><td>Renewable type</td><td><select id="add_carrier_rentype">';
    table += '<option value="UNDEFINED">UNDEFINED</option>';
    table += '<option value="RENEWABLE">RENEWABLE</option>';
    table += '<option value="FOSSIL">FOSSIL</option>';
    table += '</select></td></tr>';
    table += '</table>';
    sidebar_ctr.innerHTML += table;

    sidebar_ctr.innerHTML += '<button onclick="sidebar.hide();add_carrier();">Add carrier</button>';

    sidebar.show();
}

function select_carrier(asset_id) {
    var select_box = document.getElementById("carrier_select");
    var selected_value = select_box.options[select_box.selectedIndex].value;
    sidebar.hide();
    //alert(selected_value);
    socket.emit('command', {cmd: 'set_carrier', asset_id: asset_id, carrier_id: selected_value});
}

function select_carrier_menu(asset_id) {
    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>Carriers:</h1>';

    carrier_list = get_carrier_list(active_layer_id);
    if (carrier_list) {
        var size;
        if (carrier_list.length < 4) { size = 4; } else { size = carrier_list.length; }
        select = '<select id="carrier_select" size="'+size+'" onchange="select_carrier(\''+asset_id+'\');" style="width: 300px;">';
        for (i=0; i<carrier_list.length; i++) {
            // id, name
            select += '<option value="' + carrier_list[i]['id'] +
                '">' + carrier_list[i]['name'] + '</option>';
        }
        select += '</select>';
        sidebar_ctr.innerHTML += select;
    } else {
        sidebar_ctr.innerHTML += 'No carriers added yet';
    }

    sidebar.show();
}