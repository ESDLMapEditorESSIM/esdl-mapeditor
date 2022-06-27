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


// ------------------------------------------------------------------------------------------------------------
//  Splitting conductors (cables or pipes)
// ------------------------------------------------------------------------------------------------------------
function emit_split_conductor(id, location, mode) {
    socket.emit('command', {cmd: 'split_conductor', id: id, location: location, mode: mode});
}

function split_conductor(e, id) {
    emit_split_conductor(id, e.latlng, 'no_connect');
    // only remove conductor from UI, let server side remove conductor in ESDL
    clear_layer = true;
    //esdl_layer.removeLayer(e.relatedTarget);
    remove_object_from_layer(active_layer_id, 'esdl_layer', e.relatedTarget);
    clear_layer = false;
}

function split_conductor_connect(e, id) {
    emit_split_conductor(id, e.latlng, 'connect');
    // only remove conductor from UI, let server side remove conductor in ESDL
    clear_layer = true;
    //esdl_layer.removeLayer(e.relatedTarget);
    remove_object_from_layer(active_layer_id, 'esdl_layer', e.relatedTarget);
    clear_layer = false;
}

function split_conductor_add_joint(e, id) {
    emit_split_conductor(id, e.latlng, 'add_joint');
    // only remove conductor from UI, let server side remove conductor in ESDL
    clear_layer = true;
    //esdl_layer.removeLayer(e.relatedTarget);
    remove_object_from_layer(active_layer_id, 'esdl_layer', e.relatedTarget);
    clear_layer = false;
}

// ------------------------------------------------------------------------------------------------------------
//  Asset port operations
// ------------------------------------------------------------------------------------------------------------
function add_port(direction, asset_id) {
    // get name
    pname = document.getElementById('name_add_port').value;
    socket.emit('command', {cmd: 'add_port', direction: direction, asset_id: asset_id, pname: pname});
}

function remove_port(pid) {
    socket.emit('command', {cmd: 'remove_port', port_id: pid});
}

function set_port_profile(e, marker_id, port_id) {
    // console.log('setPortProfile(marker_id=' + marker_id + ', port_id=' + port_id + ')');
    socket.emit('command', {'cmd': 'get_port_profile_info', 'port_id': port_id});
}

// ------------------------------------------------------------------------------------------------------------
//  Change asset attribute
// ------------------------------------------------------------------------------------------------------------
function change_param(obj) {
    let asset_id = $(obj).attr('assetid');
    let asset_fragment = $(obj).attr('fragment'); // in case there is no id present
    let asset_param_name = obj.name;
    let asset_param_value = obj.value;

    socket.emit('command', {cmd: 'set_asset_param', id: asset_id, fragment: asset_fragment, param_name: asset_param_name, param_value: asset_param_value});

    let object_type = $(obj).attr('object_type'); // also use asset type
    let parent_asset_id = $(obj).attr('parent_asset_id');   // in case an asset reference is being edited
    window.PubSubManager.broadcast('ASSET_PROPERTIES', { id: asset_id, object_type: object_type, parent_asset_id: parent_asset_id, fragment: asset_fragment, name: asset_param_name, value: asset_param_value });
}

// ------------------------------------------------------------------------------------------------------------
//  Add and remove connection
// ------------------------------------------------------------------------------------------------------------
function connect_asset(feature_id, port_id) {
    // console.log('connect_asset(feature_id=' + feature_id + ', port_id=' + port_id + ')');
    if (bld_edit_id) {
        console.log('Asset in building');
    }
    if (connect_ports != null) {
        socket.emit('command', {'cmd': 'connect_ports', port1id: connect_ports, port2id: port_id});
        connect_ports = null;
    } else {
        connect_ports = port_id;
    }
}

function remove_connection(from_asset_id, from_port_id, to_asset_id, to_port_id) {
    socket.emit('command', {cmd: 'remove_connection', from_asset_id:from_asset_id, from_port_id:from_port_id, to_asset_id:to_asset_id, to_port_id:to_port_id});
}

function remove_single_connection(from_id, to_id, es_id) {
    let id = from_id + to_id;
    let conn = find_layer_by_id(es_id, 'connection_layer', id);
    if (conn !== undefined) {
        remove_object_from_layer(es_id, 'connection_layer', conn);
    }
    // also remove connection if connected from the other side
    let id2 = to_id + from_id;
    conn = find_layer_by_id(es_id, 'connection_layer', id2);
    if (conn !== undefined) {
        remove_object_from_layer(es_id, 'connection_layer', conn);
    }
}

