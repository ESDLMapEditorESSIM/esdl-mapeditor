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

// Shapefile converter
// requires:
// dialog, map and socketio as global variables

var shapefile_converter_window; // global shapefile_convert_window variable
var num_table_rows = 5;

class ShapefileConverter {
    constructor() {
        this.initSocketIO();
        this.history = [];
        this.dialog = new L.control.dialog();
        this.num_uploaded_files = 0;
        this.answer_received_for_row = {};

        let width = map.getSize();
        this.width = 1200;
        this.height = 750;
        this.x = 10;
        this.y = (width.x/2)-(this.width/2);
    }

    open_window() {
        if (dialog === undefined) {
            console.log("ERROR: dialog not defined");
            // create dialog
            return;
        }

        this.num_uploaded_files = 0;
        this.answer_received_for_row = {};

        let content = this.shapeFileUpload();
        dialog.setContent(content);
        dialog.setSize([shapefile_converter_window.width, shapefile_converter_window.height]);
        dialog.setLocation([shapefile_converter_window.x, shapefile_converter_window.y]);
        dialog.setTitle('ESDL shapefile converter');
        $('.leaflet-control-dialog-contents').scrollTop(0);
        dialog.open();
    }

    shapeFileUpload() {
        let $div = $('<div />').attr('id', 'shapefile_upload_div');
        $div.append($('<p>').append("Please upload the shapefiles (zip format) in the table below and specify the accompanying energy assets afterwards"));

        let $table = $('<table>').attr('id', 'shapefile_upload_table').addClass('pure-table pure-table-striped');
        $table.append('<thead>').children('thead').append('<tr />').children('tr').append('<th>Zip file</th><th>Containing shapefiles - associated EnergyAsset</th>');
        let $tbody = $table.append('<tbody />').children('tbody');
        for (let row=0; row<num_table_rows; row++) {
            let $file_input = $('<input>')
                .attr('id', 'file_input_shapefile_'+row)
                .attr('type', 'file')
                .attr('accept', '.zip')
                .change(function(e){console.log(e);});

            $tbody.append('<tr />').children('tr:last')
                .append($('<td>').append($file_input))
                .append($('<td>').attr('id', 'td_shapefiles'+row));
//                .append($('<td>').append($select));
        }
        $div.append($table);

        let $b = $('<button>').attr('id', 'action_button').text('Upload shapefiles');
        let $p = $('<p>').append($b);

        $b.click(function(e) {
            console.log('clicked!');
            shapefile_converter_window.parse_file_selection();
        });
        $div.append($p);

        return $div.get(0);
    }

    parse_file_selection() {
        for (let zipfile_row=0; zipfile_row<num_table_rows; zipfile_row++) {
//            let selected_energyasset = $('#asset_select_shapefile_'+row).val();
            let file_select = $('#file_input_shapefile_'+zipfile_row);
            let file = file_select[0].files[0];

            if (file) {
                console.log(file);
                this.num_uploaded_files = this.num_uploaded_files + 1;
                let reader = new FileReader();
                reader.onload = readerEvent => {
                    let contents = readerEvent.target.result;
                    socket.emit('shpcvrt_receive_files', {zipfile_row: zipfile_row, filename: file.name, file_content: contents});
                }
                reader.readAsArrayBuffer(file);
            }
        }
    }

    updateShapefileOverview(message) {
        let zipfile_row = message['zipfile_row'];
        let files = message['files'];

        this.answer_received_for_row[zipfile_row] = files;

        console.log(zipfile_row);
        console.log(files);

        let table_data = $('#td_shapefiles'+zipfile_row);

        let $table = $('<table>').addClass('pure-table pure-table-striped');
        let $tbody = $table.append('<tbody />').children('tbody');
        for (let row=0; row<files.length; row++) {
            let $select = $('<select>').attr('id', 'asset_select_shapefile_'+zipfile_row+'_'+row);
            $select.append($("<option>").val("type_record").text("Use type record"));
            $select.append($("<option>").val("ignore").text("Ignore"));
            $select.append($("<option>").val("esdl_area").text("ESDL Area"));

            for (let cap in cap_pot_list["capabilities"]) {
                let ea_per_cap = cap_pot_list["capabilities"][cap];
                let $optgroup = $('<optgroup>')
                    .attr('label', cap);
                $optgroup.style = 'font-face: bold; font-size: 10px';

                for (let ea in ea_per_cap) {
                    let $option = $("<option>")
                        .val(ea_per_cap[ea])
                        .text(ea_per_cap[ea]);
                    $optgroup.append($option);
                }
                $select.append($optgroup);
            }

            $tbody.append('<tr />').children('tr:last')
                .append($('<td>').append(files[row]))
                .append($('<td>').attr('id', 'td_energyasset_'+zipfile_row+'_'+row).append($select));
        }

        table_data.html($table);

        let $button = $('#action_button')
        $button.text('Convert shapefiles to ESDL')
        $button.off('click');
        $button.click(function(e) {
            shapefile_converter_window.parse_energyasset_selection();
        });
    }

    parse_energyasset_selection() {
        console.log(this.answer_received_for_row);

        let shapefile_energyasset_list = [];
        for (let zipfile_row in this.answer_received_for_row) {
            let files = this.answer_received_for_row[zipfile_row];
            for (let row=0; row<files.length; row++) {
                let $select = $('#asset_select_shapefile_'+zipfile_row+'_'+row);
                let energy_asset = $select.val();

                // TODO: check if no energy asset was chosen

                shapefile_energyasset_list.push({
                    zipfile_row: zipfile_row,
                    row: row,
                    shapefile_name: files[row],
                    energy_asset: energy_asset
                });
            }
        }
        socket.emit('shpcvrt_receive_energyasset_info', shapefile_energyasset_list);
    }

    initSocketIO() {
        console.log("Registering socket io bindings for ShapefileConverter")

        socket.on('shpcvrt_files_in_zip', function(message) {
            shapefile_converter_window.updateShapefileOverview(message);
        });
    }

    // all globals in here
    static handle_dialog_resize_move() {
        shapefile_converter_window.width = dialog.options.size[0];
        shapefile_converter_window.height = dialog.options.size[1];
        shapefile_converter_window.x = dialog.options.anchor[0];
        shapefile_converter_window.y = dialog.options.anchor[1];
    }

    static create(event) {
        if (event.type === 'client_connected') {
            shapefile_converter_window = new ShapefileConverter();
            map.on('dialog:resizeend', ShapefileConverter.handle_dialog_resize_move);
            map.on('dialog:moving', ShapefileConverter.handle_dialog_resize_move);
            map.on('dialog:closed', function(e) {
                // socket.emit('esdl_compare_closed');
                console.log('ESDL shapefile converter window closed');
            });
            return shapefile_converter_window;
        }
    }
}

$(document).ready(function() {
    extensions.push(function(event) { ShapefileConverter.create(event) });
});