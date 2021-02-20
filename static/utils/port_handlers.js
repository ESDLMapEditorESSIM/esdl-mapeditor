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

var port_drawing_connection = false;
var first_port = null;
var connecting_line = null;
var port_drawing_conductor = false;



function set_port_size_and_position() {
    let size = Math.pow(map.getZoom()/8+1,3);

    let port_inner_width = 8;
    let port_border_width = 3;
    let port_outer_width = port_inner_width + 2 * port_border_width;
    let port_rm_x = (size / 2); // - 3 + port_border_width;
    let port_rt_x = (size / 3); // + port_border_width;
    let port_rb_x = (size / 3); // + port_border_width;
    let port_lm_x = -port_rm_x - port_outer_width;
    let port_lt_x = -port_rt_x - port_outer_width;
    let port_lb_x = -port_rb_x - port_outer_width;
    let size_port = port_outer_width;

    /* Ports */
    $('#mapid .OutPort11').css({'width':size_port, 'height':size_port, 'margin-left':''+port_rm_x+'px', 'margin-top':'-7px'});
    $('#mapid .OutPort21').css({'width':size_port, 'height':size_port, 'margin-left':''+port_rt_x+'px', 'margin-top':'-22px'});
    $('#mapid .OutPort22').css({'width':size_port, 'height':size_port, 'margin-left':''+port_rb_x+'px', 'margin-top':'8px'});
    $('#mapid .OutPort31').css({'width':size_port, 'height':size_port, 'margin-left':''+port_rt_x+'px', 'margin-top':'-22px'});
    $('#mapid .OutPort32').css({'width':size_port, 'height':size_port, 'margin-left':''+port_rm_x+'px', 'margin-top':'-7px'});
    $('#mapid .OutPort33').css({'width':size_port, 'height':size_port, 'margin-left':''+port_rb_x+'px', 'margin-top':'8px'});
    $('#mapid .InPort11').css({'width':size_port, 'height':size_port, 'margin-left':''+port_lm_x+'px', 'margin-top':'-7px'});
    $('#mapid .InPort21').css({'width':size_port, 'height':size_port, 'margin-left':''+port_lt_x+'px', 'margin-top':'-22px'});
    $('#mapid .InPort22').css({'width':size_port, 'height':size_port, 'margin-left':''+port_lb_x+'px', 'margin-top':'8px'});
    $('#mapid .InPort31').css({'width':size_port, 'height':size_port, 'margin-left':''+port_lt_x+'px', 'margin-top':'-22px'});
    $('#mapid .InPort32').css({'width':size_port, 'height':size_port, 'margin-left':''+port_lm_x+'px', 'margin-top':'-7px'});
    $('#mapid .InPort33').css({'width':size_port, 'height':size_port, 'margin-left':''+port_lb_x+'px', 'margin-top':'8px'});

    /* Joint ports */
    if (size/3 < 5) size_joint = 5; else size_joint = size/3;
    let joint_port_rm_x = size_joint/2 - 1;
    let joint_port_lm_x = -joint_port_rm_x - port_outer_width;
    $('#mapid .JointOutPort11').css({'width':size_port, 'height':size_port, 'margin-left':''+joint_port_rm_x+'px', 'margin-top':'-7px'});
    $('#mapid .JointInPort11').css({'width':size_port, 'height':size_port, 'margin-left':''+joint_port_lm_x+'px', 'margin-top':'-7px'});

    /* Line ports */
    $('#mapid .LinePort').css({'width':size_port, 'height':size_port, 'margin-left':'-7px', 'margin-top':'-7px'});
}

