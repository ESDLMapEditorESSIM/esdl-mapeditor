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


var edr_asset_list;
var edr_asset_type_list;

function get_edr_assets(url) {
    $.ajax({
        url: url,
        success: function(data){
            edr_asset_list = data["item_list"];
            edr_asset_type_list = data["item_type_list"];
        },
        dataType: "json"
    });
}

class ReplaceWithEDRAsset {
    constructor() {
        this.initSocketIO();
        this.tmp = null;
    }

    initSocketIO() {
        console.log("Registering socket io bindings for ReplaceWithEDRAsset")
        var self = this;
    }

    on_replace_with_edr_asset(event, id) {
        let asset_list = [id];
        let clicked_asset = find_layer_by_id(active_layer_id, 'esdl_layer', id);
        let asset_class = clicked_asset.type;

        if (select_assets.is_select_mode()) {
            // One or more assets have been selected
            if (select_assets.is_selected(clicked_asset)) {
                // the current asset is part of this selection
                asset_list = select_assets.get_selected_assets();
            }
        }
        replace_with_edr_asset(asset_list, asset_class);
    }

    static create(event) {
        if (event.type === 'client_connected') {
            replace_with_edr_plugin = new ReplaceWithEDRAsset();
            console.log("ReplaceWithEDRAsset initiated!!")
        }
        if (event.type === 'add_contextmenu') {
            let layer = event.layer;
            let layer_type = event.layer_type;
            let id = layer.id;
            if (layer_type === 'marker' || layer_type === 'line') {
                layer.options.contextmenuItems.push({
                    text: 'Replace with asset from EDR',
                    icon: resource_uri + 'icons/edr3.png',
                    callback: function(e) {
                        replace_with_edr_plugin.on_replace_with_edr_asset(e, id);
                    }
                });
            }
        }
    }
}

var replace_with_edr_plugin;

$(document).ready(function() {
    extensions.push(function(event) { return ReplaceWithEDRAsset.create(event) });
});