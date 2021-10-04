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

var SPATIAL_BUFFER_LAYER = 'kpi_layer';

class SpatialBuffers {
    constructor() {
        console.log("Registered Spatial buffers plugin");
    }

    add_popup_to_spatial_buffer(feature, layer, type) {
        let text = "Spatial impact ("+type+"): " + turf.area(feature).toFixed() + " m2";
        let popup = L.popup();
        popup.setContent(text);
        layer.bindPopup(popup);

        layer.on('mouseover', function (e) {
            var popup = e.target.getPopup();
            var this_map = e.sourceTarget._map;     // can be area map and building map
            popup.setLatLng(e.latlng).openOn(this_map);
        });

        layer.on('mouseout', function(e) {
            e.target.closePopup();
        });
    }

    get_spatial_buffer_layer() {
        return get_layers(active_layer_id, SPATIAL_BUFFER_LAYER)
    }

    create_buffer(layer, distance_meters, color, type) {
        let buffer_geojson = turf.buffer(layer.toGeoJSON(), distance_meters / 1000, {units: 'kilometers'});
        let buffer_layer = L.geoJson(buffer_geojson, {
            style: {color: color},
            onEachFeature: function(feature, layer) {
                spatial_buffers_plugin.add_popup_to_spatial_buffer(feature, layer, type);
            }
        });

        buffer_layer.addTo(this.get_spatial_buffer_layer());
        if (!('buffer_info' in layer))
            layer.buffer_info = [];
        layer.buffer_info.push({
            buffer: buffer_layer,
            distance_meters: distance_meters,
        });
    }

    show_spatial_buffers() {
        if ('spatial_buffers' in user_settings.ui_settings) {
            return user_settings.ui_settings.spatial_buffers.visible_on_startup;
        }
        return false;
    }

    add_spatial_buffers(layer) {
        if ('dist' in layer.attrs) {
            for (const [cat, distance] of Object.entries(layer.attrs.dist)) {
                if (distance > 0) {
                    this.create_buffer(layer, distance, user_settings.ui_settings.spatial_buffers.colors[cat], cat);
                }
            }
        }
    }

    remove_spatial_buffers(layer) {
        if (layer.buffer_info) {
            for (let i=0; i<layer.buffer_info.length; i++) {
                layer.buffer_info[i].buffer.remove();
            }
        }
    }

    redraw_spatial_buffers(layer) {
        this.remove_spatial_buffers(layer);
        this.add_spatial_buffers(layer);
    }

    update_buffer_distance_info(asset_id, attr_fragment, attr_name, attr_value) {
        if (!asset_id) { return; }
        let layer = find_layer_by_id(active_layer_id, 'esdl_layer', asset_id);

        if (!layer) { console.log("update_buffer_distance_info: can't find layer"); return; }

        if ('dist' in layer.attrs) {
            // changed existing, or added new item to existing list
            let buffer_distance_fragment = attr_fragment.match(/\/@bufferDistance.\d+/g)[0];
            let idx = parseInt(buffer_distance_fragment.split('.')[1]);
            let number_of_buffer_distance_attrs = Object.keys(layer.attrs['dist']).length;
            if (idx == number_of_buffer_distance_attrs) {
                // new item added
                if (attr_name == 'distance') { layer.attrs['dist']['UNDEFINED'] = attr_value; }
                if (attr_name == 'type') { layer.attrs['dist'][attr_value] = 0; }
            } else {
                // changed an existing one
                if (attr_name == 'distance') {
                    let key = Object.keys(layer.attrs['dist'])[idx];
                    layer.attrs['dist'][key] = parseInt(attr_value);
                }
                if (attr_name == 'type') {
                    console.log(layer.attrs['dist']);
                    let key = Object.keys(layer.attrs['dist'])[idx];
                    layer.attrs['dist'][attr_value] = layer.attrs['dist'][key];
                    delete layer.attrs['dist'][key];
                    console.log(layer.attrs['dist']);
                }
            }
        } else {
            // new buffer_distance attribute added
            let new_buffer_distance_object = {};
            if (attr_name == 'distance') { new_buffer_distance_object['UNDEFINED'] = parseInt(attr_value); }
            if (attr_name == 'type') { new_buffer_distance_object[attr_value] = 0; }
            layer.attrs['dist'] = new_buffer_distance_object;
        }
        this.redraw_spatial_buffers(layer);
    }

    show_hide_spatial_buffer_information(visible) {
        console.log(visible);
        for (let es_id in esdl_list) {
            let esdl_layer = get_layers(es_id, 'esdl_layer');

            if (visible) {
                let esdl_objs = esdl_layer.getLayers();
                for (let i=0; i<esdl_objs.length; i++) {
                    let esdl_obj = esdl_objs[i];
                    if (!((esdl_obj instanceof L.Marker) && ('polygon' in esdl_obj)))
                        this.add_spatial_buffers(esdl_obj);
                }
            } else {
                let esdl_objs = esdl_layer.getLayers();
                for (let i=0; i<esdl_objs.length; i++) {
                    if ('buffer_info' in esdl_objs[i]) {
                        this.remove_spatial_buffers(esdl_objs[i]);
                    }
                }
            }
        }
    }

    //find_overlapping_spatial_buffers(esdl_layer) {
    //}

    bring_spatial_buffers_to_back() {
        let esdl_layer = this.get_spatial_buffer_layer();
        esdl_layer.bringToBack();
    }
    
    UISettings() {
        let $div = $('<div>').addClass('ui_settings_div').append($('<h3>').text('Spatial buffer information'));

        let $visible_on_startup = $('<input>').attr('type', 'checkbox').attr('id', 'sb_visible').attr('value', 'sb_visible').attr('name', 'sb_visible');
        let $sbvis_label = $('<label>').attr('for', 'sb_visible').text('Spatial buffer information visible on startup');
        $div.append($('<p>').append($visible_on_startup).append($sbvis_label));

        $visible_on_startup.change(function() {
            let sb_visible = $('#sb_visible').is(':checked');
            spatial_buffers_plugin.show_hide_spatial_buffer_information(sb_visible);
            socket.emit('mapeditor_user_ui_setting_set', {
                category: 'spatial_buffers',
                name: 'visible_on_startup',
                value: sb_visible
            });
        });

        socket.emit('mapeditor_user_ui_setting_get', {category: 'spatial_buffers', name: 'visible_on_startup'}, function(res) {
            let sb_visible = res;
            $('#sb_visible').prop('checked', sb_visible);
        });

        return $div;
    }

    static create(event) {
        if (event.type === 'client_connected') {
            spatial_buffers_plugin = new SpatialBuffers();
            return spatial_buffers_plugin;
        }
        if (event.type === 'ui_settings_div') {
            return spatial_buffers_plugin.UISettings();
        }
    }
}

var spatial_buffers_plugin;   // global variable for the spatial buffers plugin

$(document).ready(function() {
    extensions.push(function(event) { return SpatialBuffers.create(event) });
});