function set_marker_port_handlers(marker) {
    marker.on('mouseover', function(e) {
        if (!editing_objects && !deleting_objects) {
            let layer = e.target;
            let ports = layer.ports;
            let coords = layer._latlng;

            let num_ports = {
                'OutPort': 0,
                'InPort': 0
            };
            for (let p in ports) num_ports[ports[p].type]++;
            let cnt_ports = {
                'OutPort': 0,
                'InPort': 0
            };

            let css_joint_addition = '';
            let marker_type = marker.type;
            if (marker_type === 'Joint') css_joint_addition = 'Joint';

            for (let p in ports) {
                if (!drawState.canConnect(ports[p])) continue; // only show port that can be connected
                let class_name = 'Port '+ports[p].type+' '+css_joint_addition+ports[p].type+num_ports[ports[p].type].toString()+(cnt_ports[ports[p].type]+1).toString();
                cnt_ports[ports[p].type]++;
                let port_name = ports[p].type + ' - ' + ports[p].name;

                let divicon = L.divIcon({
                    className: class_name,
                    iconSize: null
                });

                if (ports[p].marker === undefined) {
                    // marker not yet created
                    let port_marker = L.marker([coords.lat, coords.lng], {icon: divicon, title: port_name, zIndexOffset:1000});
                    port_marker.addTo(map);

                    ports[p].active = false;
                    ports[p].marker = port_marker;
                    port_marker.parent = marker;
                    port_marker.parent_type = 'marker';
                    port_marker.port_parent = ports[p];

                    port_marker.on('mouseover', function(e) {
                        let layer = e.target;
                        layer.port_parent.active = true;

                    });
                    port_marker.on('mouseout', function(e) {
                        let layer = e.target;
                        setTimeout(function() {
                            layer.port_parent.active = false;
                            layer.removeFrom(map);
                        }, 50);
    //                    layer.removeFrom(map);
                    });
                    port_marker.on('click', function(e) {
                        handle_connect(port_marker, e);
                    });
                    port_marker.on('keyup', function(e) {
                        if (e.keyCode === 27) {
                            console.log('esc pressed!')
                        }
                    });
                } else {
                    // show already created marker
                    ports[p].active = false;
                    ports[p].marker.addTo(map);
                }
            }
            set_port_size_and_position();
        }
    });

    marker.on('mouseout', function(e) {
        let layer = e.target;
        let ports = layer.ports;

        for (let p in ports) {
            setTimeout(function() {
                if (ports[p].active === false) {
                    ports[p].marker.removeFrom(map);
                }
            }, 300);
        }
    });
}

function handle_connect(port_marker, e) {
    let layer = e.target;
    //console.log('port_marker click', e);
    // pressing Ctrl button on keyboard starts drawing pipe/cable
    handler = draw_control._toolbars.draw._modes.polyline.handler;
    // handler._enabled == true means that the person started drawing using the line tool in the toolbar
    if ((e.originalEvent.ctrlKey || e.originalEvent.metaKey) || ((drawState.isDrawing() || handler._enabled) && !port_drawing_connection)) {
        // start drawing pipe/cable
        if (drawState.isDrawing() === false) {
            console.log('Connect using conductor');

            if (L.Browser.touch && handler._poly) {
                // already added first point due to touchstart event, but we don't want this point
                // so remove
                let lastMarker = handler._markers.pop();
                let poly = handler._poly;
                handler._poly.setLatLngs([]);
                handler._markerGroup.removeLayer(lastMarker);
                if (poly.getLatLngs().length < 2) {
                    handler._map.removeLayer(poly);
                }
            }
            drawState.startDrawConductor(layer, handler);
            handler.enable();
            handler.addVertex(layer.getLatLng()); // add first point
        } else {
            // finish drawing conductor
            if (L.Browser.touch) {
                // if touch is supported by the browser, clicking on a port
                // generates a touch event on a location we don't want
                handler.deleteLastVertex(); // delete coord of touchstart event on port
            }
            handler.addVertex(layer.getLatLng()); // add latlng of asset
            drawState.stopDrawConductor(layer);
            handler.completeShape();
            drawState.resetRepeatMode();
        }
    } else {
        console.log("Connect ports")
        if (first_port == null) first_port = port_marker;
        click_port(layer);
    }
}

function move_connection(e) {
    let strt_pos;
//    console.log(first_port);
//    console.log(typeof first_port.parent);
    if (first_port.parent_type === 'marker') {
        strt_pos = first_port.parent.getLatLng();
    } else if (first_port.parent_type === 'line') {
        strt_pos = first_port.getLatLng();
    }

//    console.log(strt_pos);

    if (connecting_line == null) {
        connecting_line = L.polyline([strt_pos, e.latlng], {color: '#000000', weight: 2, dashArray: '3,10'});
        connecting_line.addTo(map);
    } else {
        connecting_line.setLatLngs([strt_pos, e.latlng]);
    }
}

function cancel_connection(e) {
    connecting_line.removeFrom(map);
    connecting_line = null;
    first_port = null;
    port_drawing_connection = false;
    map.off('mousemove', move_connection);
    map.off('contextmenu', cancel_connection);
    map.off('draw:canceled', cancel_connection)
}

