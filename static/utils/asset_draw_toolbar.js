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


class AssetDrawToolbar {
    constructor() {
        this.initSocketIO();
    }

    initSocketIO() {
        console.log("Registering socket io bindings for AssetDrawToolbar")
        var self = this;

        socket.on('recently_used_edr_assets', function(res) {
            console.log(`Test: ${res}`);
        });
    }

    settings_window_contents() {
        let $div = $('<div>').attr('id', 'asset_draw_toolbar_settings_window_div');
        $div.append($('<h1>').text('Asset Draw Toolbar settings'));
        $div.append($('<p>').text('Please select one of the sub menus to change the settings.'));
        return $div;
    }

    standard_assets_settings_contents() {
        window.activate_asset_draw_toolbar_standard_assets_settings();
        return $('<div>');
    }
    edr_assets_settings_contents() {
        window.activate_asset_draw_toolbar_edr_assets_settings();
        return $('<div>');
    }

    static create(event) {
        if (event.type === 'client_connected') {
            asset_draw_toolbar_plugin = new AssetDrawToolbar();
            console.log("AssetDrawToolbar initiated!!")
            return asset_draw_toolbar_plugin;
        }
        if (event.type === 'settings_menu_items') {
            let menu_items = {
                'value': 'asset_draw_toolbar_plugin_settings',
                'text': 'AssetDrawToolbar plugin',
                'settings_func': asset_draw_toolbar_plugin.settings_window_contents,
                'sub_menu_items': [{
                    'value': 'asset_draw_toolbar_empty_assets_settings',
                    'text': 'Standard assets',
                    'settings_func': asset_draw_toolbar_plugin.standard_assets_settings_contents,
                    'sub_menu_items': []
                }, {
                    'value': 'asset_draw_toolbar_edr_assets_settings',
                    'text': 'EDR assets',
                    'settings_func': asset_draw_toolbar_plugin.edr_assets_settings_contents,
                    'sub_menu_items': []
                }]
            };

            return menu_items;
        }
    }
}

var asset_draw_toolbar_plugin;

$(document).ready(function() {
    extensions.push(function(event) { return AssetDrawToolbar.create(event) });
});