// ------------------------------------------------------------------------------------------------------------
//  Deletes a building (Marker or Polygon) and its connections
// ------------------------------------------------------------------------------------------------------------
function remove_building_from_building_layer(bld) {
    let asset = find_layer_by_id(active_layer_id, 'bld_layer', bld.id);

    let geojson_layers = get_layers(active_layer_id, 'bld_layer').getLayers();
    for (let i=0; i<geojson_layers.length; i++) {
      if (geojson_layers[i] instanceof L.FeatureGroup) {
        let bld_layers = geojson_layers[i].getLayers();
        for (let j=0; j<bld_layers.length; j++) {
          if (bld_layers[j].feature.properties.id == bld.id) {
            geojson_layers[i].removeLayer(bld_layers[j]);
            return;
          }
        }
      }
    }

}

function remove_building(bld) {
    socket.emit('command', {cmd: 'get_building_connections', id: bld.id}, function(conn_list) {
      if (conn_list) {
        for (let i=0; i<conn_list.length; i++) {
          remove_single_connection(conn_list[i]["from_id"], conn_list[i]["to_id"], active_layer_id);
        }
      }

      remove_building_from_building_layer(bld);     // remove geojson polygon from building layer
      delete_asset(bld);
    });
}

// ------------------------------------------------------------------------------------------------------------
//  Deletes an asset (Marker, Polyline or Polygon) and its connections
// ------------------------------------------------------------------------------------------------------------
function delete_asset(clicked_asset) {
    $(".ui-tooltip-content").parents('div').remove();

    let asset_list = [clicked_asset.id];
    if (select_assets.is_select_mode()) {
        // One or more assets have been selected
        if (select_assets.is_selected(clicked_asset)) {
            // the current asset is part of this selection
            asset_list = select_assets.get_selected_assets();
        }
    }

    // asset_list now contains a list of all IDs of the selected assets
    all_layers = get_layers(active_layer_id, 'esdl_layer').getLayers();
    for (let idx=0; idx<asset_list.length; idx++) {
        asset_id = asset_list[idx];
        let asset = find_layer_by_id(active_layer_id, 'esdl_layer', asset_id);

        if (asset instanceof L.Polygon) {
            // Remove maker that belongs to polygon
            if (asset.marker) {
                remove_object_from_layer(active_layer_id, 'esdl_layer', asset.marker)
            }
        } else if (asset instanceof L.Polyline) {
            if (asset.mouseOverArrowHead !== undefined) {
                remove_object_from_layer(es_bld_id, 'connection_layer', asset.mouseOverArrowHead);
                delete asset.mouseOverArrowHead;
            }

            if (asset.selectline) {  // remove highlight if selected
                remove_object_from_layer(es_bld_id, 'esdl_layer', asset.selectline);
                delete asset.selectline;
            }
        }

        // remove connections manually
        for (let i in asset.ports) {
            let from_id = asset.ports[i].id;
            for (let j in asset.ports[i].conn_to) {
                remove_single_connection(from_id, asset.ports[i].conn_to[j], asset.esid)
            }
        }

        // remove the asset itself
        remove_object_from_layer(asset.esid, 'esdl_layer', asset);
        socket.emit('command', {cmd: 'remove_object', id: asset.id, asspot: asset.asspot});
    }
    if (select_assets.is_select_mode()) {
        select_assets.deselect_all_assets();
    }
}

