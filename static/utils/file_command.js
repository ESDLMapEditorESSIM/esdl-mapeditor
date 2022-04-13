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
//  Functions for starting a new ESDL file, loading and saving an ESDL file
// ------------------------------------------------------------------------------------------------------------
function new_ESDL() {
    sidebar_ctr = sidebar.getContainer();
    sidebar_ctr.innerHTML = '<h1>New ESDL energysystem</h1>';

    table = '<table>';
    table += '<tr><td width=180>Name</td><td><input type="text" width="60" id="new_name"></td></tr>';
    table += '<tr><td width=180>Description</td><td><input type="text" width="60" id="new_description"></td></tr>';
    table += '<tr><td width=180>Instance name</td><td><input type="text" width="60" id="new_instance_name"></td></tr>';
    table += '<tr><td width=180></td><td></td></tr>';
    table += '<tr><td width=180>Top-level area name</td><td><input type="text" width="60" id="new_area_name"></td></tr>';
    table += '</table>';

    sidebar_ctr.innerHTML += table;
    sidebar_ctr.innerHTML += '<p><button onclick="sidebar.hide();click_new_ESDL_button(this);">Create</button></p>';

    sidebar.show();
}

function click_new_ESDL_button(obj) {
    new_name = document.getElementById('new_name').value;
    new_description = document.getElementById('new_description').value;
    new_instance_name = document.getElementById('new_instance_name').value;
    new_top_area_name = document.getElementById('new_area_name').value;

    socket.emit('file_command', {cmd: 'new_esdl', name: new_name, description: new_description,
        instance_name: new_instance_name, top_area_name: new_top_area_name});
}

function open_ESDL(event) {
    // getting a hold of the file reference
    var file = event.target.files[0];

    // setting up the reader
    var reader = new FileReader();
    reader.readAsText(file); // this is reading as data url

    // here we tell the reader what to do when it's done reading...
    reader.onload = readerEvent => {
        var content = readerEvent.target.result; // this is the content!
        socket.emit('file_command', {cmd: 'load_esdl_from_file', filename: file.name, file_content: content});
    }

    // clear file input so that one could load the same file the next time
    $('.inputFile')[0].value = "";

    // show loader
    show_loader();
}

function import_ESDL(event) {
    // getting a hold of the file reference
    var file = event.target.files[0];

    // setting up the reader
    var reader = new FileReader();
    reader.readAsText(file); // this is reading as data url

    // here we tell the reader what to do when it's done reading...
    reader.onload = readerEvent => {
        var content = readerEvent.target.result; // this is the content!
        socket.emit('file_command', {cmd: 'import_esdl_from_file', filename: file.name, file_content: content});
    }

    // show loader
    show_loader();
}

function send_cmd_load_ESDL() {
    socket.emit('file_command', {cmd: 'get_list_from_store'});
}

function send_cmd_import_ESDL() {
    socket.emit('file_command', {cmd: 'get_list_from_store'});
}

function click_load_ESDL_button(obj) {
    select = document.getElementById('load_es_selection');
    es_id = select.options[select.selectedIndex].value;
    es_title = select.options[select.selectedIndex].innerHTML;
    // console.log(es_id);

    // title_div = document.getElementById('es_title');
    // title_div.innerHTML = '<h1>' + es_title + '</h1>';

    socket.emit('file_command', {cmd: 'load_esdl_from_store', id: es_id});

    // show loader
    show_loader();
}

function click_import_ESDL_button(obj) {
    select = document.getElementById('load_es_selection');
    es_id = select.options[select.selectedIndex].value;
    socket.emit('file_command', {cmd: 'import_esdl_from_store', id: es_id})
    show_loader();
}

// Save ESDL: creates an IFrame to download, otherwise the websocket connection will be reset
// if we set the window.location.href directly...
var $idown;  // Keep it outside of the function, so it's initialized once.
function save_ESDL(e, prefix) {
    let url = prefix+'/esdl'
    //if ($idown) {
    //    $idown.attr('src',url);
    //} else {
    //    $idown = $('<iframe>', { id:'idown', src:url }).hide().appendTo('body');
    //}
    // The following code does a HTML5 download request.
    // From stackoverflow:
    // simply setting the window.url to the download url does not work as it navigates away from the current
    // page, releasing the websocket connection.
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.responseType = 'arraybuffer';
    xhr.onload = function () {
        if (this.status === 200) {
            var filename = "";
            var disposition = xhr.getResponseHeader('Content-Disposition');
            if (disposition && disposition.indexOf('attachment') !== -1) {
                var filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                var matches = filenameRegex.exec(disposition);
                if (matches != null && matches[1]) filename = matches[1].replace(/['"]/g, '');
            }
            var type = xhr.getResponseHeader('Content-Type');

            var blob;
            if (typeof File === 'function') {
                try {
                    blob = new File([this.response], filename, { type: type });
                } catch (e) { /* Edge */ }
            }
            if (typeof blob === 'undefined') {
                blob = new Blob([this.response], { type: type });
            }

            if (typeof window.navigator.msSaveBlob !== 'undefined') {
                // IE workaround for "HTML7007: One or more blob URLs were revoked by closing the blob for which they were created. These URLs will no longer resolve as the data backing the URL has been freed."
                window.navigator.msSaveBlob(blob, filename);
            } else {
                var URL = window.URL || window.webkitURL;
                var downloadUrl = URL.createObjectURL(blob);

                if (filename) {
                    // use HTML5 a[download] attribute to specify filename
                    var a = document.createElement("a");
                    // safari doesn't support this yet
                    if (typeof a.download === 'undefined') {
                        window.location = downloadUrl;
                    } else {
                        a.href = downloadUrl;
                        a.download = filename;
                        document.body.appendChild(a);
                        a.click();
                    }
                } else {
                    window.location = downloadUrl;
                }

                setTimeout(function () { URL.revokeObjectURL(downloadUrl); }, 100); // cleanup
            }
        }
    };
    xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    xhr.send();
}

function send_cmd_store_ESDL() {
    // socket.emit('file_command', {cmd: 'store_esdl'});
    esdl_store_save_window();
}

function send_download_ESDL() {
    socket.emit('file_command', {cmd: 'download_esdl'});
}
