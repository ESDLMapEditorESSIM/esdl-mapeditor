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

// Heat network extension


//function init() {}

function duplicate(event, id) {
    // console.log('Duplicating layer id = ', id)
    let area_bld_id = $( "#area_bld_select" ).val();
    socket.emit('duplicate', {asset_id: id, area_bld_id: area_bld_id});
}

function reverse_conductor(event, id) {
    socket.emit('reverse_conductor', {asset_id: id});
}

function update(event) {
    if (event.type === 'add_contextmenu') {
        let layer = event.layer;
        let id = layer.id;
        // console.log('Extension HeatNetwork add_contextmenu for id=' + id)
        // Only add 'duplicate' context menu for EnergyAssets (not for Areas and Buildings)
        if (layer.hasOwnProperty("asspot")) {
            if (layer.asspot === 'asset') {
                layer.options.contextmenuItems.push({
                    text: 'Duplicate',
                    icon: resource_uri + 'icons/Duplicate.png',
                    callback: function(e) { duplicate(e, id); }
                });
            }
        }
        if (event.layer_type === 'line') {
            layer.options.contextmenuItems.push({
                text: 'Reverse',
                icon: resource_uri + 'icons/Reverse.png',
                callback: function(e) { reverse_conductor(e, id); }
            });
        }
    }

}


$(document).ready(function() {
    extensions.push(update)
});