// ------------------------------------------------------------------------------------------------------------
//  Handlers for clicking on an asset or potential
// ------------------------------------------------------------------------------------------------------------
function set_marker_handlers(marker) {
    let asset_id = marker.id;

    marker.bindContextMenu({
        contextmenu: true,
        contextmenuWidth: 140,
        contextmenuItems: [],
        contextmenuInheritItems: false
    });

    if (marker.ports) {
        if (marker.ports.length > 0) {
            // for (let p=0; p<marker.ports.length; p++) {
            //    let port_id = ''+marker.ports[p].id;
            //    let port_id_in_menu = '';
            //    if (marker.ports[p].name === undefined || marker.ports[p].name === "") {
            //            port_id_in_menu = ' (' + port_id + ')'
            //    }
            //    marker.options.contextmenuItems.push({
            //        icon: 'icons/Connect.png',
            //        text: 'Connect ' + marker.ports[p].type + port_id_in_menu + ': ' + marker.ports[p].name,
            //        callback: function(e) { connect_asset(asset_id, port_id); }
            //    });
            // }
            // marker.options.contextmenuItems.push('-');

            for (let p=0; p<marker.ports.length; p++) {
                let port_id = marker.ports[p].id;
                let port_id_in_menu = '';
                if (marker.ports[p].name === undefined || marker.ports[p].name === "") {
                        port_id_in_menu = ' (' + port_id + ')'
                }
                marker.options.contextmenuItems.push({
                    icon: 'icons/Graph.png',
                    text: 'Set profile of ' + marker.ports[p].type + port_id_in_menu + ': ' + marker.ports[p].name,
                    callback: function(e) { set_port_profile(e, asset_id, port_id); }
                });
            }

            marker.options.contextmenuItems.push('-');
            marker.options.contextmenuItems.push({
                text: 'Set carrier',
                icon: 'icons/SetCarrier.png',
                callback: function(e) {
                    select_carrier_menu(asset_id);
                }
            });
            marker.options.contextmenuItems.push({
                text: 'Set Control Strategy',
                icon: 'icons/Control.png',
                callback: function(e) {
                    control_strategy_window(asset_id);
                }
            });

            if (marker.capability == 'Conversion') {
                marker.options.contextmenuItems.push('-');
                for (p=0; p<marker.ports.length; p++) {
                    let port_id = marker.ports[p].id
                    let port_id_in_menu = '';
                    if (marker.ports[p].name === undefined || marker.ports[p].name === "") {
                            port_id_in_menu = ' (' + port_id + ')'
                    }
                    if (marker.ports[p].type == 'OutPort') {
                        menu_item_txt = 'Set DrivenByDemand for: ' + marker.ports[p].type + port_id_in_menu + ': ' + marker.ports[p].name;
                        callback_function = function(e) {
                            set_driven_by_demand(asset_id, port_id);
                        }
                    } else {
                        menu_item_txt = 'Set DrivenBySupply for: ' + marker.ports[p].type + port_id_in_menu + ': ' + marker.ports[p].name;
                        callback_function = function(e) {
                            set_driven_by_supply(asset_id, port_id);
                        }
                    }

                    marker.options.contextmenuItems.push({
                        icon: 'icons/Graph.png',
                        text: menu_item_txt,
                        callback: callback_function
                    });
                }
            }

            if (marker.capability == 'Storage') {
                marker.options.contextmenuItems.push('-');
                marker.options.contextmenuItems.push({
                    icon: 'icons/Graph.png',
                    text: 'Set Storage strategy...',
                    callback: function(e) {
                        socket.emit('command', {'cmd': 'get_storage_strategy_info', 'asset_id': asset_id});
                    }
                });
            }

            if (marker.capability == 'Consumer' || marker.capability == 'Producer') {
                marker.options.contextmenuItems.push('-');
                marker.options.contextmenuItems.push({
                    icon: 'icons/Graph.png',
                    text: 'Set Curtailment strategy...',
                    callback: function(e) {
                        socket.emit('command', {cmd: 'get_curtailment_strategy_info', asset_id: asset_id})
                    }
                });
            }

            if (marker.capability == 'Consumer' || marker.capability == 'Producer' ||
                    marker.capability == 'Conversion') {
                marker.options.contextmenuItems.push('-');
                marker.options.contextmenuItems.push({
                    icon: 'icons/Costs.png',
                    text: 'Set marginal costs...',
                    callback: function(e) {
                        socket.emit('command', {cmd: 'set_marginal_costs_get_info', asset_id: asset_id})
                        //marginal_costs_window(asset_id);
                    }
                });
            }
        }
    }

    marker.options.contextmenuItems.push('-');
    marker.options.contextmenuItems.push({
        // icon: 'icons/Costs.png',
        text: 'Set sector...',
        callback: function(e) {
            select_sector_menu(asset_id);
        }
    });
    // TODO: decide on seperators
    marker.options.contextmenuItems.push('-');
    marker.options.contextmenuItems.push({
        icon: 'icons/Delete.png',
        text: 'Delete',
        callback: function(e) {
            delete_asset(marker);
        }
    });

    // TODO: after editing the layers in LeafletDraw, these events are removed and need to be added again
    marker.off('dragend')
    marker.on('dragend', function(e) {
        var marker = e.target;
        var pos = marker.getLatLng();
        update_marker_ports(marker);
        console.log('update-coord', {id: marker.id, coordinates: pos, asspot: marker.asspot});
        socket.emit('update-coord', {id: marker.id, coordinates: pos, asspot: marker.asspot});

        // console.log(e.oldLatLng.lat);
        // console.log(pos.lat + ', ' + pos.lng );
    });

    marker.on('contextmenu', function(e) {
        // remove tooltip of marker when pressing right mouse button
        // otherwise it hides the contextmenu when moving over tooltip
        remove_tooltip();
    });

    // TODO replace this with map.on("draw:deleted") as then undo function works
    // Now it deletes everything even when you press cancel.
    marker.off('remove')
    marker.on('remove', function(e) {
        // console.log('remove marker');
        // marker.options.icon.tooltip('destroy');
        $(".ui-tooltip-content").parents('div').remove();

        if (deleting_objects == true) {
            // Remove polygon that belongs to marker, if one is present
            if (marker.polygon) {
               // all_layers = esdl_layer.getLayers();
               all_layers = get_layers(active_layer_id, 'esdl_layer').getLayers();
               for (let i=0; i<all_layers.length; i++) {
                    layer = all_layers[i];
                    if (layer.id == asset_id && layer instanceof L.Polygon) {
                        // esdl_layer.removeLayer(layer);
                        remove_object_from_layer(active_layer_id, 'esdl_layer', layer);
                    }
               }
            }

            let layer = e.target;
            if ('buffer_info' in layer)
                spatial_buffers_plugin.remove_spatial_buffers(layer);

            // remove connections manually:
            for (let i in marker.ports) {
                let from_id = marker.ports[i].id;
                for (let j in marker.ports[i].conn_to) {
                    remove_single_connection(from_id, marker.ports[i].conn_to[j], marker.esid)
                }
            }
            socket.emit('command', {cmd: 'remove_object', id: marker.id, asspot: marker.asspot});
        }
    });

    marker.off('click');
    marker.on('click', function(e) {
        var marker = e.target;
        if (!e.originalEvent.shiftKey && !e.originalEvent.ctrlKey && !e.originalEvent.altKey &&
                !e.originalEvent.metaKey) {
            if (deleting_objects == false && editing_objects == false) {        // do not execute when removing/editing objects
                // console.log('marker clicked');
                var marker = e.target;

                if (select_assets.is_select_mode()) {
                    // One or more assets have been selected
                    if (select_assets.is_selected(marker)) {
                        // the current asset is part of this selection
                        let asset_list = select_assets.get_selected_assets();
                        object_properties_window(asset_list);
                    } else { // the current asset is clicked but was not part of the selection
                        object_properties_window(marker.id);
                        select_assets.deselect_all_assets();
                        select_assets.toggle_selected(marker);
                    }
                } else {
                    object_properties_window(marker.id);
                    select_assets.deselect_all_assets();
                    select_assets.toggle_selected(marker);
                }
            }
        } else {
            console.log('click with metakey');
            console.log(e);
        }
    });

    set_marker_port_handlers(marker);
    select_assets.add_asset_handler(marker);

    // let extensions know they can update this layer.
    // e.g. add a context menu item
    for (let i=0; i<extensions.length; i++) {
        updatefun = extensions[i];
        updatefun({type: 'add_contextmenu', layer: marker, layer_type: 'marker'});  // or should layer_type be split into asset/potential
    }
}

