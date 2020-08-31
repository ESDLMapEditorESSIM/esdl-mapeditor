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

 class ETMLocal {
    constructor() {
        this.initSocketIO();
    }

    initSocketIO() {
        console.log("Registering socket io bindings for ETMLocal plugin")
    }

    show_info(id, data) {
        sidebar.setContent(etmlocal_plugin.create_sidebar_content(id, data).get(0));
        sidebar.show();
    }

    create_sidebar_content(id, data) {
        let $div = $('<div>').attr('id', 'etmlocal-main-div');
        let $title = $('<h1>').text('ETMLocal - '+id);
        $div.append($title);

        $div.append(etmlocal_plugin.generate_table(data));

        return $div;
    }

    generate_table(data) {
        if (Object.keys(data[0]).length !== 0) {
            let $table = $('<table>').addClass('pure-table pure-table-striped').attr('id', 'etmlocal_table');
            let $thead = $('<thead>').append($('<tr>').append($('<th>').text('Key')).append($('<th>')
               .text('Value')));
            let $tbody = $('<tbody>');
            $table.append($thead);
            $table.append($tbody);

            for (let key in data[0]) {
                let value = data[0][key];
                $tbody.append($('<tr>')
                        .append($('<td>').css('width', '220px').css('font-size', '9px').css('word-break', 'break-all').text(key))
                        .append($('<td>').css('font-size', '9px').text(value)));
            }

            return $table;
        } else {
            return $('<p>').text('No information');
        }
    }

    area_info(event, id) {
        socket.emit('etmlocal_get_info', id, function(res) {
            etmlocal_plugin.show_info(id, res);
        });
    }

    static create(event) {
        if (event.type === 'client_connected') {
            etmlocal_plugin = new ETMLocal();
            return etmlocal_plugin;
        }
        if (event.type === 'add_contextmenu') {
            let layer = event.layer;
            let layer_type = event.layer_type;
            let id = layer.id;
            if (layer_type === 'area') {
                layer.options.contextmenuItems.push({
                    text: 'get ETMLocal info',
                    icon: resource_uri + 'icons/Vesta.png',
                    callback: function(e) {
                        etmlocal_plugin.area_info(e, id);
                    }
                });
            }
        }
        if (event.type === 'settings_menu_items') {
            let menu_items = {
                'value': 'etmlocal_plugin_settings',
                'text': 'ETMLocal plugin',
                'settings_func': function() { return $('<p>').text('ETMLocal plugin')},
                'sub_menu_items': []
            };

            return menu_items;
        }
    }
}

var etmlocal_plugin;   // global variable for the etmlocal plugin

$(document).ready(function() {
    extensions.push(function(event) { return ETMLocal.create(event) });
});