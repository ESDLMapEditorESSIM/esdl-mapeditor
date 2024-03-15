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


function set_tooltip_position() {
    let size = Math.pow(map.getZoom()/8+1,3);
    $('#mapid .InteractiveTooltip').css({
        'margin-left':'0px',
        'margin-top':''+size/1.5+'px'
    });
}

function click_tooltip_button(e) {
    console.log(e);
}

function set_marker_tooltip_handlers(marker) {
    marker.on('mouseover', function(e) {
        marker.mouseover = true;

        if (!editing_objects && !deleting_objects) {

            let layer = e.target;
            let coords = layer._latlng;
            let leaflet_pos = layer._icon._leaflet_pos;

            if (!marker.tooltip) {
                let divicon = L.divIcon({
                    className: 'InteractiveTooltip',
                    iconSize: null,
                    html: '<div id="tooltip_contents_div">',
                });

                let tooltip_marker = L.marker([coords.lat, coords.lng], {icon: divicon, title: '', zIndexOffset: 1000});
                tooltip_marker.addTo(get_layers(active_layer_id, 'esdl_layer'));
                show_tooltip(marker.title, marker.id);

                tooltip_marker.parent = marker;
                tooltip_marker.parent_type = 'marker';
                tooltip_marker.active = false;
                marker.tooltip = tooltip_marker;

                tooltip_marker.on('mouseover', function (e) {
                    let tooltip = e.target;
                    tooltip.active = true;
                });
                tooltip_marker.on('mouseout', function (e) {
                    let tooltip = e.target;
                    tooltip.active = false;

                    setTimeout(function () {
                        // if after 300 ms, the tooltip is not re-activated and the mouse did not move back to the asset
                        if (tooltip.active === false && !tooltip.parent.mouseover) {
                            tooltip.removeFrom(get_layers(active_layer_id, 'esdl_layer'));
                            tooltip.parent.tooltip = undefined;
                            remove_tooltip();
                        }
                    }, 300);
                });

                set_tooltip_position();
            }
        }
    });

    marker.on('mouseout', function(e) {
        let layer = e.target;
        layer.mouseover = false;

        setTimeout(function() {
            if (layer.tooltip && layer.tooltip.active === false && !layer.mouseover) {
                layer.tooltip.removeFrom(get_layers(active_layer_id, 'esdl_layer'));
                layer.tooltip = undefined;
            }
        }, 300);
    });
}

function update_marker_tooltip(marker) {
    let ports = marker.ports;
    let coord = marker.getLatLng();

    for (let p in ports) { // ports is a dictionary: {'0': ...., '1': ...}
        let marker = ports[p].marker;
        if (marker !== undefined) {
            // update port marker location
            marker.setLatLng([coord.lat, coord.lng])
        }
    }
}

function handle_click_tooltip(tooltip_marker, e) {
    console.log('handle_click_tooltip');
}
