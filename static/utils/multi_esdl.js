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

var esdl_list = {};         // Dictionairy to keep energysystem information
var active_layer_id = null;     // es_id of current layer that is being editted
var draw_control = null;
var draw_control_map = {};
var select_esdl_control = null;

// -----------------------------------------------------------------------------------------------------------
//  Update the overlays in the Layer Control Tree
// -----------------------------------------------------------------------------------------------------------
function update_layer_control_tree() {
    let esdl_layers = [];
    for (let id in esdl_list) {
        es = esdl_list[id]
        child = {
            label: es.title,
            children: [
                { label: 'Area', layer: es.layers['area_layer'] },
                { label: 'Assets', layer: es.layers['esdl_layer'] },
                { label: 'Connections', layer: es.layers['connection_layer'] },
                { label: 'Buildings', layer: es.layers['bld_layer'] },
                { label: 'Potentials', layer: es.layers['pot_layer'] },
                { label: 'KPIs', layer: es.layers['kpi_layer'] },
                { label: 'Simulation results', layer: es.layers['sim_layer'] },
                { label: 'Notes', layer: es.layers['notes_layer'] }
            ]
        };
        esdl_layers.push(child)
    }

    let overlaysTree = {
        label: 'ESDL',
        children: esdl_layers
    }

    layer_ctrl_tree.setOverlayTree(overlaysTree);
}

function select_active_layer_old() {
    let active_esdl_layer_index = document.getElementById('esdl_layer_select').selectedIndex;
    let active_esdl_layer_options = document.getElementById('esdl_layer_select').options;
    let active_esdl_layer = active_esdl_layer_options[active_esdl_layer_index].id;
    select_active_layer(active_esdl_layer);
}

function select_active_layer(active_esdl_layer) {
    active_layer_id = active_esdl_layer;
    socket.emit('set_active_es_id', active_layer_id);
    draw_control = add_draw_control(draw_control, map);         // connect draw control to new active layer
    update_area_bld_list_select();
    update_title(esdl_list[active_layer_id].title);
    let bounds = get_layers(active_layer_id, 'esdl_layer').getBounds();
    if (Object.keys(bounds).length !== 0)
        map.flyToBounds(bounds, {padding: [50,50], animate: true});     // zoom to layer
}

function add_select_esdl() {
    if (select_esdl_control) {
        map.removeControl(select_esdl_control);
    }

    select_esdl_control = L.control({position: 'topright'});
    select_esdl_control.onAdd = function (map) {
        var div = L.DomUtil.create('div', 'info legend');

        var select = '<select id="esdl_layer_select" onchange="select_active_layer_old();">';
        for (let id in esdl_list) {
            es = esdl_list[id]
            select += '<option id="'+es.id+'"';
            if (es.id == active_layer_id) { select += ' selected'; }
            select += '>'+es.title+'</option>';
        }
        select += '</select>';
        div.innerHTML += select;
        div.firstChild.onmousedown = div.firstChild.ondblclick = L.DomEvent.stopPropagation;
        return div;
    };
    select_esdl_control.addTo(map);
}


function add_draw_control(dc, mp) {
    if (dc) {
        mp.removeControl(dc);
    }

    L.drawLocal.draw.toolbar.buttons.polygon = 'Draw an area or asset as a polygon';
    L.drawLocal.draw.toolbar.buttons.polyline = 'Draw a cable or a pipe';
    L.drawLocal.draw.toolbar.buttons.marker = 'Draw the asset that is selected in the menu as a marker';


    dc = new L.Control.Draw({
        edit: {
            featureGroup: get_layers(active_layer_id, 'esdl_layer'),
            poly: {
                allowIntersection: true
            },
            edit: {
                movable: true
            }
        },
        draw: {
            polygon: {
                allowIntersection: false,
                showArea: true,
                showLength: true,
                zIndexOffset: -2000 // for drawing polygons correctly with adapted polyline
            },
            circle: false,
            circlemarker: false,
            polyline: {
                repeatMode: true,
                zIndexOffset: -2000, // for drawing using the port handlers
                touchIcon: new L.DivIcon({ // create smaller touch icon
			        iconSize: new L.Point(12, 12),
		        	className: 'leaflet-div-icon leaflet-editing-icon leaflet-touch-icon'
		        })
            },
            marker: {
                icon: new WindTurbineMarker(),
                repeatMode: true
            }
        }
    })
    mp.addControl(dc);
    draw_control_map[mp.getContainer().id] = dc;
    return dc;
}