function click_port(layer) {
    if (port_drawing_connection) {
        socket.emit('command', {'cmd': 'connect_ports', port1id: first_port.port_parent.id, port2id: layer.port_parent.id});

        map.off('mousemove', move_connection);
        map.off('contextmenu', cancel_connection);
        map.off('draw:canceled', cancel_connection)
        connecting_line.removeFrom(map);
        connecting_line = null;
        first_port = null;
        port_drawing_connection = false;
    } else {
        port_drawing_connection = true;
        map.on('mousemove', move_connection);
        map.on('contextmenu', cancel_connection);
        map.on('draw:canceled', cancel_connection);
    }
}

function update_marker_ports(marker) {
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

function update_line_ports(line) {
    let ports = line.ports;
    let coords = line._latlngs;

    for (let p in ports) { // ports is a dictionary: {'0': ...., '1': ...}
        let coords_index = 0;
        if (p !== '0') {
            coords_index = coords.length - 1;
        }
        let marker = ports[p].marker;
        if (marker !== undefined) {
            // update port marker location
            marker.setLatLng([coords[coords_index].lat, coords[coords_index].lng])
        }
    }
}

function set_line_port_handlers(line) {

    line.on('mouseover', function(e) {
        let layer = e.target;

        if (map.getZoom() > 12 || calculate_length(layer) > 1000) {
        // add line decorator with >>> to show direction of conductor
            if (layer.type === undefined) {
                layer.type = 'ElectricityCable';
            }
            layer.setStyle({
                color: layer.color,
                opacity: 1,
                weight: 4
            });
            let lineType = layer.type;
            let lineColor = layer.color;
            // let lineColorHoover = colors[lineType + '_hoover']
            let lineColorHoover = lineColor;
            // only show when zoom level is appropriate and length is larger than 1km
            let arrowHead = L.polylineDecorator(layer, {
                        patterns: [
                            {
                                offset: '1%',
                                repeat: '49%',
                                endOffset: 5,
                                symbol: L.Symbol.arrowHead({pixelSize: 12, polygon: true, pathOptions: {stroke: true, color: lineColorHoover, fillOpacity: 1, weight: 1}})
                            }
                        ]
                    }).addTo(map);
            line.mouseOverArrowHead = arrowHead; // make sure we can removed it later in the mouseOut event
        }

        if (!editing_objects && !deleting_objects) {
           // do handling of ports of a conductor
            let ports = layer.ports;
            let coords = layer._latlngs;
            let coords_len = coords.length;

            for (let p in ports) {
                if (p == '0') coords_index = 0; else coords_index = coords_len - 1;

                let class_name = 'Port '+ports[p].type+' LinePort';
                let port_name = ports[p].type + ' - ' + ports[p].name;

                let divicon = L.divIcon({
                    className: class_name,
                    iconSize: null
                });

                if (ports[p].marker === undefined) {
                    // marker not yet created

                    let port_marker = L.marker([coords[coords_index].lat, coords[coords_index].lng], {icon: divicon, title: port_name, zIndexOffset:1000});
                    port_marker.addTo(map);

                    ports[p].active = false;
                    ports[p].marker = port_marker;
                    port_marker.parent = line;
                    port_marker.parent_type = 'line';
                    port_marker.port_parent = ports[p];

                    port_marker.on('mouseover', function(e) {
                        let layer = e.target;
                        layer.port_parent.active = true;
                    });
                    port_marker.on('mouseout', function(e) {
                        let layer = e.target;
                        setTimeout(function() {
                            layer.port_parent.active = false;
                            layer.removeFrom(map);
                        }, 50);
                    });
                    port_marker.on('click', function(e) {
                        handle_connect(port_marker, e);
//                        let layer = e.target;
//                        if (first_port == null) first_port = port_marker;
//                        click_port(layer);
                    });
                } else {
                    // show already created marker
                    ports[p].active = false;
                    ports[p].marker.addTo(map);
                }
            }
            set_port_size_and_position();
        }
    });

    line.on('mouseout', function(e) {
        let layer = e.target;
        // remove line decoration
        layer.setStyle({
            color: layer.color,
            opacity: 1,
            weight: 3
        });
        if (layer.mouseOverArrowHead !== undefined) {
            map.removeLayer(layer.mouseOverArrowHead)
            delete layer.mouseOverArrowHead;
        }

        // remove port decoration
        let ports = layer.ports;
        for (let p in ports) {
            setTimeout(function() {
                if (ports[p].active === false) {
                    ports[p].marker.removeFrom(map);
                }
            }, 100);
        }
    });
}
