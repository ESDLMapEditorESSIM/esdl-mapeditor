
function open_building_editor(dialog, building_info) {
    console.log(building_info);
    let bld_id = building_info['id'];

    var contents = [
        "<div class=\"building-info\" id=\"building-info\">",
            "<div class=\"flexbox-parent\">",
                "<div class=\"flexbox-item\">",

                    "<div id=\"bld_ctrl\" style=\"clear: left; position: relative; padding:3px;\">",
                    "    <button id=\"bld_edr-asset-btn\" onclick=\"select_edr_asset_window();\" title=\"EDR assets\" class=\"ui-button ui-widget ui-corner-all\">EDR assets</button>",
                    "    <select id=\"bld_asset_menu\" style='position:relative;z-index:100'>",
                    "        <option value=\"Battery\">Battery</option>",
                    "        <option value=\"CHP\">Combined Heat and Power</option>",
                    "        <option value=\"EConnection\">EConnection</option>",
                    "        <option value=\"ElectricityDemand\">ElectricityDemand</option>",
                    "        <option value=\"ElectricityNetwork\">ElectricityNetwork</option>",
                    "        <option value=\"Electrolyzer\">Electrolyzer</option>",
                    "        <option value=\"FuelCell\">FuelCell</option>",
                    "        <option value=\"GConnection\">GConnection</option>",
                    "        <option value=\"GasHeater\">GasHeater</option>",
                    "        <option value=\"GasNetwork\">GasNetwork</option>",
                    "        <option value=\"GenericConsumer\">GenericConsumer</option>",
                    "        <option value=\"GenericConversion\">GenericConversion</option>",
                    "        <option value=\"GenericProducer\">GenericProducer</option>",
                    "        <option value=\"GeothermalSource\">GeothermalSource</option>",
                    "        <option value=\"HeatingDemand\">HeatingDemand</option>",
                    "        <option value=\"HeatNetwork\">HeatNetwork</option>",
                    "        <option value=\"HeatPump\">HeatPump</option>",
                    "        <option value=\"Joint\">Joint</option>",
                    "        <option value=\"MobilityDemand\">MobilityDemand</option>",
                    "        <option value=\"PowerPlant\">PowerPlant</option>",
                    "        <option value=\"PVInstallation\">PVInstallation</option>",
                    "        <option value=\"PVParc\">PVParc</option>",
                    "        <option value=\"Transformer\">Transformer</option>",
                    "        <option value=\"UTES\">UTES</option>",
                    "        <option value=\"WindTurbine\">WindTurbine</option>",
                    "    </select>",

                    "    <select id=\"bld_line_select\">",
                    "        <option value=\"ElectricityCable\">ElectricityCable</option>",
                    "        <option value=\"Pipe\">Pipe</option>",
                    "    </select>",

                    "    <select id=\"bld_select\"></select>",
                    "</div>",

                "</div>",
                // "<div id=\"bldmapid\" class=\"flexbox-item flexbox-item-grow\" style=\"height: 610px; width:100%; z-index:8000\"></div>",
                "<div id=\"bldmapid\" style=\"height: 610px; width:100%; z-index:8000\"></div>",
            "</div>",
        "</div>"
    ].join('');

    dialog.setContent(contents);
    // document.getElementById('building-info').innerHTML = 'Test';

    var bld_map = new L.Map('bldmapid', {
        crs: L.CRS.Simple,
        maxBounds: [[0,0],[500,500]]
    });

    var bounds = [[0,0], [500,500]];
    var bld_background = L.imageOverlay('', bounds);
    bld_map.fitBounds(bounds);

    create_new_bld_layer(bld_id, 'Building', bld_map)
    L.control.layers(
        {
            'Building': bld_background.addTo(bld_map)
        },
        {
            'Assets': get_layers(bld_id, 'esdl_layer'),
            'BuildingUnits': get_layers(bld_id, 'bld_layer'),
            'Connections': get_layers(bld_id, 'connection_layer'),
            'Potentials': get_layers(bld_id, 'pot_layer')
        },
        { position: 'topright', collapsed: false }
    ).addTo(bld_map);

    var bld_draw_control = new L.Control.Draw({
        edit: {
            featureGroup: get_layers(bld_id, 'esdl_layer'),
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
                repeatMode: true
            }
        }
    });
    bld_map.addControl(bld_draw_control);

    L.marker(L.latLng([  0,  0])).addTo(bld_map);
    L.marker(L.latLng([500,  0])).addTo(bld_map);
    L.marker(L.latLng([  0,500])).addTo(bld_map);
    L.marker(L.latLng([500,500])).addTo(bld_map);

    L.control.mousePosition().addTo(bld_map);

    bld_map.on(L.Draw.Event.CREATED, function (event) {
        var layer = event.layer;

        get_layers(bld_id, 'esdl_layer').addLayer(layer);
    });

    map.off('dialog:closed'); // previous event handler must be removed
    function on_dialog_close(event) {
        console.log('close - remove bld layer with id: '+bld_id);
        remove_bld_layer(bld_id);
        //close_dialog(event, bld_id)
    }
    map.on('dialog:closed', on_dialog_close);

    $(function() {
        $("#bld_asset_menu").selectmenu({ 'width':200, 'max-height': 500 }); //.selectmenu( "menuWidget" ).addClass( "overflow" );
        $("#bld_line_select").selectmenu({ width:200 });
        $("#bld_select").selectmenu({ width:500 });
    });

    dialog.open();
}

function add_handler() {
socket.on('add_esdl_objects', function(data) {
    console.log('add_esdl_objects (bld)');
    console.log(data);
});
}