// return the draw_control beloning to this map
function get_active_draw_control(map) {
    return draw_control_map[map.getContainer().id];
}

// -----------------------------------------------------------------------------------------------------------
//  Functions related to the list of energysystem information
// -----------------------------------------------------------------------------------------------------------
function create_new_esdl_layer(es_id, title) {
    if (es_id in esdl_list) {
        console.log('es_id exists, first remove it');
        remove_esdl_layer_from_ui(es_id);
    }

    esdl_list_item = {
        id: es_id,
        title: title,
        layers: {
            esdl_layer: L.featureGroup().addTo(map),
            area_layer: L.featureGroup().addTo(map),
            bld_layer: L.featureGroup().addTo(map),
            pot_layer: L.featureGroup().addTo(map),
            connection_layer: L.featureGroup().addTo(map),
            kpi_layer: L.featureGroup().addTo(map),
            sim_layer: L.featureGroup().addTo(map),
            notes_layer: L.featureGroup().addTo(map)
        },
        sector_list: null,
        carrier_list: null,
        area_bld_list: null,
        kpi_info: null
    };

    esdl_list[es_id] = esdl_list_item;
    active_layer_id = es_id;
    // update_layer_control_tree();
}

function remove_esdl_layer_from_ui(es_id) {
    esdl_list_item = esdl_list[es_id]
    for (let lyr in esdl_list_item.layers) {
        if (map.hasLayer(esdl_list_item.layers[lyr]))
            map.removeLayer(esdl_list_item.layers[lyr])
    }
    delete esdl_list[es_id];
}

function remove_esdl_layer(es_id) {
    remove_esdl_layer_from_ui(es_id);
    socket.emit('command', {cmd: 'remove_energysystem', remove_es_id: es_id});
}

function rename_esdl_energy_system(es_id, name) {
    esdl_list[es_id].title = name
    socket.emit('command', {cmd: 'rename_energysystem', remame_es_id: es_id, name: name});
    if (es_id === active_layer_id) {
        update_title(name);
    }
}

function create_new_bld_layer(bld_id, title, bld_map) {
    esdl_list_item = {
        id: bld_id,
        title: title,
        layers: {
            esdl_layer: L.featureGroup().addTo(bld_map),
            bld_layer: L.featureGroup().addTo(bld_map),
            pot_layer: L.featureGroup().addTo(bld_map),
            connection_layer: L.featureGroup().addTo(bld_map),
            notes_layer: L.featureGroup().addTo(bld_map)
        },
        sector_list: null,
        carrier_list: null,
        area_bld_list: null,
        kpi_info: null
    };

    esdl_list[bld_id] = esdl_list_item;
}


function remove_bld_layer(bld_id) {
    delete esdl_list[bld_id];
}

function show_esdl_layer_on_map(es_id, layer_name) {
    if (!map.hasLayer(esdl_list[es_id].layers[layer_name]))
        esdl_list[es_id].layers[layer_name].addTo(map);
}

function hide_esdl_layer_from_map(es_id, layer_name) {
    if (map.hasLayer(esdl_list[es_id].layers[layer_name]))
        esdl_list[es_id].layers[layer_name].removeFrom(map);
}

function clear_esdl_layer_list() {
    for (let id in esdl_list) {
        for (let l in esdl_list[id].layers) {
            esdl_list[id].layers[l].removeFrom(map);
        }
    }
    esdl_list = {};
}

function add_object_to_layer(es_id, layer_name, object) {
    esdl_list[es_id].layers[layer_name].addLayer(object);
}

function remove_object_from_layer(es_id, layer_name, object) {
    esdl_list[es_id].layers[layer_name].removeLayer(object);
}

function get_layers(es_id, layer_name) {
    return esdl_list[es_id].layers[layer_name];
}

