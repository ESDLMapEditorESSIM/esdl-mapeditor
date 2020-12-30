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

    settings_window_contents() {
        let $div = $('<div>').attr('id', 'ui_settings_window_div');
        $div.append($('<h1>').text('UI Settings'));

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