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

var store_item_metadata = {};


function process_store_item_metadata(data) {
    store_item_metadata = data
}

function click_store_save_button() {
    store_title = document.getElementById('store_title').value;
    store_descr = document.getElementById('store_descr').value;
    store_email = document.getElementById('store_email').value;

    socket.emit('file_command', {cmd: 'store_esdl', store_title: store_title, store_descr: store_descr, store_email: store_email});
}

function esdl_store_save_window() {
    if (Object.keys(store_item_metadata).length > 0) {
        title = store_item_metadata['title'];
        descr = store_item_metadata['description'];
        email = store_item_metadata['email'];
    } else {
        title = '';
        descr = '';
        email = '';
    }

    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>ESDL store:</h1>';

    table = '<table>';
    table += '<tr><td width=180>Title</td><td><input id="store_title" type="text" width="60" value="'+title+'"></td></tr>';
    table += '<tr><td width=180>Description</td><td><input id="store_descr" type="text" width="60" value="'+descr+'"></td></tr>';
    table += '<tr><td width=180>Email</td><td><input id="store_email" type="text" width="60" value="'+email+'"></td></tr>';
    table += '</table>';
    sidebar_ctr.innerHTML += table;

    sidebar_ctr.innerHTML += '<button onclick="sidebar.hide();click_store_save_button();">Save</button>';

    sidebar.show();
}
