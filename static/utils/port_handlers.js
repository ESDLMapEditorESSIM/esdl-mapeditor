var port_drawing_connection = false;
var first_port = null;
var connecting_line = null;

function set_marker_port_handlers(marker) {
    marker.on('mouseover', function(e) {
        let layer = e.target;
        console.log(layer);

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
            let class_name = 'Port '+ports[p].type+' '+css_joint_addition+ports[p].type+num_ports[ports[p].type].toString()+(cnt_ports[ports[p].type]+1).toString();
            cnt_ports[ports[p].type]++;
            let port_name = ports[p].type + ' - ' + ports[p].name;

            let divicon = L.divIcon({
                className: class_name,

                iconSize:     [14, 14], // size of the icon
                iconAnchor:   [7, 7], // point of the icon which will correspond to marker's location
                popupAnchor:  [0, -2] // point from which the popup should open relative to the iconAnchor
            });

            let port_marker = L.marker([coords.lat, coords.lng], {icon: divicon, title: port_name});
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
                layer.removeFrom(map);
            });
            port_marker.on('click', function(e) {
                let layer = e.target;
                if (first_port == null) first_port = port_marker;
                click_port(layer);
            });
        }
    });

    marker.on('mouseout', function(e) {
        let layer = e.target;
        let ports = layer.ports;

        for (let p in ports) {
            setTimeout(function() {
                if (ports[p].active == false) {
                    ports[p].marker.removeFrom(map);
                }
            }, 10);
        }
    });
}

function move_connection(e) {
    let strt_pos;
    console.log(first_port);
    console.log(typeof first_port.parent);
    if (first_port.parent_type === 'marker') {
        strt_pos = first_port.parent.getLatLng();
    } else if (first_port.parent_type === 'line') {
        strt_pos = first_port.getLatLng();
    }

    console.log(strt_pos);

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
}

function click_port(layer) {
    let start_lat = layer._latlng['lat'];
    let start_lng = layer._latlng['lng'];

    let this_pos;
    if (first_port.parent_type === 'marker') {
        this_pos = layer.parent.getLatLng();
    } else if (first_port.parent_type === 'line') {
        this_pos = layer.getLatLng();
    }
    if (port_drawing_connection) {
        socket.emit('command', {'cmd': 'connect_ports', port1id: first_port.port_parent.id, port2id: layer.port_parent.id});

        connecting_line.removeFrom(map);
        connecting_line = null;
        map.off('mousemove', move_connection);
        map.off('contextmenu', cancel_connection);
        first_port = null;
        port_drawing_connection = false;
    } else {
        port_drawing_connection = true;
        map.on('mousemove', move_connection);
        map.on('contextmenu', cancel_connection);
    }
}

function set_line_port_handlers(line) {
    line.on('mouseover', function(e) {
        let layer = e.target;
        console.log(layer);

        let ports = layer.ports;
        let coords = layer._latlngs;
        let coords_len = coords.length;

        console.log(coords);

        for (let p in ports) {
            if (p == '0') coords_index = 0; else coords_index = coords_len - 1;

            let class_name = 'Port '+ports[p].type;
            let port_name = ports[p].type + ' - ' + ports[p].name;

            let divicon = L.divIcon({
                className: class_name,

                iconSize:     [14, 14], // size of the icon
                iconAnchor:   [7, 7], // point of the icon which will correspond to marker's location
                popupAnchor:  [0, -2] // point from which the popup should open relative to the iconAnchor
            });

            let port_marker = L.marker([coords[coords_index].lat, coords[coords_index].lng], {icon: divicon, title: port_name});
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
                layer.removeFrom(map);
            });
            port_marker.on('click', function(e) {
                let layer = e.target;
                if (first_port == null) first_port = port_marker;
                click_port(layer);
            });
        }
    });

    line.on('mouseout', function(e) {
        let layer = e.target;
        let ports = layer.ports;

        for (let p in ports) {
            setTimeout(function() {
                if (ports[p].active == false) {
                    ports[p].marker.removeFrom(map);
                }
            }, 10);
        }
    });
}
