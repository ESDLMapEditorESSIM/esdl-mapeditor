function add_area_map_handlers(socket, map) {

    console.log('Adding handlers to area map');

    // the 'dragend' event of Polyline does not work, this is an alternative solution
    map.on('draw:edited', function (e) {
        var layers = e.layers;
        layers.eachLayer(function (layer) {
            if (layer instanceof L.Polyline && !(layer instanceof L.Polygon)) {
                polyline_length = calculate_length(layer);
                socket.emit('update-line-coord', {id: layer.id, polyline: layer.getLatLngs(), length: polyline_length});
            }
            if (layer instanceof L.Polygon) {

                // Find marker belonging to Polygon and recalculate center
                // esdl_objects = esdl_layer.getLayers();
                esdl_objects = get_layers(active_layer_id, 'esdl_layer').getLayers();
                for (let i=0; i<esdl_objects.length; i++) {
                    esdl_object = esdl_objects[i];
                    if (esdl_object.id == layer.id && esdl_object instanceof L.Marker) {
                        polygon_center = calculate_leaflet_polygon_center(layer.getLatLngs()[0]);
                        var newLatLng = new L.LatLng(polygon_center[0], polygon_center[1]);
                        esdl_object.setLatLng(newLatLng);

                        // send updated coordinates to backend to update connections
                        socket.emit('update-coord', {id: layer.id, lat: polygon_center[0], lng: polygon_center[1], asspot: layer.asspot});
                    }
                }

                // recalculate area
                polygon_area = calculate_area(layer);
                socket.emit('update-polygon-coord', {id: layer.id, polygon: layer.getLatLngs(), polygon_area: polygon_area});
            }
        });
    });

    // To prevent the onclick functionality when removing objects
	map.on(L.Draw.Event.DELETESTART, function (event) {
        deleting_objects = true;
	});

	map.on(L.Draw.Event.DELETESTOP, function (event) {
        deleting_objects = false;
	});

    // To prevent the onclick functionality when editing objects
	map.on(L.Draw.Event.EDITSTART, function (event) {
        editing_objects = true;
	});

	map.on(L.Draw.Event.EDITSTOP, function (event) {
        editing_objects = false;
	});

    map.on(L.Draw.Event.CREATED, function (event) {
        let layer = event.layer;
        let type = event.layerType;
        layer.id = uuidv4();

        selected_area_bld_index = document.getElementById("area_bld_select").selectedIndex;
        selected_area_bld_options = document.getElementById("area_bld_select").options;
        selected_area_bld_id = selected_area_bld_options[selected_area_bld_index].value;
        // console.log('selected area/building id: ' + selected_area_bld_id);

        if (type === 'marker') {
            selection = document.getElementById("asset_menu").selectedIndex;
            asset_options = document.getElementById("asset_menu").options;
            selected_asset = asset_options[selection].value;
            // console.log('selected option: ' + selection);
            // console.log('selected asset: ' + selected_asset);

            layer.name = selected_asset + '_' + layer.id.substring(0,4);
            socket.emit('command', {cmd: 'add_object', area_bld_id: selected_area_bld_id, object: selected_asset, asset_name: layer.name, asset_id: layer.id,
                shape: {
                    type: 'point',
                    crs: 'WGS84',
                    lat: layer.getLatLng().lat,
                    lng: layer.getLatLng().lng
                }
            });
        }
        if (type === 'polyline') {
            line_type = document.getElementById("line_select").value;
            //console.log('selected line type: ' + line_type);
            layer.type = line_type;
            layer.name = line_type + '_' + layer.id.substring(0,4);
            layer.title = layer.name;
            polyline_length = calculate_length(layer);
            socket.emit('command', {cmd: 'add_object', area_bld_id: selected_area_bld_id, object: line_type, asset_name: layer.name, asset_id: layer.id,
                shape: {
                    type: 'polyline',
                    crs: 'WGS84',
                    coordinates: layer.getLatLngs(),
                    length: polyline_length
                }
            });
        }
        if (type === 'polygon' || type === 'rectangle') {
            // TODO: What to do with drawing polygon for an ESDL Area (e.g. a 'bedrijventerrein')
            // socket.emit('command', {cmd: 'set_area_bld_polygon', area_bld_id: selected_area_bld_id, polygon: layer.getLatLngs()});
            // area_layer.addLayer(layer, true);

            selection = document.getElementById("asset_menu").selectedIndex;
            asset_options = document.getElementById("asset_menu").options;
            selected_asset = asset_options[selection].value;
            // console.log('selected option: ' + selection);
            // console.log('selected asset: ' + selected_asset);

            layer.name = selected_asset + '_' + layer.id.substring(0,4);
            polygon_area = calculate_area(layer);
            socket.emit('command', {cmd: 'add_object', area_bld_id: selected_area_bld_id, object: selected_asset, asset_name: layer.name, asset_id: layer.id,
                shape: {
                    type: type,
                    crs: 'WGS84',
                    coordinates: layer.getLatLngs(),
                    polygon_area: polygon_area
                }
            });
        }
    });

    map.on('click', function(e) {
        map.contextmenu.hide();
    });
};
