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

 class ETMInterface {
    constructor() {
        this.initSocketIO();
    }

    initSocketIO() {
        console.log("Registering socket io bindings for ETMInterface plugin")
    }

    show_info(id, data) {
        sidebar.setContent(etm_interface_plugin.create_sidebar_content(id, data).get(0));
        sidebar.show();
    }

    create_sidebar_content(id, data) {
        let $div = $('<div>').attr('id', 'etm-main-div');
        let $title = $('<h1>').text('ETMInterface - '+id);
        $div.append($title);

        $div.append($('<p>').text(data));
        return $div;
    }

    area_info(event, id) {
        socket.emit('etm_get_sankey_data', id, function(res) {
            etm_interface_plugin.show_info(id, res);
        });
    }

    static create(event) {
        if (event.type === 'client_connected') {
            etm_interface_plugin = new ETMInterface();
            return etm_interface_plugin;
        }
        if (event.type === 'add_contextmenu') {
            let layer = event.layer;
            let layer_type = event.layer_type;
            let id = layer.id;
            if (layer_type === 'area') {
                layer.options.contextmenuItems.push({
                    text: 'get ETM sankey info',
                    icon: resource_uri + 'icons/Vesta.png',
                    callback: function(e) {
                        etm_interface_plugin.area_info(e, id);
                    }
                });
            }
        }
        if (event.type === 'settings_menu_items') {
            let menu_items = {
                'value': 'etm_interface_plugin_settings',
                'text': 'ETMInterface plugin',
                'settings_func': function() { return $('<p>').text('ETMInterface plugin')},
                'sub_menu_items': []
            };

            return menu_items;
        }
    }
}

var etm_interface_plugin;   // global variable for the etm_interface plugin

$(document).ready(function() {
    extensions.push(function(event) { return ETMInterface.create(event) });
});