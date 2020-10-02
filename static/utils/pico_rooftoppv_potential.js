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
        this.initSocketIO();
    }

    initSocketIO() {
        console.log("Registering PICO RooftopPV plugin");
    }

    show_sidebar() {
        sidebar.setContent(pico_rooftoppv_potential_plugin.create_sidebar_content().get(0));
        sidebar.show();
    }

    create_sidebar_content() {
        let $div = $('<div>').attr('id', 'pico_rooftoppv_potential_main_div');
        let $title = $('<h1>').attr('id', 'pico_rooftoppv_potential_title').text('PICO rooftop PV potential');
        $div.append($title);

        let $content_div = $('<div>').attr('id', 'pico_rooftoppv_potential_content_div').addClass('sidebar-div');
        let $intro = $('<p>').text('Please select the percentage of the Potential that you would like to convert to a installed PV Installation')
        $content_div.append($intro)

        let $input = $('<input>').attr('type', 'text').attr('width','20')
                        .attr('id', 'percentage_use_potential').attr('value','100');
        $content_div.append($input);

        let $button = $('<button>').text('Use');
        $button.click(function() { sidebar.hide(); pico_rooftoppv_potential_plugin.use_part_of_potential(); });
        $content_div.append($button);

        $div.append($content_div);

        return $div;
    }

    use_part_of_potential() {
        let percentage = parseFloat($('#percentage_use_potential').val());
        socket.emit('use_part_of_potential', this.potential_id, percentage);
    }

    choose_rooftop_pv_potential_usage(e, id) {
        this.potential_id = id;
        pico_rooftoppv_potential_plugin.show_sidebar();
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
                        pico_rooftoppv_potential_plugin.choose_rooftop_pv_potential_usage(e, id);
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
