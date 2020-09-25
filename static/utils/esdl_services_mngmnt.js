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

// ESDLServicesMngmnt
// requires:
// map and socketio as global variables


class ESDLServicesMngmnt {

    send_store_settings() {
        let settings = $('#srvs_mngmnt_textarea').val();
        let settings_json = JSON.parse(settings);
        socket.emit('store_esdl_services_list', settings_json);
        set_esdl_services_information(settings_json);
    }

    settings_window_contents() {
        let $div = $('<div>').attr('id', 'esdl_services_mngmnt_window_div');
        $div.append($('<h1>').text('ESDL Services Management management'));

        $div.append($('<textarea>').attr('id', 'srvs_mngmnt_textarea').addClass('textarea_srvs_mngmnt'));

        $div.append(
            $('<div>').append($('<button>').text('Store').click(function() {esdl_services_mngmnt_plugin.send_store_settings();}))
        );

        socket.emit('get_esdl_services_list', function(res) {
            $('#srvs_mngmnt_textarea').val(JSON.stringify(res, null, 4));
        });

        return $div;
    }

    static create(event) {
        if (event.type === 'client_connected') {
            esdl_services_mngmnt_plugin = new ESDLServicesMngmnt();
            console.log("ESDLServicesMngmnt plugin initiated!!")
            return esdl_services_mngmnt_plugin;
        }
        if (event.type === 'settings_menu_items') {
            let menu_items = {
                'value': 'esdl_services_mngmnt_plugin',
                'text': 'ESDL Services Management plugin',
                'settings_func': esdl_services_mngmnt_plugin.settings_window_contents,
                'sub_menu_items': []
            };

            return menu_items;
        }
    }
}

var esdl_services_mngmnt_plugin;

$(document).ready(function() {
    extensions.push(function(event) { return ESDLServicesMngmnt.create(event) });
});