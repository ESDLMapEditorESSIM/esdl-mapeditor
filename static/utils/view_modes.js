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

        socket.emit('view_modes_initialize');
    }

    initSocketIO() {
        console.log("Registering socket io bindings for ViewModes plugin")
    }

    static create(event) {
        if (event.type === 'client_connected') {
            view_modes_plugin = new ViewModes();
            return view_modes_plugin;
        }
        // if (event.type === 'add_contextmenu') {
        //     let layer = event.layer;
        //     let layer_type = event.layer_type;
        //     let id = layer.id;
        //     if (layer_type === 'marker') {
        //         layer.options.contextmenuItems.push({
        //             text: 'edit attributes',
        //             icon: resource_uri + 'icons/Edit.png',
        //             callback: function(e) {
        //                 object_properties_window(id);
        //             }
        //         });
        //     }
        // }
        if (event.type === 'settings_menu_items') {
            let menu_items = {
                'value': 'view_modes_plugin_settings',
                'text': 'MapEditor view modes',
                'settings_func': function() { return $('<p>').text('MapEditor view modes')},
                'sub_menu_items': []
            };

            return menu_items;
        }
    }
}

var view_modes_plugin;   // global variable for the ViewModes plugin

$(document).ready(function() {
    extensions.push(function(event) { return ViewModes.create(event) });
});