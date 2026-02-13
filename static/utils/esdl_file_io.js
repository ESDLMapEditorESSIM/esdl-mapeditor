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


function read_esdl_file_as_array_buffer(file) {
    return new Promise(function(resolve, reject) {
        let file_reader = new FileReader();

        file_reader.onload = function() {
            let result = {
              file: file_reader.result,
              filename: file.name
            }
            resolve(result);
        };
        file_reader.onerror = function() {
            reject(file_reader);
        };

        file_reader.readAsDataURL(file);
    });
}

function load_esdl_files(event) {
    const files = [];
    for (let file_nr=0; file_nr<event.target.files.length; file_nr++) {
        const file = event.target.files[file_nr];
        if (file) {
            files.push(file);
        }
    }

    if (!files.length) {
        return;
    }

    const readers = [];
    for (let i=0; i<files.length; i++) {
        readers.push(read_esdl_file_as_array_buffer(files[i]));
    }

    const load_esdl_url = window.resource_uri + '/esdl_file_io';
    Promise.all(readers).then((array_with_file_info) => {
        window.show_loader();
        $.ajax({
            url: load_esdl_url,
            type: 'POST',
            data: { file_info: array_with_file_info, is_import: false },
            success: function (response) {
                window.hide_loader();
                if (response && (response.status === 'pending_prompt' || response.status === 'error_prompt_sent')) {
                    return;
                }
                socket.emit('process_loaded_energysystems');
            },
            error: handle_esdl_file_upload_error,
        });
    }).catch((error) => {
        console.error('Error reading files:', error);
        alert('Error reading files: ' + error);
    });
}


function import_esdl_helper(event) {
    const files = [];
    for (let file_nr=0; file_nr<event.target.files.length; file_nr++) {
        const file = event.target.files[file_nr];
        if (file) {
            files.push(file);
        }
    }

    if (!files.length) {
        return;
    }

    const readers = [];
    for (let i=0; i<files.length; i++) {
        readers.push(read_esdl_file_as_array_buffer(files[i]));
    }

    const import_esdl_url = window.resource_uri + '/esdl_file_io';
    Promise.all(readers).then((array_with_file_info) => {
        // here we tell the reader what to do when it's done reading...
        window.show_loader();
        $.ajax({
            url: import_esdl_url,
            type: 'POST',
            // data: {file_content: content, filename: file.name, import: true},
            data: { file_info: array_with_file_info, is_import: true },
            success: function (response) {
                window.hide_loader();
                if (response && (response.status === 'pending_prompt' || response.status === 'error_prompt_sent')) {
                    return;
                }
                window.socket.emit('process_loaded_energysystems');
            },
            error: handle_esdl_file_upload_error,
        });
    }).catch((error) => {
        console.error('Error reading files:', error);
        alert('Error reading files: ' + error);
    });
}

function import_esdl_files(event) {
    import_esdl_helper(event, false);
}


/**
 * Function to handle errors in the AJAX request for loading or importing ESDL files.
 * @param xhr
 * @param textStatus
 * @param thrownError
 */
function handle_esdl_file_upload_error(xhr, textStatus, thrownError) {
    window.hide_loader();
    console.error('AJAX request failed:', xhr);
    console.error('Status:', xhr.status);
    console.error('Error:', thrownError);
    console.error('Error message:', xhr.responseJSON);
    let response_msg = "";
    if (xhr.responseJSON && xhr.responseJSON.message) {
        response_msg = '\n\nError message: ' +  xhr.responseJSON.message;
    }
    alert('Error occurred during loading or importing of ESDL file(s): ' + xhr.status + ' - ' + thrownError + response_msg);
}