// ------------------------------------------------------------------------------------------------------------
//  Handlers for clicking on a pipe or cable
// ------------------------------------------------------------------------------------------------------------
function set_line_handlers(line) {
    let line_id = line.id;
    line.bindContextMenu({
        contextmenu: true,
        contextmenuWidth: 140,
        contextmenuItems: [],
        contextmenuInheritItems: false
    });
    line.options.contextmenuItems.push(
        { text: 'Split', icon: 'icons/SplitLine.png', callback: function(e) { split_conductor(e, line_id); } });
    line.options.contextmenuItems.push(
        { text: 'Split and connect', icon: 'icons/SplitLine.png', callback: function(e) { split_conductor_connect(e, line_id); } });
    line.options.contextmenuItems.push(
        { text: 'Split and add joint', icon: 'icons/SplitLine.png', callback: function(e) { split_conductor_add_joint(e, line_id); } });
    line.options.contextmenuItems.push('-');

    // for (let p=0; p<line.ports.length; p++) {
    //     let port_id = ''+line.ports[p].id;
    //     line.options.contextmenuItems.push({
    //         icon: 'icons/Connect.png',
    //         text: 'Connect ' + line.ports[p].type + ' (' + port_id + '): ' + line.ports[p].name,
    //         callback: function (e) { connect_asset(line_id, port_id); }
    //     });
    // }

    // line.options.contextmenuItems.push('-');
    line.options.contextmenuItems.push({
        text: 'Set carrier',
        icon: 'icons/SetCarrier.png',
        callback: function(e) {
            select_carrier_menu(line_id);
        }
    });

    line.options.contextmenuItems.push({
        icon: 'icons/Delete.png',
        text: 'Delete',
        callback: function(e) {
            delete_asset(line);
        }
    });

    line.off('remove');
    line.on('remove', function(e) {
        let layer = e.target;
        if (layer.mouseOverArrowHead !== undefined) {
            remove_object_from_layer(es_bld_id, 'connection_layer', layer.mouseOverArrowHead);
            delete layer.mouseOverArrowHead;
        }

        // TEST IF THIS IS BETTER
        // if (clear_layer == false) socket.emit('command', {cmd: 'remove_object', id: line.id});
        if (deleting_objects == true) {
            // remove connections
            console.log(line.ports);
            for (let i in line.ports) {
                let from_id = line.ports[i].id;
                for (let j in line.ports[i].conn_to) {
                    remove_single_connection(from_id, line.ports[i].conn_to[j], line.esid)
                }
            }

            if ('buffer_info' in layer)
                spatial_buffers_plugin.remove_spatial_buffers(layer);

            socket.emit('command', {cmd: 'remove_object', id: line.id});
        }
    });

    line.off('click');
    line.on('click', function(e) {
        if (!e.originalEvent.shiftKey && !e.originalEvent.ctrlKey && !e.originalEvent.altKey &&
                !e.originalEvent.metaKey) {
            if (deleting_objects == false && editing_objects == false) {
                var line = e.target;

                if (select_assets.is_select_mode()) {
                    // One or more assets have been selected
                    if (select_assets.is_selected(line)) {
                        // the current asset is part of this selection
                        let asset_list = select_assets.get_selected_assets();
                        object_properties_window(asset_list);
                        L.DomEvent.stopPropagation(e); // prevent click on map
                    } else { // the current asset is clicked but was not part of the selection
                        object_properties_window(line.id);
                        select_assets.deselect_all_assets();
                        select_assets.toggle_selected(line); // highlight selection
                        L.DomEvent.stopPropagation(e);
                    }
                } else {
                    object_properties_window(line.id);
                    select_assets.deselect_all_assets();
                    select_assets.toggle_selected(line);
                    L.DomEvent.stopPropagation(e);
                }
            }
        }
    });
    line.off('edit');
    line.on('edit', function(e) { // in edit mode dragging has ended: update connections
        var layer = e.target;
        //var pos = marker.getLatLng();
        polyline_length = calculate_length(layer);
        socket.emit('update-line-coord', {id: layer.id, polyline: layer.getLatLngs(), length: polyline_length});
        //socket.emit('update-coord', {id: marker.id, coordinates: pos, asspot: marker.asspot});
        // console.log(e.oldLatLng.lat);
        // console.log(pos.lat + ', ' + pos.lng );
    });

    set_line_port_handlers(line);
    select_assets.add_asset_handler(line);

    // let extensions know they can update this layer.
    // e.g. add a context menu item
    for (let i=0; i<extensions.length; i++) {
        updatefun = extensions[i];
        updatefun({type: 'add_contextmenu', layer: line, layer_type: 'line'});
    }

}


