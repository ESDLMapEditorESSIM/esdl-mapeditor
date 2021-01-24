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

class Port_profile_viewer{
    constructor() {
        this.initSocketIO();
        this.asset_port_profile_list = null;
    }

    initSocketIO() {
        console.log("Registering socket io bindings for Port profile viewer plugin");
    }

    show_window() {
        sidebar_b.setContent(port_profile_viewer_plugin.create_sidebar_content().get(0));
        sidebar_b.show();
        port_profile_viewer_plugin.change_selected_profile();
    }

    update_port_profile_list() {
        let port_idx = $('#port_select').val();
        let profile_list = port_profile_viewer_plugin.asset_port_profile_list[port_idx].profiles;

        let $profile_select = $('#profile_select');
        $profile_select.empty();

        if (profile_list) {
            for (let i=0; i<profile_list.length; i++) {
                let $option = $('<option>').attr('value', i).text(profile_list[i].uiname);
                $profile_select.append($option);
            }
            port_profile_viewer_plugin.change_selected_profile();
        } else {
            $('#profile_div').html('<p>Error - no profiles attached to this port</p>');
        }
    }

    change_selected_profile() {
        let port_idx = $('#port_select').val();
        let profile_idx = $('#profile_select').val();
        let profile_info = port_profile_viewer_plugin.asset_port_profile_list[port_idx].profiles[profile_idx];

        if (profile_info) {
            socket.emit('get_profile_panel', profile_info['id'], function(embed_url) {
                console.log(embed_url);
                if (embed_url) {
                    $('#profile_div').html('<iframe width="100%" height="100%" src="'+embed_url+'"></iframme>');
                } else {
                    $('#profile_div').html('<p>Error - no profile URL returned</p>');
                }
            });
        } else {
            $('#profile_div').html('<p>Error - no profiles attached to this port</p>');
        }
    }

    create_sidebar_content() {
        let $div = $('<div>').attr('id', 'port_profile_viewer_main_div');
        let $title = $('<h1>').attr('id', 'port_profile_viewer_title').text('Port profile viewer');
        $div.append($title);

        let $content_div = $('<div>').attr('id', 'port_profile_viewer_content_div').addClass('sidebar-div');
        $div.append($content_div);

        let $select_div = $('<div>').attr('id', 'select_div');
        $content_div.append($select_div);
        let $port_select = $('<select>').attr('id', 'port_select');
        for (let i=0; i<port_profile_viewer_plugin.asset_port_profile_list.length; i++) {
            let $option = $('<option>')
                .attr('value', i)
                .text(port_profile_viewer_plugin.asset_port_profile_list[i].port_name);
            $port_select.append($option);
        }
        $port_select.change(port_profile_viewer_plugin.update_port_profile_list);

        let $profile_select = $('<select>').attr('id', 'profile_select');
        for (let i=0; i<port_profile_viewer_plugin.asset_port_profile_list[0].profiles.length; i++) {
            let $option = $('<option>')
                .attr('value', i)
                .text(port_profile_viewer_plugin.asset_port_profile_list[0].profiles[i].uiname);
            $profile_select.append($option);
        }
        $profile_select.change(port_profile_viewer_plugin.change_selected_profile);

        $select_div.append($port_select);
        $select_div.append($profile_select);

        let $profile_div = $('<div>').attr('id', 'profile_div');
        $content_div.append($profile_div);

        return $div;
    }

    request_profiles_for_asset(e, id) {
        socket.emit('port_profile_viewer_request_asset', id, function(port_profile_list) {
            port_profile_viewer_plugin.asset_port_profile_list = port_profile_list;
            port_profile_viewer_plugin.show_window();
        });
    }

    static create(event) {
        if (event.type === 'client_connected') {
            port_profile_viewer_plugin = new Port_profile_viewer();
            return port_profile_viewer_plugin;
        }
        if (event.type === 'add_contextmenu') {
            let layer = event.layer;
            let layer_type = event.layer_type;
            let id = layer.id;
            if (layer_type === 'marker' || layer_type === 'line') {
                layer.options.contextmenuItems.push({
                    text: 'Port profile viewer',
                    icon: resource_uri + 'icons/Graph.png',
                    callback: function(e) {
                        port_profile_viewer_plugin.request_profiles_for_asset(e, id);
                    }
                });
            }
        }
    }
}

var port_profile_viewer_plugin;   // global variable for the port profile viewer plugin

$(document).ready(function() {
    extensions.push(function(event) { Port_profile_viewer.create(event) });
});
