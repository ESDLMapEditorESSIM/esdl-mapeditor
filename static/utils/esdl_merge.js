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

function send_merge_esdl() {
    let esdl_source_id = document.getElementById('esdl_merge_source')
        .options[document.getElementById('esdl_merge_source').selectedIndex].value;
    let esdl_destination_id = document.getElementById('esdl_merge_destination')
        .options[document.getElementById('esdl_merge_destination').selectedIndex].value;

    document.getElementById('esdl_merge_button').style.display = 'none';
    socket.emit('esdl_merge', {esdl_source_id: esdl_source_id, esdl_destination_id: esdl_destination_id});
}

function merge_esdl_window() {
    let sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>Merge ESDL</h1>';
    sidebar_ctr.innerHTML += '<p><b>Note:</b> This is very experimental functionality to test the merge library. ' +
        'Properly merging references is currently \'work in progress\'</p>'

    if (esdl_list) {
        sidebar_ctr.innerHTML += '<h3>Select energysystem to merge:</h3>';

        let select = '<select id="esdl_merge_source" style="width: 300px;">';

        for (let id in esdl_list) {
            es = esdl_list[id];
            select += '<option value="' + id +
                '">' + es['title'] + '</option>';
        }
        select += '</select>';
        sidebar_ctr.innerHTML += select;

        sidebar_ctr.innerHTML += '<h3>... into this energysystem:</h3>';

        select = '<select id="esdl_merge_destination" style="width: 300px;">';
        for (let id in esdl_list) {
            es = esdl_list[id];
            select += '<option value="' + id +
                '">' + es['title'] + '</option>';
        }
        select += '</select>';
        sidebar_ctr.innerHTML += select;
        sidebar_ctr.innerHTML += '<p><button id="esdl_merge_button" onclick="sidebar.hide();send_merge_esdl();">Merge</button></p>';
    } else {
        sidebar_ctr.innerHTML += 'No ESDLs found!';
        sidebar_ctr.innerHTML += '<button id="esdl_merge_close_button" onclick="sidebar.hide();">Close</button>';
    }

    sidebar.show();
}