function find_layer_by_id(es_id, layer_name, id) {
    let layer_list = esdl_list[es_id].layers[layer_name].getLayers();
    for (let i=0; i<layer_list.length; i++) {
        let layer = layer_list[i];
        if (layer instanceof L.GeoJSON) {     // building layer
          let geojson_layer_list = Object.entries(layer._layers);   // _layers is an Object with ids as keys
          for (let j=0; j<geojson_layer_list.length; j++) {
            let geojson_layer = geojson_layer_list[j];
            if (geojson_layer[1].feature.properties.id == id) {
              return geojson_layer;
            }
          }
        } else if (layer.id == id) {
            return layer;
        }
    }
}

function clear_layers(es_id, layer_name) {
    if (es_id != null) {
        esdl_list[es_id].layers[layer_name].clearLayers();
    }
}

function set_sector_list(es_id, sector_list) {
    esdl_list[es_id].sector_list = sector_list;
}

function get_sector_list(es_id) {
    return esdl_list[es_id].sector_list;
}

function get_carrier_style_class_name(carrier_mapping) {
    return 'car_' + carrier_mapping.name.replace(/[^a-z]/ig, ''); // only a-z in class name, no spaces
}

/**
Creates a dynamic class based on a carrier color that can be added to ports
*/
function update_carrier_style_class(carrier_mapping) {
    let carrier_class_name = carrier_mapping.name;
    carrier_class_name = get_carrier_style_class_name(carrier_mapping);
    let carrier_color = carrier_mapping.color;
    // dynamically create a style we can add to the marker
    if ( $("head").children("#"+carrier_class_name).length === 0) {
        // add only when class is not defined
        let style = $("<style id="+carrier_class_name+" type='text/css'> ."+carrier_class_name+" { background: "+carrier_color+";} </style>");
        style.appendTo("head"); // add to <head> element
    } else {
        $("head").children("#"+carrier_class_name).text('.'+carrier_class_name+' { background: '+carrier_color+';}');
    }
}

// Copied colors from building_type_colors in area_building_layer.js
// var conn_line_colors = ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928']
var conn_line_colors = ['#ff0000', '#0000ff', '#00ff00', '#800080', '#ffa500', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928']

function set_carrier_list(es_id, carrier_list) {
    esdl_list[es_id].carrier_list = carrier_list;

    carrier_info_mapping = {};
    carrier_info_mapping[0] = { color: '#808080', name: 'No carrier specified'}
    carrier_info_mapping[1] = { color: '#FF0000', name: 'Conflicting carriers specified'}

    for (i=0; i<carrier_list.length; i++) {
        let color = conn_line_colors[i % conn_line_colors.length]; // default color if no color stored

        if (carrier_color_dict) {
            if (es_id + carrier_list[i]['id'] in carrier_color_dict) {
                color = carrier_color_dict[es_id + carrier_list[i]['id']]['color'];
                console.log('found '+color+' in color_dict');
            }
        }
        carrier_info_mapping[carrier_list[i].id] = {
            color: color,
            name: carrier_list[i].name
        }
        update_carrier_style_class(carrier_info_mapping[carrier_list[i].id]);
    }
    esdl_list[es_id].carrier_info_mapping = carrier_info_mapping;
}

function get_carrier_list(es_id) {
    return esdl_list[es_id].carrier_list;
}

function get_carrier_info_mapping(es_id) {
    return esdl_list[es_id].carrier_info_mapping;
}

function set_carrier_color(es_id, carrier_id, color) {
    esdl_list[es_id].carrier_info_mapping[carrier_id]['color'] = color
    update_color_in_carrier_color_dict(es_id, carrier_id, color);
    update_carrier_style_class(esdl_list[es_id].carrier_info_mapping[carrier_id]);
}

function set_area_bld_list(es_id, area_bld_list) {
    esdl_list[es_id].area_bld_list = area_bld_list;
}

function get_area_bld_list(es_id) {
    return esdl_list[es_id].area_bld_list;
}

function set_kpi_info(es_id, kpi_info) {
    esdl_list[es_id].kpi_info = kpi_info;
}

function get_kpi_info(es_id) {
    return esdl_list[es_id].kpi_info;
}

function get_all_kpi_info() {
    kpi_info = {};
    for (let es_id in esdl_list) {
        kpi_es = esdl_list[es_id].kpi_info;
        if (kpi_es) {
            kpi_info[es_id] = kpi_es;
        }
    }
    return kpi_info;
}