function add_asset(es_bld_id, asset_info, add_to_building, carrier_info_mapping, tt_format) {
    // Format of asset_info
    // 0         1          2     3   4           5          6      7      8        9
    // 'point'   asset      name  id  class_name  [lat,lon]  attrs  state  [ports]  capability
    // 'line'    asset      name  id  class_name  [...]      attrs  state  [ports]
    // 'polygon' asset      name  id  class_name  [...]      attrs  state  [ports]  capability
    // 'point'   potential  name  id  class_name  [lat,lon]
    // 'polygon' potential  name  id  class_name  [...]
    if ((asset_info[0] == 'point' && asset_info[1] == 'asset' && asset_info[4] != 'Joint') ||
        (asset_info[0] == 'polygon' && asset_info[1] == 'asset' )) {
        capability = asset_info[9];
        classname = 'circle ' + capability;
        if (!add_to_building) classname = 'zoom '+classname;
    } else if (asset_info[1] == 'potential') {
        classname = 'circle Potential';
        if (!add_to_building) classname = 'zoom '+classname;
    } else {
        classname = '';
    }
    let img_class = "circle-img";
    if (!add_to_building) img_class = 'zoom '+img_class;
    if (asset_info[1] == 'asset') {
        if (asset_info[7] == 'o') {
            classname += ' Optional';       // will become 'Producer Optional'
        }
        if (asset_info[7] == 'd') {
            classname += 'Disabled';        // will become 'ProducerDisabled'
            img_class += "-disabled";
        }
    }
  
    imgsrc = 'images/' + asset_info[4] + '.png';
    if (!assets_for_icons.includes(asset_info[4])) {
        imgsrc = drawTextImage(getAbbrevation(asset_info[4]));
    }
  
    var divicon = L.divIcon({
        className: classname,
        html: '<div class="image-div" style="font-size:0px"><img class="'+img_class+'" src="' + imgsrc + '"></img></div>',
        iconSize: null
    });
    if (asset_info[4] == 'Joint') {
        img_class = "circle-img-joint"
        if (!add_to_building) img_class = 'zoom '+img_class;
        classname = "Joint"
        if (!add_to_building) classname = 'zoom '+classname;
        divicon = L.divIcon({
            className: classname,
            html: '<div style="font-size:0px"><img class="'+img_class+'" src="' + imgsrc + '"></img></div>',
            iconSize: null
        });
    }
  
    if (asset_info[2] == null) asset_info[2] = 'No name';
    var title = asset_info[4]+': '+asset_info[2];
    if (asset_info[0] == 'point' && !(asset_info[1] == 'asset' && 'surfaceArea' in asset_info[6])) {
        var marker = L.marker(
            [asset_info[5][0], asset_info[5][1]], {
                icon: divicon,
                title: title,
                riseOnHover: true,
                draggable: true,
                autoPan: true,
            }
        );
  
        marker.title = title;
        marker.id = asset_info[3];
        marker.esid = es_id;
        marker.name = asset_info[2];
        marker.type = asset_info[4];
        marker.asspot = asset_info[1];
        marker.attrs = asset_info[6];
        if (marker.asspot == 'asset') {
            marker.ports = asset_info[8];
            marker.capability = asset_info[9];
        }
  
        set_marker_handlers(marker);
        add_object_to_layer(es_bld_id, 'esdl_layer', marker);

        if (asset_info[1] == 'asset') {
            if (spatial_buffers_plugin.show_spatial_buffers())
                spatial_buffers_plugin.add_spatial_buffers(marker);

            if (user_settings.ui_settings.tooltips.show_asset_information_on_map)
                marker.bindTooltip(get_tooltip_text(tt_format['marker'], marker.name, marker.attrs),
                    { permanent: true, className: 'marker-tooltip' });
        }
    }
    if (asset_info[0] == 'polygon' || (asset_info[0] == 'point' && asset_info[1] == 'asset' && 'surfaceArea' in asset_info[6])) {
        // If an asset has an esdl.Point geometry and a surfaceArea attribute, draw it as a circle.
        var coords = asset_info[5]
        let polygon_color;
        if (asset_info[1] == 'asset') {
            polygon_color = colors[asset_info[9]]
        } else {
            polygon_color = colors["Potential"]
        }
        var polygon;
        if (asset_info[0] == 'polygon') {
            polygon = L.polygon(coords, {color: polygon_color, weight: 3, draggable:true, title: title});
        } else {
            let radius = Math.sqrt(asset_info[6]['surfaceArea'] / Math.PI)
            polygon = L.circle(coords, {radius: radius, color: polygon_color, weight: 3, draggable:true, title: title});
        }
  
        polygon.title = title;
        polygon.id = asset_info[3];
        polygon.esid = es_id;
        polygon.name = asset_info[2];
        polygon.type = asset_info[4];
        polygon.asspot = asset_info[1];
        polygon.attrs = asset_info[6];
        // esdl_layer.addLayer(polygon);
        add_object_to_layer(es_bld_id, 'esdl_layer', polygon);
        if (spatial_buffers_plugin.show_spatial_buffers())
            spatial_buffers_plugin.add_spatial_buffers(polygon);
  
        var polygon_center = coords;        // Take the point location as a center or
        if (asset_info[0] == 'polygon') {   // if its a polygon, calculate the center
            polygon_center = calculate_array_polygon_center(coords);
        }
        var marker = L.marker(polygon_center, {icon: divicon, title: title, riseOnHover: true});
  
        marker.title = title;
        marker.id = asset_info[3];
        marker.esid = es_id;
        marker.name = asset_info[2];
        marker.type = asset_info[4];
        marker.asspot = asset_info[1];
        marker.attrs = asset_info[6];
        marker.polygon = polygon;
        polygon.marker = marker;
        if (marker.asspot == 'asset') {
            marker.ports = asset_info[8];
            marker.capability = asset_info[9];
        }
  
        set_marker_handlers(marker);
        add_object_to_layer(es_bld_id, 'esdl_layer', marker);
  
        if (user_settings.ui_settings.tooltips.show_asset_information_on_map)
            marker.bindTooltip(get_tooltip_text(tt_format['marker'], marker.name, marker.attrs),
                { permanent: true, className: 'marker-tooltip' });
    }
    if (asset_info[0] == 'line') {
        var coords = asset_info[5];
        var lineType = asset_info[4];
        var port_list = asset_info[8];
        var line_color = colors[lineType];
        for (let p=0; p<port_list.length; p++) {
            let port_carrier_id = port_list[p]['carrier'];
            if (port_carrier_id) {
                line_color = carrier_info_mapping[port_carrier_id]['color'];
            }
        }
        let line_options = {color: line_color, weight: 3, draggable:true, title: title, className:"zoomline"};
        if (asset_info[7] == 'o') {   // Optional asset with dashed line
            line_options['dashArray'] = '3,10';
        }
        if (asset_info[7] == 'd') {    // Disabled asset with grey dotted line
            line_options['dashArray'] = '2,4';
            line_options['color'] = '#808080';
        }
        var line = L.polyline(coords, line_options);
  
        // line.bindPopup(asset_info[4]+': '+asset_info[2]+ '('+ asset_info[3] + ')');
        line.title = title;
        line.id = asset_info[3];
        line.esid = es_id;
        line.ports = asset_info[8];
        line.type = asset_info[4];
        line.asspot = asset_info[1];
        line.attrs = asset_info[6];
        line.state = asset_info[7];
        line.name = asset_info[2];     // "";
        line.color = line_color;    // TODO: improve?
  
        set_line_handlers(line);
        add_object_to_layer(es_bld_id, 'esdl_layer', line);
        if (spatial_buffers_plugin.show_spatial_buffers())
            spatial_buffers_plugin.add_spatial_buffers(line);

        if (user_settings.ui_settings.tooltips.show_asset_information_on_map)
            line.setText(get_tooltip_text(tt_format['line'], line.name, line.attrs) +
                '                   ', {repeat: true});
    }
}


