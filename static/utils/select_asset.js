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


class SelectAssets {
    constructor() {
        this.select_mode = false;
        this.selected_assets = [];
    }

    deselect_all_assets() {
        while (this.selected_assets.length) {
            let asset_id = this.selected_assets[0];
            let asset_leaflet_obj = find_layer_by_id(active_layer_id, 'esdl_layer', asset_id);
            if (asset_leaflet_obj === undefined) {
                // make sure we don't end up in an endless loop...
                this.selected_assets.splice(this.selected_assets.indexOf(asset_id), 1);
            } else {
                this.toggle_selected(asset_leaflet_obj);
                this.enable_context_menu_items(asset_leaflet_obj);
            }
        }
        this.select_mode = false;
    }

    add_map_handler(map) {
        map.on('click', function(e) {
            if (!e.originalEvent.shiftKey) { // box select uses Shift to do selection
                select_assets.deselect_all_assets();
                select_assets.select_mode = false;
            }
        });
    }

    is_select_mode() {
        return (this.selected_assets.length > 0);
    }

    is_selected(asset_leaflet_obj) {
        return asset_leaflet_obj.selected;
    }

    get_selected_assets() {
        return this.selected_assets;
    }

    add_to_selected_list(asset_leaflet_obj) {
        this.selected_assets.push(asset_leaflet_obj.id);
        // filter out duplicates as the current approach might fail in some corner cases
        this.selected_assets = this.selected_assets.filter((v, i, a) => a.indexOf(v) === i);
        //this.disable_context_menu_items(asset_leaflet_obj);

        // only disable contect menu when more than 1 is selected
        if (this.selected_assets.length == 2) {
            this.disable_context_menu_items(find_layer_by_id(active_layer_id, 'esdl_layer', this.selected_assets[0]))
            this.disable_context_menu_items(asset_leaflet_obj);
        } else if (this.selected_assets.length > 2) {
            this.disable_context_menu_items(asset_leaflet_obj);
        }
    }

    remove_from_selected_list(asset_leaflet_obj) {
        let index = this.selected_assets.indexOf(asset_leaflet_obj.id)
        this.selected_assets.splice(index, 1);
        if (this.selected_assets.length == 0)
            this.select_mode = false;
        this.enable_context_menu_items(asset_leaflet_obj);
    }

    toggle_selected(asset_leaflet_obj) {
        //console.log("asset was selected: ", asset_leaflet_obj.name, asset_leaflet_obj.selected);
        if (!asset_leaflet_obj.selected) {
            this.select_mode = true;
            asset_leaflet_obj.selected = true;
            this.add_to_selected_list(asset_leaflet_obj);
        } else {
            asset_leaflet_obj.selected = false;
            this.remove_from_selected_list(asset_leaflet_obj);
        }
        // console.log("asset is now selected: ", asset_leaflet_obj.selected);
        if (asset_leaflet_obj instanceof L.Marker) {
            let cll = asset_leaflet_obj.getElement().classList;
            cll.toggle('Selected');
        }
        if (asset_leaflet_obj instanceof L.Polyline) {
            update_line_color(asset_leaflet_obj); // from assets.js
//            if (asset_leaflet_obj.selected) {
//                //asset_leaflet_obj.options.orig_color = asset_leaflet_obj.options.color;
//                asset_leaflet_obj.setStyle({
//                    color: "white",
//                    dashArray: "5,10"
//                });
//                //asset_leaflet_obj.color = "#ffffff";
//            } else {
//                //asset_leaflet_obj.setStyle({
//                //    color: asset_leaflet_obj.options.orig_color,
//                //    dashArray: ""
//                //});
//                //asset_leaflet_obj.color = asset_leaflet_obj.options.orig_color;
//                //delete asset_leaflet_obj.options.orig_color;
//                // from assets.js
//            }
        }
    }

    add_asset_handler(asset_leaflet_obj) {
        asset_leaflet_obj.on('click', function(e) {
            if (e.originalEvent.ctrlKey || e.originalEvent.metaKey) {
                console.log("Asset ctrl-clicked!")
                select_assets.select_mode = true;
                select_assets.toggle_selected(e.target);

                // stop propagation, else map will also receive click event
                L.DomEvent.stopPropagation(e);
            }
        });
    }

    enable_context_menu_items(asset_leaflet_obj) {
        for (let i=0; i<asset_leaflet_obj.options.contextmenuItems.length; i++) {
            let option = asset_leaflet_obj.options.contextmenuItems[i];
            if (option != '-')
                option['disabled'] = false;
        }
    }

    disable_context_menu_items(asset_leaflet_obj) {
        for (let i=0; i<asset_leaflet_obj.options.contextmenuItems.length; i++) {
            let option = asset_leaflet_obj.options.contextmenuItems[i];
            if ((option != '-') && (option.text != 'Delete'))
                option['disabled'] = true;
        }
    }

}

var select_assets = new SelectAssets()

// -----------------------------
//  BoxSelectAssets
// -----------------------------

L.Map.BoxSelectAssets = L.Map.BoxZoom.extend({

    _onMouseUp: function (e) {
        if ((e.which !== 1) && (e.button !== 1)) { return; }

        this._finish();

        if (!this._moved) { return; }
        // Postpone to next JS tick so internal click event handling
        // still see it as "moved".
        setTimeout(L.bind(this._resetState, this), 0);
        var bounds = new L.LatLngBounds(
            this._map.containerPointToLatLng(this._startPoint),
            this._map.containerPointToLatLng(this._point)
        );

    		//this._map.fitBounds(bounds).fire('boxzoomend', {boxZoomBounds: bounds});
        let contains = true;    // if false then use intersects
        if (this._point.x < this._startPoint.x)
            contains = false;

        let esdl_objects = get_layers(active_layer_id, 'esdl_layer').getLayers();
        for (let i=0; i<esdl_objects.length; i++) {
            let esdl_object = esdl_objects[i];

            if (esdl_object instanceof L.Marker) {
                if (bounds.contains(esdl_object.getLatLng())) {
                    select_assets.toggle_selected(esdl_object);
                }
            } else {
                if (contains) {
                    if (bounds.contains(esdl_object.getLatLngs())) {
                        select_assets.toggle_selected(esdl_object);
                    }
                } else {
                    if (bounds.intersects(esdl_object.getLatLngs())) {
                        select_assets.toggle_selected(esdl_object);
                    }
                }
            }
        }
    }

});

L.Map.mergeOptions({boxZoom: false});
L.Map.mergeOptions({boxSelectAssets: true});
L.Map.addInitHook('addHandler', 'boxSelectAssets', L.Map.BoxSelectAssets);
