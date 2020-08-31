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

var bld_map;
var bld_edit_id = null;        // stores the ID of the building while editing building

function open_building_editor(dialog, building_info) {
    console.log(building_info);
    bld_edit_id = building_info['id'];

    var contents = [
        "<div class=\"building-info\" id=\"building-info\">",
            "<div class=\"flexbox-parent\">",
                "<div class=\"flexbox-item\">",

                    "<div id=\"bld_ctrl\" style=\"clear: left; position: relative; padding:3px;\">",
                    "    <button id=\"bld_edr-asset-btn\" onclick=\"select_edr_asset_window();\" title=\"EDR assets\" class=\"ui-button ui-widget ui-corner-all\">EDR assets</button>",
                    "    <select id=\"bld_asset_menu\" style='position:relative;z-index:100'>",
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

    if (bld_map && bld_map.remove) {
        bld_map.off();
        bld_map.remove();
    }

    bld_map = new L.Map('bldmapid', {
        crs: L.CRS.Simple,
        maxBounds: [[0,0],[500,500]]
    });

    L.imageOverlay('images/BuildingBackground.png', [[0,0],[500,500]]).addTo(bld_map);

    bld_map = add_building_map_handlers(bld_map);

    var bounds = [[0,0], [500,500]];
    var bld_background = L.imageOverlay('', bounds);
    bld_map.fitBounds(bounds);

    create_new_bld_layer(bld_edit_id, 'Building', bld_map);
    active_layer_id_backup = active_layer_id;
    // TODO: check if this is handy!!
    active_layer_id = bld_edit_id;

    L.control.layers(
        {
            'Building': bld_background.addTo(bld_map)
        },
        {
            'Assets': get_layers(bld_edit_id, 'esdl_layer'),
            'BuildingUnits': get_layers(bld_edit_id, 'bld_layer'),
            'Connections': get_layers(bld_edit_id, 'connection_layer'),
            'Potentials': get_layers(bld_edit_id, 'pot_layer')
        },
        { position: 'topright', collapsed: false }
    ).addTo(bld_map);

    var bld_draw_control = new L.Control.Draw({
        edit: {
            featureGroup: get_layers(bld_edit_id, 'esdl_layer'),
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
    L.control.mousePosition().addTo(bld_map);

    map.off('dialog:closed'); // previous event handler must be removed
    function on_dialog_close(event) {
        console.log('close - remove bld layer with id: '+bld_edit_id);
        remove_bld_layer(bld_edit_id);
        //close_dialog(event, bld_edit_id)
        active_layer_id = active_layer_id_backup;
        select_area_bld_list(area_before_building_edit);
        bld_edit_id = null;
    }
    map.on('dialog:closed', on_dialog_close);

    $(function() {
        $("#bld_asset_menu").selectmenu({ 'width':200, 'max-height': 500 }); //.selectmenu( "menuWidget" ).addClass( "overflow" );
        $("#bld_line_select").selectmenu({ width:200 });
        $("#bld_select").selectmenu({ width:500 });
    });

    // changes the icon for the new marker command
    $('#bld_asset_menu').on('selectmenuchange', function (e) {
        socket.emit('command', {'cmd': 'set_asset_drawing_mode', 'mode': 'empty_assets'});
        initiate_draw_asset(bld_draw_control, 'bld_asset_menu');
    });

    build_asset_menu('bld_asset_menu', false, cap_pot_list);
    bld_draw_control = add_draw_control(bld_draw_control, bld_map);                 // couple draw_control to active layer

    dialog.open();
}

function add_handler() {
//socket.on('add_esdl_objects', function(data) {
//    console.log('add_esdl_objects (bld)');
//    console.log(data);
//});
}