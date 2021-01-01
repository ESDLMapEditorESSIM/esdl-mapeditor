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

class ViewModes {
    constructor() {
        this.initSocketIO();
    }

    initSocketIO() {
        console.log("Registering ViewModes plugin");
    }

    UISettings() {
        let $div = $('<div>').addClass('ui_settings_div').append($('<h3>').text('View modes'));

        let $view_mode_select = $('<select>').attr('id', 'vm_select').attr('size', 5);
        $div.append($('<p>')
            .text('Select your default view mode (the view mode influences what parameters are shown ' +
              'for ESDL assets and determines the available assets on the Asset Draw Toolbar. You need to refresh ' +
              'your browser to apply the changes.')
            .append($('<p>')).append($view_mode_select));

        $view_mode_select.change(function() {
            let mode = $('#vm_select').val();

            socket.emit('view_modes_set_mode', {
                mode: mode
            });
        });

        socket.emit('view_modes_get_possible_modes', function(res) {
            let possible_modes = res['possible_modes'];
            for (let i=0; i<possible_modes.length; i++) {
                let $option = $('<option>').attr('value',possible_modes[i]).text(possible_modes[i]);
                $view_mode_select.append($option);
            }
        });

        return $div;
    }

    static create(event) {
        if (event.type === 'client_connected') {
            view_modes_plugin = new ViewModes();
            return view_modes_plugin;
        }
        if (event.type === 'ui_settings_div') {
            return view_modes_plugin.UISettings();
        }
    }
}

var view_modes_plugin;   // global variable for the ViewModes plugin

$(document).ready(function() {
    extensions.push(function(event) { return ViewModes.create(event) });
});