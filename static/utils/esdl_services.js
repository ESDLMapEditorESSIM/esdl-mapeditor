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

var esdl_services_information;

function set_esdl_services_information(info) {
    esdl_services_information = info;

    update_service_contextmenus(info);
}

// function query_esdl_service(index) {
/**
 * Actually execute the querying of an ESDL service.
 * @param {*} service 
 * @param {*} state_params: The optional parameters the function should use to fill query p arameters with.
 */
function query_esdl_service(service, state_params) {
    let params = {};
    params['service_id'] = service['id'];

    if (service['type'] == 'geo_query') {
        params['area_scope'] = document.getElementById('area_scope').options[document.getElementById('area_scope').selectedIndex].value;
        //        params['area_id'] = document.getElementById('area_id').value;
        params['area_id'] = document.getElementById('area_list_select').options[document.getElementById('area_list_select').selectedIndex].value;
        if ("url_area_subscope" in service['geographical_scope']) {
            params['area_subscope'] = document.getElementById('area_subscope').options[document.getElementById('area_subscope').selectedIndex].value;
        }
    }

    params['query_parameters'] = {}
    let q_params = service['query_parameters'];
    for (let i = 0; i < q_params.length; i++) {
        let parameter_name = q_params[i]['parameter_name'];
        let ptype = '';
        if ('type' in q_params[i]) {
            ptype = q_params[i]['type'];
        }

        let parameter_value = undefined;
        if (ptype == 'constant' && 'value' in q_params[i]) {
            parameter_value = q_params[i]['value'];
        } else if (state_params != null) {
            if (parameter_name in state_params) {
                parameter_value = state_params[parameter_name];
            }
        } else {
            if (ptype == 'integer' || ptype == 'string') {
                parameter_value = document.getElementById(parameter_name + '_' + ptype).value;
            }
            else if (ptype == 'boolean') {
                parameter_value = document.getElementById(parameter_name + '_boolean').options[document.getElementById(parameter_name + '_boolean').selectedIndex].value;
            }
            else if (ptype == 'selection') {
                parameter_value = document.getElementById(parameter_name + '_select').options[document.getElementById(parameter_name + '_select').selectedIndex].value;
            }
            else if (ptype == 'multi-selection') {
                parameter_value = Array.from(document.getElementById(parameter_name + '_select').selectedOptions).map(option => option.value);
            }
        }
        params['query_parameters'][parameter_name] = parameter_value;
    }

    params['body_config'] = {}
    if (service['type'] == 'json') {
        let b_params = service['body_config'];
        if (b_params && Object.keys(b_params).length) {
            if (b_params['type'] == 'json') {
                for (let i=0; i<b_params['parameters'].length; i++) {
                    if (b_params['parameters'][i]['type'] == 'json_string') {
                        let parameter_name = b_params['parameters'][i]['parameter'];
                        let parameter_value = document.getElementById(parameter_name+'_textarea').value;
                        params['body_config'][parameter_name] = JSON.parse(parameter_value);
                    }
                }
            }
        }
    }

    // Only for services that are triggered from the sidebar, hide the query button
    // Using "type" is legacy, use location instead.
    if (
        service['type'] !== "map_context_menu" &&
        service['location'] !== "map_context_menu" &&
        service['type'] !== "area_context_menu" &&
        service['location'] !== "area_context_menu"
    ) {
        document.getElementById('query_service_button').style.display = 'none';
    }
    show_loader();
    console.log("query_esdl_service params", params);
    socket.emit('command', { cmd: 'query_esdl_service', params: params });

    // TODO: Determine when to close
    if (service['type'] == 'geo_query') {
        sidebar.hide();
    }
}

var asset_severity_order = {
  "INFO": 0,
  "WARNING": 1,
  "ERROR": 2,
};

var asset_severity_color = {
  "INFO": "#00FF00",
  "WARNING": "#FFA500",
  "ERROR": "#FF0000",
}

var asset_severity_class = {
  "INFO": "Info_marker",
  "WARNING": "Warning_marker",
  "ERROR": "Error_marker",
}

