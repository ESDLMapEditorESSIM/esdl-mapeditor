var sector_list = [];

function set_sector_list(list) {
    sector_list = list;
}

function add_sector() {
    sector_name = document.getElementById('add_sector_name').value;
    socket.emit('command', {cmd: 'add_sector', name: sector_name, code: '', descr: ''});
}

function remove_sector(id) {
    socket.emit('command', {cmd: 'remove_sector', id: id});
    sidebar.hide();
}

function sector_info() {
    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>Sectors:</h1>';

    table = '<table>';
    if (sector_list) {
        for (i=0; i<sector_list.length; i++) {
            // id, name
            table += '<tr><td><button onclick="remove_sector(\'' + sector_list[i]['id'] +
                '\');">Del</button></td><td title="' + sector_list[i]['id'] + '">' + sector_list[i]['name'] + '</td></tr>';
        }
        table += '</table>';
        sidebar_ctr.innerHTML += table;
    } else {
        sidebar_ctr.innerHTML += 'No sectors added yet';
    }

    sidebar_ctr.innerHTML += '<h2>Add sector:</h2>';
    table = '<table>';
    table += '<tr><td>Name</td><td><input type="text" width="60" id="add_sector_name"></td></tr>';
    table += '</table>';
    sidebar_ctr.innerHTML += table;

    sidebar_ctr.innerHTML += '<button onclick="sidebar.hide();add_sector();">Add sector</button>';

    sidebar.show();
}

function select_sector(asset_id) {
    var select_box = document.getElementById("sector_select");
    var selected_value = select_box.options[select_box.selectedIndex].value;
    sidebar.hide();
    //alert(selected_value);
    socket.emit('command', {cmd: 'set_sector', asset_id: asset_id, sector_id: selected_value});
}

function select_sector_menu(asset_id) {
    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>Sectors:</h1>';

    if (sector_list) {
        var size;
        if (sector_list.length < 4) { size = 4; } else { size = sector_list.length; }
        select = '<select id="sector_select" size="'+size+'" onchange="select_sector(\''+asset_id+'\');" style="width: 300px;">';
        for (i=0; i<sector_list.length; i++) {
            // id, name
            select += '<option value="' + sector_list[i]['id'] +
                '">' + sector_list[i]['name'] + '</option>';
        }
        select += '</select>';
        sidebar_ctr.innerHTML += select;
    } else {
        sidebar_ctr.innerHTML += 'No sectors added yet';
    }

    sidebar.show();
}
