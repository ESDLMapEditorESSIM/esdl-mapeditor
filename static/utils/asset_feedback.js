/**
 *  This work is based on original code developed and copyrighted by TNO 2026.
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

function show_asset_feedback(active_layer_id, asset_feedback_dict) {
    // active_layer_id: active energy system ID
    // asset_feedback_dict: dictionary with asset IDs as key and list of feedback messages with severity as values
    let esdl_layer = get_layers(active_layer_id, 'esdl_layer');
    let esdl_objects = esdl_layer.getLayers();
    let sim_layer = get_layers(active_layer_id, 'sim_layer');

    for (let i = 0; i < esdl_objects.length; i++) {
        let object = esdl_objects[i];
        if (object.id in asset_feedback_dict) {
            let asset_feedback = asset_feedback_dict[object.id];

            let asset_severity = 'INFO';
            let asset_message = '<h1>Feedback</h1><ul>';
            asset_feedback.forEach(function (af, index) {
                if (asset_severity_order[af["severity"]] > asset_severity_order[asset_severity])
                    asset_severity = af["severity"]
                asset_message += '<li>' + af["severity"] + ': ' + af['validation_message'];

                if (af['check_result_messages']) {
                    asset_message += '<ul>';
                    for (let crm of af['check_result_messages']) {
                        asset_message += '<li>' + crm + '</li>';
                    }
                    asset_message += '</ul>';
                }
                asset_message += '</li>';
            });
            asset_message += '</ul>';

            if (object instanceof L.Marker) {
                let cur_location = object.getLatLng();

                let divicon = L.divIcon({
                    className: 'asset_feedback ' + asset_severity_class[asset_severity],
                    html: '',

                    iconSize: [40, 40], // size of the icon     // TODO: Resize on zoom level
                    iconAnchor: [22, 22], // point of the icon which will correspond to marker's location
                    popupAnchor: [0, -15] // point from which the popup should open relative to the iconAnchor
                });

                let marker = L.marker(cur_location, {icon: divicon, title: asset_message});
                marker.id = object.id;
                marker.title = asset_message;
                // marker.bindTooltip(asset_message);

                add_object_to_layer(active_layer_id, 'sim_layer', marker);
            }
            if (object instanceof L.Polyline) {
                let coords = object.getLatLngs();
                let line_color = asset_severity_color[asset_severity];
                let line = L.polyline(coords, {
                    color: line_color,
                    weight: 6,
                    draggable: false,
                    title: asset_message
                });
                line.id = object.id;
                line.title = asset_message;
                line.bindTooltip(asset_message);

                add_object_to_layer(active_layer_id, 'sim_layer', line);
            }
        }
    }

    $('.asset_feedback').tooltip({
        content: function () {
            return $(this).attr('title');
        }
    });

    // Show Vue asset feedback window
    asset_feedback_window(asset_feedback_dict);
}