function process_service_results(results) {
    let service_results_div = document.getElementById('service_results_div');

    hide_loader();
    // TODO: Make this more generic

    if ('show_asset_results' in results) {
        let esdl_layer = get_layers(active_layer_id, 'esdl_layer');
        let esdl_objects = esdl_layer.getLayers();
        let sim_layer = get_layers(active_layer_id, 'sim_layer');

        var divicon = L.divIcon({
            className: 'Overload_marker',
            html: '',

            iconSize: [40, 40], // size of the icon
            iconAnchor: [22, 22], // point of the icon which will correspond to marker's location
            popupAnchor: [0, -15] // point from which the popup should open relative to the iconAnchor
        });

        for (let i = 0; i < esdl_objects.length; i++) {
            let object = esdl_objects[i];
            if (object.id in results['show_asset_results']['Transformer']) {
                let transformer_results = results['show_asset_results']['Transformer'][object.id];
                if (transformer_results['loading_percent'] > 100) {
                    let cur_location = object.getLatLng();

                    let marker = L.marker(cur_location, { icon: divicon, title: object.id });
                    marker.id = object.id;
                    marker.title = object.id;

                    add_object_to_layer(active_layer_id, 'sim_layer', marker);
                }
            }

            if (object.id in results['show_asset_results']['ElectricityCable']) {
                let cable_results = results['show_asset_results']['ElectricityCable'][object.id];
                if (cable_results['loading_percent'] > 100) {
                    let coords = object.getLatLngs();

                    let line = L.polyline(coords, { color: "#FF0000", weight: 6, draggable: false, title: object.id });
                    line.id = object.id;
                    line.title = object.id;

                    add_object_to_layer(active_layer_id, 'sim_layer', line);
                }
            }
        }
        sidebar.hide();
    }

    if ('asset_feedback' in results) {
        let esdl_layer = get_layers(active_layer_id, 'esdl_layer');
        let esdl_objects = esdl_layer.getLayers();
        let sim_layer = get_layers(active_layer_id, 'sim_layer');

        for (let i = 0; i < esdl_objects.length; i++) {
            let object = esdl_objects[i];
            if (object.id in results['asset_feedback']) {
                let asset_feedback = results['asset_feedback'][object.id];

                let asset_severity = 'INFO';
                let asset_message = '<h1>Feedback</h1><ul>';
                asset_feedback.forEach(function(af, index) {
                    if (asset_severity_order[af["severity"]] > asset_severity_order[asset_severity])
                        asset_severity = af["severity"]
                    asset_message += '<li>' + af["severity"] + ': ' + af['message'] + '</li>';
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

                    let marker = L.marker(cur_location, { icon: divicon, title: asset_message });
                    marker.id = object.id;
                    marker.title = asset_message;
                    // marker.bindTooltip(asset_message);

                    add_object_to_layer(active_layer_id, 'sim_layer', marker);
                }
                if (object instanceof L.Polyline) {
                    let coords = object.getLatLngs();
                    let line_color = asset_severity_color[asset_severity];
                    let line = L.polyline(coords, { color: line_color, weight: 6, draggable: false, title: asset_message });
                    line.id = object.id;
                    line.title = asset_message;
                    line.bindTooltip(asset_message);

                    add_object_to_layer(active_layer_id, 'sim_layer', line);
                }
            }
        }

        $('.asset_feedback').tooltip({
            content: function() {
                return $(this).attr('title');
            }
        });

        // Show Vue asset feedback window
        asset_feedback_window(results['asset_feedback']);
    }

    if ('show_url' in results) {
        let description = results['show_url']['description']
        let url = results['show_url']['url']
        let link_text = results['show_url']['link_text']
        service_results_div.innerHTML = description;
        service_results_div.innerHTML += '<a href="' + url + '" target="_blank">' + link_text + '</link>';
        service_results_div.innerHTML += '<p id="sidebar_action_button"><button type="button" class="btn btn-block btn-primary" onclick="sidebar.hide();">Close</button></p>';
        if ('response' in results['show_url']) {
            if ('errors' in results['show_url']['response']) {
                let table = '<table class="pure-table pure-table-striped">';
                table += '<thead><tr><th>Feedback from the ETM API</th></tr></thead>';
                for (let i=0; i<results['show_url']['response']['errors'].length; i++) {
                    table += '<tr><td>' + results['show_url']['response']['errors'][i] + '</td></tr>';
                }
                table += '</table>';
                service_results_div.innerHTML += '<p>' + table + '</p>';
            }
        }
    }
    if ('message' in results) {
        service_results_div.innerHTML += `<p>${results["message"]}</p>`;
        service_results_div.innerHTML += '<p id="sidebar_action_button"><button type="button" class="btn btn-block btn-primary" onclick="sidebar.hide();">Close</button></p>';
    }

    if (!('show_asset_results' in results) && !('asset_feedback' in results) &&
        !('show_url' in results) && !('message' in results)) {
        sidebar.hide();
    }
}

var area_list_mapping = {
    "COUNTRY": "countries",
    "PROVINCE": "provinces",
    "REGION": "regions",
    "MUNICIPALITY": "municipalities",
    "DISTRICT": "districts",
    "NEIGHBOURHOOD": "neighbourhoods"
}

function change_area_scope(select_element_id, area_type_select_id) {
    let area_scope_index = document.getElementById(area_type_select_id).selectedIndex;
    let area_scope_options = document.getElementById(area_type_select_id).options;
    let area_scope = area_scope_options[area_scope_index].text;
    show_area_list(select_element_id, area_scope, null, null);
}

function show_area_list(select_element_id, scope, filter_type, selected_filter) {
    let boundaries_url = "";
    let text_index = 0;
    let value_index = 0;
    if (filter_type != null) {
        boundaries_url = resource_uri + '/boundaries_names/' + area_list_mapping[filter_type.toUpperCase()] + '/'
            + selected_filter.toUpperCase() + '/' + area_list_mapping[scope.toUpperCase()];
        text_index = 3;
        value_index = 2;
    } else {
        boundaries_url = resource_uri + '/boundaries_names/' + area_list_mapping[scope.toUpperCase()];
        text_index = 1;
        value_index = 0;
    }

    $.ajax({
        url: boundaries_url,
        success: function (data) {
            let area_list = data["boundaries_names"];
            let sel_el = $('#' + select_element_id).get(0);

            if (sel_el.options) {
                let list_len = sel_el.options.length - 1;
                for (let i = list_len; i >= 0; i--) {
                    sel_el.remove(i);
                }
            }

            for (let i = 0; i < area_list.length; i++) {
                let option = document.createElement("option");
                option.text = area_list[i][text_index];
                option.value = area_list[i][value_index];
                sel_el.add(option);
            }
            sel_el.selectedIndex = 0;
            if (sel_el.onchange) {
                sel_el.onchange();
            }
        }
    });
}

/**
 * The entry point for using ESDL services.
 * 
 * @param {*} index The index of the active service in the esdl_config.py service list.
 * @param {*} state Optional initial state to pass to the workflow.
 */
function show_service_settings(index, state=null) {
    let service_settings_div = document.getElementById('service_settings_div');
    if (!service_settings_div) {
        // The sidebar is not rendered. This happens when starting services from the context menu.
        const sidebar_ctr = sidebar.getContainer();
        sidebar_ctr.innerHTML += '<div id="service_settings_div"></div>';
        sidebar.show();
        service_settings_div = document.getElementById('service_settings_div');
    }

    let service = esdl_services_information[index];
    service_settings_div.innerHTML = '<h1>' + service['name'] + '</h1>';
    service_settings_div.innerHTML += '<p>' + service['explanation'] + '</p>';

    if (service['type'] === 'vueworkflow' || service['type'] === 'workflow') {
        window.activate_service_workflow(index, service, state).then();
    } else {
        render_service(service, service_settings_div);
    }
}

/**
 * Render an actual service. Called from the workflow module, as well as for direct services.
 * @param {*} service 
 * @param {*} service_settings_div 
 */
function render_service(service, service_settings_div, workflow_state_params) {
    if (service['type'] == 'geo_query') {
        service_settings_div.innerHTML += '<h3>Geographical selection</h3>';

        let gs_info = service['geographical_scope'];
        let scopes = gs_info['area_scopes'];

        let table = '<table>';
        table += '<tr><td width=180>Scope</td><td><select id="area_scope" onchange="change_area_scope(\'area_list_select\', \'area_scope\');">';
        for (let i = 0; i < scopes.length; i++) {
            table += '<option value="' + scopes[i]['url_value'] + '">' + scopes[i]['scope'] + '</option>';
        }
        table += '</select></td></tr>';

        if ("url_area_subscope" in gs_info) {
            let subscopes = gs_info['area_subscopes'];
            table += '<table>';
            table += '<tr><td width=180>Sub scope</td><td><select id="area_subscope">';
            for (let i = 0; i < scopes.length; i++) {
                table += '<option value="' + subscopes[i]['url_value'] + '">' + subscopes[i]['scope'] + '</option>';
            }
            table += '</select></td></tr>';
        }
        //        table += '<tr><td width=180>Area id</td><td><input id="area_id" type="text"></input></td></tr>';
        table += '<tr><td width=180>Area select</td><td><select id="area_list_select"></select></td></tr>'
        table += '</table>';
        service_settings_div.innerHTML += table;

        show_area_list('area_list_select', scopes[0]['scope']);
        // document.getElementById('area_scope').onchange();  // force loading
    }

    if (service['show_query_params'] != false && (service['type'] == 'geo_query' || service['type'] == 'simulation' || service['type'].startsWith('send_esdl') || service['type'] == 'json')) {
        let q_params = service['query_parameters'];

        if (q_params.length > 0) {
            service_settings_div.innerHTML += '<h3>Service query parameters</h3>';

            let table = '<table>';
            for (let i = 0; i < q_params.length; i++) {
                table += '<tr><td width=180>' + q_params[i]['name'] + '</td><td>';

                let ptype = q_params[i]['type'];
                if (ptype == 'integer' || ptype == 'string') {
                    let default_value = "";
                    if ('default' in q_params[i]) {
                        default_value = q_params[i]['default'];
                    }
                    table += '<input id="' + q_params[i]['parameter_name'] + '_' + ptype + '" type="text" value="'+default_value+'"></input>';
                }
                else if (ptype == 'boolean') {
                    table += '<select id="' + q_params[i]['parameter_name'] + '_boolean"><option value="true">TRUE</value><option value="false">FALSE</value></select>';
                }
                else if (ptype == 'selection' || ptype == 'multi-selection') {
                    table += '<select id="' + q_params[i]['parameter_name'] + '_select"';
                    if (ptype == 'multi-selection') {
                        table += ' multiple';
                    }
                    table += '>';
                    let pos_values = q_params[i]['possible_values'];
                    for (let j = 0; j < pos_values.length; j++) {
                        table += '<option value="' + pos_values[j] + '">' + pos_values[j] + '</option>';
                    }
                    table += '</select>';
                }
                table += '</td></tr>';
                // table += '<option value="'++'">'++'</option>';
            }

            table += '</table>';
            service_settings_div.innerHTML += table;
        }
    }

    let first_body_ui_parameter = true;
    if (service['type'] == 'json') {
        let b_params = service['body_config'];
        if (b_params && Object.keys(b_params).length) {
            if (b_params['type'] == 'json') {
                for (let i=0; i<b_params['parameters'].length; i++) {
                    if (b_params['parameters'][i]['type'] == 'json_string') {
                        if (first_body_ui_parameter) {
                            service_settings_div.innerHTML += '<p><h3>Service body parameters</h3>';
                            service_settings_div.innerHTML += '<table>';
                            first_body_ui_parameter = false;
                        }

                        let table_rows = '<tr><td>'+b_params['parameters'][i]['name']+'</td></tr>';
                        table_rows += '<tr><td><textarea id="'+b_params['parameters'][i]['parameter']+'_textarea" style="width:100%; height:200px;">';
                        table_rows += JSON.stringify(b_params['parameters'][i]['default'], null, 4);
                        table_rows += '</textarea></td></tr>';

                        service_settings_div.innerHTML += table_rows;
                    }
                }
                if (!first_body_ui_parameter) {
                    service_settings_div.innerHTML += '</table></p>';
                }
            }
        }
    }

    // Add the workflow state params if requested.
    let params = service['state_params'] ? workflow_state_params : null;

    service_settings_div.innerHTML += '<p id="sidebar_action_button"><button id="query_service_button" type="button" class="btn btn-block btn-primary">Run Service</button>';
    // We need to wait a second before the stuff is rendered.
    setTimeout(() => {
        $(`button#query_service_button`).click(() => {
            query_esdl_service(service, params);
        });
    }, 1000);
}

function esdl_services_info() {
    let sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>ESDL services:</h1>';

    if (esdl_services_information) {
        let table = '<table>';
        for (let i = 0; i < esdl_services_information.length; i++) {
            // id, name
            // Using type for this is legacy. We now use location instead.
            if (esdl_services_information[i]['type'] !== "map_context_menu" &&
                esdl_services_information[i]['location'] !== "map_context_menu" &&
                esdl_services_information[i]['type'] !== "area_context_menu" &&
                esdl_services_information[i]['location'] !== "area_context_menu"
            ) {
                table += '<tr><td><button onclick="show_service_settings(' + i + ');">Open</button></td><td>' + esdl_services_information[i]['name'] + '</td></tr>';
            }
        }
        table += '</table>';
        sidebar_ctr.innerHTML += table;
    } else {
        sidebar_ctr.innerHTML += 'No external ESDL services defined yet';
    }

    sidebar_ctr.innerHTML += '<hr>';

    sidebar_ctr.innerHTML += '<div id="service_settings_div"></div>';
    sidebar_ctr.innerHTML += '<div id="service_results_div"></div>';

    sidebar.show();
}

function show_esdl_service_sidebar(id) {
    for (let i=0; i<esdl_services_information.length; i++) {
        if (esdl_services_information[i].id == id) {
            let sidebar_ctr = sidebar.getContainer();
            sidebar_ctr.innerHTML = '<div id="service_settings_div"></div>'
            show_service_settings(i);
            sidebar.show();
        }
    }
}

/**
 * Render when an error has occurred in one of the services.
 * 
 * @param {*} service_index 
 */
function service_render_error(service_index, text = null) {
    if (text === null) {
        text = 'An error has occurred executing this service';
    }
    return `
        <div>
            <p class="text-danger">${text}</p>
            <button class="btn btn-warning" onclick="show_service_settings(${service_index})">
                Start over
            </button>
        </div>
    `;
}

function update_service_contextmenus(services_list) {
    // For now, remove all contextmenu items
    map.contextmenu.removeAllItems();
    for (let i = 0; i < services_list.length; i++) {
        if (services_list[i]['type'] == "map_context_menu" || services_list[i]['location'] == "map_context_menu") {
            map.contextmenu.addItem({
                text: services_list[i]['name'],
                icon: resource_uri + 'icons/service.png',
                callback: function(e) {
                    const service = services_list[i];
                    const state = {
                        lat: e.latlng.lat.toString(),
                        lng: e.latlng.lng.toString(),
                    };
                    if (service['type'] === 'vueworkflow' || service['type'] === 'workflow') {
                        window.show_service_settings(i, state);
                    } else {
                        query_esdl_service(service, state);
                    }
                }
            });
        }
    }
}

function update_esdl_services(event) {
    if (event.type === 'add_contextmenu') {
        let layer = event.layer;
        let id = layer.id;

        if (event.layer_type === 'area') {
            for (let i = 0; i < esdl_services_information.length; i++) {
                if (esdl_services_information[i]['type'] == "area_context_menu" || esdl_services_information[i]['location'] == "area_context_menu") {
                    // if (esdl_services_information[i]['area_scope'] == layer.scope) {
                        layer.options.contextmenuItems.push({
                            text: esdl_services_information[i]['name'],
                            icon: resource_uri + 'icons/service.png',
                            callback: function (e) {
                                const service = esdl_services_information[i];
                                const state = {
                                    area_id: id,
                                }
                                if (service['type'] === 'vueworkflow' || service['type'] === 'workflow') {
                                    window.show_service_settings(i, state);
                                } else {
                                    query_esdl_service(service, state);
                                }
                            }
                        });
                    // }
                }
            }
        }

        if (event.layer_type === 'marker') {
            for (let i = 0; i < esdl_services_information.length; i++) {
                if (esdl_services_information[i]['type'] == "asset_context_menu" || esdl_services_information[i]['location'] == "asset_context_menu") {
                    layer.options.contextmenuItems.push({
                        text: esdl_services_information[i]['name'],
                        icon: resource_uri + 'icons/service.png',
                        callback: function (e) {
                            const service = esdl_services_information[i];
                            const state = {
                                asset_id: id,
                            }
                            if ("options" in service && "send_esdl" in service["options"] && service["options"]["send_esdl"]) {
                                $.ajax({
                                    url: '/get_object_esdl/' + id,
                                    success: function (data) {
                                        console.log(data);
                                        state['esdl'] = data['esdl'];
                                        if (service['type'] === 'vueworkflow' || service['type'] === 'workflow') {
                                            window.show_service_settings(i, state);
                                        } else {
                                            query_esdl_service(service, state);
                                        }
                                    }
                                })
                            } else {
                                if (service['type'] === 'vueworkflow' || service['type'] === 'workflow') {
                                    window.show_service_settings(i, state);
                                } else {
                                    query_esdl_service(service, state);
                                }
                            }
                        }
                    });
                }
            }
        }
    }
}

$(document).ready(function() {
    extensions.push(update_esdl_services)
});