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

class UISettings {

    // Asset draw toolbar has no separate extension (it's part of the Vue code), so include settings div here
    asset_draw_toolbar_settings() {
        let $div = $('<div>').addClass('ui_settings_div').append($('<h3>').text('Asset draw toolbar'));

        let $adtvis_on_startup = $('<input>').attr('type', 'checkbox').attr('id', 'adt_visible').attr('value', 'adt_visible').attr('name', 'adt_visible');
        let $adtvis_label = $('<label>').attr('for', 'adt_visible').text('Asset draw toolbar visible on startup');
        $div.append($('<p>').append($adtvis_on_startup).append($adtvis_label));

        $adtvis_on_startup.change(function() {
            let adt_visible = $('#adt_visible').is(':checked');
            socket.emit('mapeditor_user_ui_setting_set', {category: 'asset_bar', name: 'visible_on_startup', value: adt_visible});
        });

        socket.emit('mapeditor_user_ui_setting_get', {category: 'asset_bar', name: 'visible_on_startup'}, function(res) {
            let adt_visible = res;
            $('#adt_visible').prop('checked', adt_visible);
        });

        return $div;
    }

    // Asset UI information has no separate extension (it's part of the Vue code), so include settings div here
    asset_ui_information_settings() {
        let $div = $('<div>').addClass('ui_settings_div').append($('<h3>').text('Asset information on map'));

        let $aivis_on_map = $('<input>').attr('type', 'checkbox').attr('id', 'ai_visible').attr('value', 'ai_visible').attr('name', 'ai_visible');
        let $aivis_label = $('<label>').attr('for', 'ai_visible').text('Asset information is visible on the map');
        $div.append($('<p>').append($aivis_on_map).append($aivis_label));

        $aivis_on_map.change(function() {
            let ai_visible = $('#ai_visible').is(':checked');
            socket.emit('mapeditor_user_ui_setting_set', {category: 'tooltips', name: 'show_asset_information_on_map', value: ai_visible});
        });

        socket.emit('mapeditor_user_ui_setting_get', {category: 'tooltips', name: 'show_asset_information_on_map'}, function(res) {
            let ai_visible = res;
            $('#ai_visible').prop('checked', ai_visible);
        });

        return $div;
    }

    // Services toolbar has no separate extension (it's part of the Vue code), so include settings div here
    services_toolbar_settings() {
        let $div = $('<div>').addClass('ui_settings_div').append($('<h3>').text('Services toolbar'));

        let $stbvis_on_startup = $('<input>').attr('type', 'checkbox').attr('id', 'stb_visible').attr('value', 'stb_visible').attr('name', 'stb_visible');
        let $stbvis_label = $('<label>').attr('for', 'stb_visible').text('Services toolbar is visible on startup');
        $div.append($('<p>').append($stbvis_on_startup).append($stbvis_label));

        $stbvis_on_startup.change(function() {
            let stb_visible = $('#stb_visible').is(':checked');
            socket.emit('mapeditor_user_ui_setting_set', {category: 'services_toolbar', name: 'visible_on_startup', value: stb_visible});
        });

        socket.emit('mapeditor_user_ui_setting_get', {category: 'services_toolbar', name: 'visible_on_startup'}, function(res) {
            let stb_visible = res;
            $('#stb_visible').prop('checked', stb_visible);
        });

        return $div;
    }

    settings_window_contents() {
        let $div = $('<div>').attr('id', 'ui_settings_window_div');
        $div.append($('<h1>').text('UI Settings'));

        $div.append(ui_settings_plugin.asset_draw_toolbar_settings());
        $div.append(ui_settings_plugin.asset_ui_information_settings());
        $div.append(ui_settings_plugin.services_toolbar_settings());

        for (let i=0; i<extensions.length; i++) {
            let extensions_function = extensions[i];
            let div = extensions_function({type: 'ui_settings_div'});
            if (div) $div.append(div);
        }

        return $div;
    }

    static create(event) {
        if (event.type === 'client_connected') {
            ui_settings_plugin = new UISettings();
            console.log("UISettings plugin initiated!!")
            return ui_settings_plugin;
        }
        if (event.type === 'settings_menu_items') {
            let menu_items = {
                'value': 'ui_settings_plugin',
                'text': 'UI Settings',
                'settings_func': ui_settings_plugin.settings_window_contents,
                'sub_menu_items': []
            };

            return menu_items;
        }
    }
}

var ui_settings_plugin;

$(document).ready(function() {
    extensions.push(function(event) { return UISettings.create(event) });
});