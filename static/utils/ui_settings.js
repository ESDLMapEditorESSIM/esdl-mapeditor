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

        let $visible_on_startup = $('<input>').attr('type', 'checkbox').attr('id', 'adt_visible').attr('value', 'adt_visible').attr('name', 'adt_visible');
        let $adtvis_label = $('<label>').attr('for', 'adt_visible').text('Asset draw toolbar visible on startup');
        $div.append($('<p>').append($visible_on_startup).append($adtvis_label));

        $visible_on_startup.change(function() {
            let adt_visible = $('#adt_visible').is(':checked');
            socket.emit('mapeditor_user_ui_setting_set', {category: 'asset_bar', name: 'visible_on_startup', value: adt_visible});
        });

        socket.emit('mapeditor_user_ui_setting_get', {category: 'asset_bar', name: 'visible_on_startup'}, function(res) {
            let adt_visible = res;
            $('#adt_visible').prop('checked', adt_visible);
        });

        return $div;
    }

    settings_window_contents() {
        let $div = $('<div>').attr('id', 'ui_settings_window_div');
        $div.append($('<h1>').text('UI Settings'));

        $div.append(ui_settings_plugin.asset_draw_toolbar_settings());

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