var esdl_list = {};         // Dictionairy to keep energysystem information
var active_layer_id = null;     // es_id of current layer that is being editted
var draw_control = null;
var bld_draw_control = null;
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
                { label: 'Simulation results', layer: es.layers['sim_layer'] }
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

    dc = new L.Control.Draw({
        edit: {
            featureGroup: get_layers(active_layer_id, 'esdl_layer'),
            poly: {
                allowIntersection: true
            }
        },
        draw: {
            polygon: {
                allowIntersection: true,
                showArea: true
            },
            circle: false,
            polyline: {
                repeatMode: true
            },
            marker: {
                icon: new WindTurbineMarker(),
                repeatMode: true
            }
        }
    })
    mp.addControl(dc);
    return dc;
}

// -----------------------------------------------------------------------------------------------------------
//  Functions related to the list of energysystem information
// -----------------------------------------------------------------------------------------------------------
function create_new_esdl_layer(es_id, title) {
    esdl_list_item = {
        id: es_id,
        title: title,
        layers: {
            esdl_layer: L.featureGroup().addTo(map),
            area_layer: L.featureGroup().addTo(map),
            bld_layer: L.featureGroup().addTo(map),
            pot_layer: L.featureGroup().addTo(map),
            connection_layer: L.featureGroup().addTo(map),
            sim_layer: L.featureGroup().addTo(map)
        },
        sector_list: null,
        carrier_list: null,
        area_bld_list: null
    };

    esdl_list[es_id] = esdl_list_item;
    active_layer_id = es_id;
    update_layer_control_tree();
}

function remove_esdl_layer(es_id) {
    esdl_list_item = esdl_list[es_id]
    for (let lyr in esdl_list_item.layers) {
        if (map.hasLayer(esdl_list_item.layers[lyr]))
            map.removeLayer(esdl_list_item.layers[lyr])
    }
    delete esdl_list[es_id];

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
            connection_layer: L.featureGroup().addTo(bld_map)
        },
        sector_list: null,
        carrier_list: null,
        area_bld_list: null
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

// Copied colors from building_type_colors in area_building_layer.js
// var conn_line_colors = ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928']
var conn_line_colors = ['#0000ff', '#ff0000', '#00ff00', '#800080', '#ffa500', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928']

function set_carrier_list(es_id, carrier_list) {
    esdl_list[es_id].carrier_list = carrier_list;

    carrier_info_mapping = {};
    carrier_info_mapping[0] = { color: '#808080', name: 'No carrier specified'}
    carrier_info_mapping[1] = { color: '#FF0000', name: 'Conflicting carriers specified'}

    for (i=0; i<carrier_list.length; i++) {
        carrier_info_mapping[carrier_list[i].id] = {
            color: conn_line_colors[i],
            name: carrier_list[i].name
        }
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
}

function set_area_bld_list(es_id, area_bld_list) {
    esdl_list[es_id].area_bld_list = area_bld_list;
}

function get_area_bld_list(es_id) {
    return esdl_list[es_id].area_bld_list;
}