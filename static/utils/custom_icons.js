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


class CustomIcons {
    constructor() {
        this.initSocketIO();
        this.custom_icons = null;
    }

    initSocketIO() {
        console.log("Registering socket io bindings for CustomIcons")
        var self = this;
    }

    settings_window_contents() {
        let $div = $('<div>').attr('id', 'custom_icons_settings_window_div');
        window.activate_custom_icons_settings();
        return $div;
    }

    get_custom_icons() {
        return $.get('/custom_icons')
            .done((res) => {
                let icons_list = res.icons_list;
                let icons_dict = {};
                for (let i=0; i<icons_list.length; i++) {
                    console.log(icons_list[i].selector);
                    icons_dict[icons_list[i].selector] = icons_list[i];
                }
                custom_icons_plugin.custom_icons = icons_dict;
            })
            .fail((error) => {
                // eslint-disable-next-line
                console.error(error);
            });
    }

    get_icon_for(asset_class, extra_attrs) {
        for (let ea in extra_attrs) {
            if (asset_class + '.' + ea + '(\'' + extra_attrs[ea] + '\')' in custom_icons_plugin.custom_icons) {
                let custom_icon = custom_icons_plugin.custom_icons[asset_class + '.' + ea + '(\'' + extra_attrs[ea] + '\')'];
                return {
                    contentType: custom_icon.icon.content_type,
                    imageData: custom_icon.icon.data
                }
            }
        }
        return null;
    }

    static create(event) {
        if (event.type === 'client_connected') {
            custom_icons_plugin = new CustomIcons();
            console.log("CustomIcons initiated!!")
            custom_icons_plugin.get_custom_icons();
            return custom_icons_plugin;
        }
        if (event.type === 'settings_menu_items') {
            let menu_items = {
                'value': 'custom_icons_plugin_settings',
                'text': 'Custom icons plugin',
                'settings_func': custom_icons_plugin.settings_window_contents,
                'sub_menu_items': []
            };

            return menu_items;
        }
    }
}

var custom_icons_plugin;

$(document).ready(function() {
    extensions.push(function(event) { return CustomIcons.create(event) });
});