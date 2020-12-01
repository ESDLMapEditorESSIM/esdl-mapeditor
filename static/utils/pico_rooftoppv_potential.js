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

class PICO_RooftopPV {
    constructor() {
        this.potential_id = null;
        this.area_id = null;
        this.initSocketIO();
    }

    initSocketIO() {
        console.log("Registering PICO RooftopPV plugin");
    }

    show_sidebar(show_percentage_question, type) {
        sidebar.setContent(pico_rooftoppv_potential_plugin.create_sidebar_content(show_percentage_question, type).get(0));
        sidebar.show();
    }

    create_sidebar_content(show_percentage_question, type) {
        let all_text = '';
        let button_text = '';
        if (type == 'use') {
            all_text = 'Apply this percentage to all solar potentials';
            button_text = 'Use';
        } else {
            all_text = 'Query rooftop PV potential for all areas';
            button_text = 'Query';
        }

        let $div = $('<div>').attr('id', 'pico_rooftoppv_potential_main_div');
        let $title = $('<h1>').attr('id', 'pico_rooftoppv_potential_title').text('PICO rooftop PV potential');
        $div.append($title);

        let $content_div = $('<div>').attr('id', 'pico_rooftoppv_potential_content_div').addClass('sidebar-div');
        if (show_percentage_question) {
            let $intro = $('<p>').text('Please select the percentage of the Potential that you would like to convert to a installed PV Installation')
            $content_div.append($intro)

            let $input = $('<input>').attr('type', 'text').attr('width','20')
                            .attr('id', 'percentage_use_potential').attr('value','100');
            $content_div.append($input);
        }

        let $all_potentials = $('<input>').attr('type', 'checkbox').attr('id', 'all_potentials').attr('value', 'all_potentials').attr('name', 'all_potentials');
        let $ap_label = $('<label>').attr('for', 'all_potentials').text(all_text);
        $content_div.append($('<p>').append($all_potentials).append($ap_label));

        let $button = $('<button>').text(button_text);
        if (type == 'use')
            $button.click(function() { sidebar.hide(); pico_rooftoppv_potential_plugin.use_part_of_potential(); });
        else
            $button.click(function() { sidebar.hide(); pico_rooftoppv_potential_plugin.perform_query(); });

        $content_div.append($('<p>').append($button));

        $div.append($content_div);

        return $div;
    }

    use_part_of_potential() {
        let percentage = parseFloat($('#percentage_use_potential').val());
        let all_potentials = $('#all_potentials').prop('checked');
        if (this.potential_id != null) {
            socket.emit('use_part_of_potential', this.potential_id, percentage, all_potentials);
        } else {
            socket.emit('use_part_of_potential_area', this.area_id, percentage, all_potentials);
        }
    }

    choose_rooftop_pv_potential_usage(e, id, type) {
        if (type == 'potential') {
            this.potential_id = id;
            this.area_id = null;
        }
        if (type == 'area') {
            this.area_id = id;
            this.potential_id = null;
        }

        pico_rooftoppv_potential_plugin.show_sidebar(true, 'use');
    }

    query_rooftop_pv_potential(e, id) {
        this.area_id = id;
        this.potential_id = null;
        pico_rooftoppv_potential_plugin.show_sidebar(false, 'Query');
    }

    perform_query() {
        let all_potentials = $('#all_potentials').prop('checked');
        show_loader();
        socket.emit('query_solar_potentials', this.area_id, all_potentials, function(res) {
            hide_loader();
        });
    }

    static create(event) {
        if (event.type === 'client_connected') {
            pico_rooftoppv_potential_plugin = new PICO_RooftopPV();
            return pico_rooftoppv_potential_plugin;
        }
        if (event.type === 'add_contextmenu') {
            let layer = event.layer;
            let layer_type = event.layer_type;
            let id = layer.id;
            if (layer_type === 'marker' && layer.type === 'SolarPotential') {
                layer.options.contextmenuItems.push({
                    text: 'Use Rooftop PV Potential',
                    icon: resource_uri + 'icons/RooftopPV.png',
                    callback: function(e) {
                        pico_rooftoppv_potential_plugin.choose_rooftop_pv_potential_usage(e, id, 'potential');
                    }
                });
            }
           if (layer_type === 'area') {
                layer.options.contextmenuItems.push({
                    text: 'Query Rooftop PV Potential',
                    icon: resource_uri + 'icons/RooftopPV.png',
                    callback: function(e) {
                        pico_rooftoppv_potential_plugin.query_rooftop_pv_potential(e, id);
                    }
                });
                layer.options.contextmenuItems.push({
                    text: 'Use Rooftop PV Potential',
                    icon: resource_uri + 'icons/RooftopPV.png',
                    callback: function(e) {
                        pico_rooftoppv_potential_plugin.choose_rooftop_pv_potential_usage(e, id, 'area');
                    }
                });
           }

        }
    }
}

var pico_rooftoppv_potential_plugin;   // global variable for the PICO_RooftopPV plugin

$(document).ready(function() {
    extensions.push(function(event) { PICO_RooftopPV.create(event) });
});