var debug_layer;
function init_selection_pane(map) {
    // panes allow us to play with the zIndex of layers
    var overlay_pane = map.createPane('lineSelectionPane');
    map.getPane('lineSelectionPane').style.zIndex = 350;
}


/**
Refreshes the line color based on the (updated) data of the layer
*/
var ui_counter = 0;
function update_line_color(line_layer) {
    ui_counter++;
    debug_layer = line_layer;
    var line_color = colors[line_layer.type];
    let port_list = line_layer.ports;
    if (port_list) { // find line color based on carrier if available
        for (let p=0; p<port_list.length; p++) {
            let port_carrier_id = port_list[p]['carrier'];
            if (port_carrier_id) {
                line_color = carrier_info_mapping[port_carrier_id]['color'];
                break;
            }
        }
    }
    // default state
    let line_options = {lineCap: 'round', opacity: 1.0, color: line_color, weight: 3, draggable:true, title: title, className:"zoomline", dashArray:""};

    if (line_layer.selected) {
        //line_options['color'] = '#000000';
        //line_options['dashArray'] = '15,5';
        //line_options['weight'] = 25;
        //line_options['lineCap'] = 'butt';
        //$('#mapid .zoomline').css({'opacity': 0.5});
        $('#mapid .zoomline').addClass('notselectedline'); // unhighlight all
        if (line_layer.selectline === undefined) {
            let size_line = 3;
            if (map.getZoom() > 12) size_line = 2 * map.getZoom() - 27 + 6; //butt
            let selectline_options = {lineCap: 'round', color: "#050505", weight: size_line, draggable:false,
                                      title: title, className:"overlayline",
                                      dashArray:"", opacity: 1.0, pane: 'lineSelectionPane'};
            //$('#mapid .zoomline').css({'stroke-width': size_line});
            var selectline = L.polyline(line_layer.getLatLngs(), selectline_options);
            line_layer.selectline = selectline;
            add_object_to_layer(es_bld_id, 'esdl_layer', selectline);
            if (L.DomUtil.hasClass(line_layer._path, 'notselectedline')) {
                L.DomUtil.removeClass(line_layer._path, 'notselectedline');
                L.DomUtil.addClass(line_layer._path, 'selectedline');
            }
        }
        //line_options['color'] = "#FFDDDD";
        //line_options['opacity'] = 0.5;

        //
    } else {
        if (line_layer.selectline) {
            //console.log('remove select line');
            remove_object_from_layer(es_bld_id, 'esdl_layer', line_layer.selectline);
            //line_layer.selectline.remove();
            delete line_layer.selectline;
        }
        L.DomUtil.removeClass(line_layer._path, 'selectedline');
    }

    if (select_assets.get_selected_assets().length == 0) {
        //$('#mapid .zoomline').css({'opacity': 1.0});
        $('#mapid .zoomline').removeClass('notselectedline');
    }

    if (line_layer.state == 'o') {   // Optional asset with dashed line
        line_options['dashArray'] = '3,10';
    }
    if (line_layer.state == 'd') {    // Disabled asset with grey dotted line
        line_options['dashArray'] = '2,4';
        line_options['color'] = '#808080';
    }

    if (line_layer.mouseactive) { // mousemove
        // thicker line
        line_options['weight'] = 7;
    }

    line_layer.setStyle(line_options);
    line_layer.color = line_color;
    //console.log('line color', line_options['color'], line_color, line_layer.selected)
}

