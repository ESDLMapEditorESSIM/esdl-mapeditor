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

class ModelContexts {
    constructor() {
        console.log("Registering ViewModes plugin");
    }

    UISettings() {
        let $div = $('<div>').addClass('ui_settings_div').append($('<h3>').text('View modes'));

        let $model_context_select = $('<select>').attr('id', 'vm_select').attr('size', 5);
        $div.append($('<p>')
            .text('Select your default view mode (the view mode influences what parameters are shown ' +
              'for ESDL assets and determines the available assets on the Asset Draw Toolbar. You need to refresh ' +
              'your browser to apply the changes.')
            .append($('<p>')).append($model_context_select));

        $model_context_select.change(function() {
            let mode = $('#vm_select').val();

            socket.emit('model_contexts_set_mode', {
                mode: mode
            });
        });

        socket.emit('model_contexts_get_mode_info', function(res) {
            let current_mode = res['current_mode'];
            let possible_modes = res['possible_modes'];
            for (let i=0; i<possible_modes.length; i++) {
                let $option = $('<option>').attr('value',possible_modes[i]).text(possible_modes[i]);
                if (possible_modes[i] === current_mode)
                    $option = $option.attr('selected', true);
                $model_context_select.append($option);
            }
        });

        return $div;
    }

    static create(event) {
        if (event.type === 'client_connected') {
            model_contexts_plugin = new ModelContexts();
            return model_contexts_plugin;
        }
        if (event.type === 'ui_settings_div') {
            return model_contexts_plugin.UISettings();
        }
    }
}

var model_contexts_plugin;   // global variable for the ViewModes plugin

$(document).ready(function() {
    extensions.push(function(event) { return ModelContexts.create(event) });
});