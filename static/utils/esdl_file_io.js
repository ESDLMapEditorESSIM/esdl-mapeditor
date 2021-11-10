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

function loas_esdl_files(event) {
    var file = event.target.files[0];

    let files = [];
    for (let file_nr=0; file_nr<event.target.files.length; file_nr++) {
        let file = event.target.files[file_nr];
        if (file) files.push(file);
    }

    if (!files.length) return;

    let readers = [];
    for (let i=0; i<files.length; i++) {
        readers.push(this.read_esdl_file_as_array_buffer(files[i]));
    }

    Promise.all(readers).then((array_with_file_info) => {
        let load_esdl_url = resource_uri + '/esdl_file_io';

        show_loader();
        $.ajax({
            url: load_esdl_url,
            type: 'POST',
            data: {file_info: array_with_file_info},
            success: function (data) {
               // don't hide loader yet ???   but who should?
               hide_loader();
               // console.log(data);

               socket.emit('process_loaded_energysystems');
            },
            error: function(xhr, ajaxOptions, thrownError) {
               hide_loader();
               alert('Error occurred in loas_esdl_files: ' + xhr.status + ' - ' + thrownError);
            }
        });
    });
}