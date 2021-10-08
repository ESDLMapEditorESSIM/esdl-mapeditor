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
                    delete_asset_marker(marker);
                }
            });
        }
    }

    marker.on('dragend', function(e) {
        var marker = e.target;
        var pos = marker.getLatLng();
        socket.emit('update-coord', {id: marker.id, coordinates: pos, asspot: marker.asspot});
        // console.log(e.oldLatLng.lat);
        // console.log(pos.lat + ', ' + pos.lng );
    });

    // TODO replace this with map.on("draw:deleted") as then undo function works
    // Now it deletes everything even when you press cancel.
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
            delete_asset_line(line);
        }
    });

    line.on('remove', function(e) {
        var layer = e.target;
        if (layer.mouseOverArrowHead !== undefined) {
            map.removeLayer(layer.mouseOverArrowHead)
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

            socket.emit('command', {cmd: 'remove_object', id: line.id});
        }
    });

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
    if (asset_info[0] == 'point') {
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
  
        if (user_settings.ui_settings.tooltips.show_asset_information_on_map)
            marker.bindTooltip(get_tooltip_text(tt_format['marker'], marker.name, marker.attrs),
                { permanent: true, className: 'marker-tooltip' });
    }
    if (asset_info[0] == 'polygon') {
        var coords = asset_info[5];
        let polygon_color;
        if (asset_info[1] == 'asset') {
            polygon_color = colors[asset_info[9]]
        } else {
            polygon_color = colors["Potential"]
        }
        var polygon = L.polygon(coords, {color: polygon_color, weight: 3, draggable:true, title: title});
  
        polygon.title = title;
        polygon.id = asset_info[3];
        polygon.esid = es_id;
        polygon.name = asset_info[2];
        polygon.type = asset_info[4];
        polygon.asspot = asset_info[1];
        polygon.attrs = asset_info[6];
        // esdl_layer.addLayer(polygon);
        add_object_to_layer(es_bld_id, 'esdl_layer', polygon);
  
        var polygon_center = calculate_array_polygon_center(coords);
        var marker = L.marker(polygon_center, {icon: divicon, title: title, riseOnHover: true});
  
        marker.title = title;
        marker.id = asset_info[3];
        marker.esid = es_id;
        marker.name = asset_info[2];
        marker.type = asset_info[4];
        marker.asspot = asset_info[1];
        marker.attrs = asset_info[6];
        marker.polygon = true;
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
    for (let p=0; p<port_list.length; p++) {
        let port_carrier_id = port_list[p]['carrier'];
        if (port_carrier_id) {
            line_color = carrier_info_mapping[port_carrier_id]['color'];
            break;
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
            if (map.getZoom() > 15) size_line = 2 * map.getZoom() - 27 + 6; //butt
            let selectline_options = {lineCap: 'round', color: "#000000", weight: size_line, draggable:false,
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
            console.log('remove select line');
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
    console.log('line color', line_options['color'], line_color, line_layer.selected)
}