// ------------------------------------------------------------------------------------------------------------
//  Calculates leaflet sizes of assets, joints, ...
// ------------------------------------------------------------------------------------------------------------
function set_leaflet_sizes() {
    let zoom_level = map.getZoom();
    let size = Math.pow(zoom_level/8+1,3);

    /* Markers */
    let marker_border = '1px';
    if (zoom_level > 12 && zoom_level <= 15) marker_border = '2px';
    if (zoom_level > 15) marker_border = '3px';

    let size_marker = '' + size + 'px';
    let margin_marker = '-' + (size + 6)/2 + 'px';      /* border is 3px, so add twice the border */
    let size_image = '' + 0.7*size + 'px';              /* image size 70% of marker size */

    $('#mapid .zoom.circle').css({
        'width': size_marker,
        'height': size_marker,
        'line-height': size_marker,
        'margin-left': margin_marker,
        'margin-top': margin_marker,
        'border-width': marker_border
    });
    $('#mapid .image-div').css({'text-align':'center'});
    $('#mapid .zoom.circle-img').css({'width':size_image, 'height':size_image});

    /* Joints */
    if (size/3 < 5) size_joint = 5; else size_joint = size/3;
    let size_joint_px = '' + size_joint + 'px';                /* markers were 30px, joints were 10px */
    let margin_joint_px = '-' + size_joint/2 + 'px';           /* center joint */

    $('#mapid .zoom.Joint').css({'width':size_joint_px, 'height':size_joint_px, 'margin-left':margin_joint_px, 'margin-top':margin_joint_px});
    $('#mapid .zoom.circle-img-joint').css({'width':size_joint_px, 'height':size_joint_px});

    /* Lines */
    let size_line = 2;
    if (zoom_level > 15) size_line = '' + 2 * zoom_level - 27;
    $('#mapid .zoomline').css({'stroke-width': size_line + 'px'});
    $('#mapid .overlayline').css({'stroke-width': (size_line + 6) + 'px' });

    set_port_size_and_position();       /* Ports */
}