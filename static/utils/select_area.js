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


class SelectAreas {
    constructor() {
        this.select_mode = false;
        // Selected areas is a list of ESDL area IDs (so without "(1 of 3)"
        this.selected_areas = [];
    }

    /**
     * Find the Leaflet layers for a selected area.
     * @param {string} area_id
     * @returns {L.Layer|undefined}
     */
    find_selected_areas(area_id) {
        let areas_leaflet_obj = find_areas_by_id(active_layer_id, area_id);
        return areas_leaflet_obj;
    }

    deselect_all_areas() {
        while (this.selected_areas.length) {
            let area_id = this.selected_areas[0];
            let areas_leaflet_obj = this.find_selected_areas(area_id);
            if (areas_leaflet_obj === undefined) {
                // make sure we don't end up in an endless loop...
                this.selected_areas.splice(this.selected_areas.indexOf(area_id), 1);
            } else {
                // Call toggle with first element from list. toggle_selected will handle all layers
                this.toggle_selected(areas_leaflet_obj[0]);
                for (let area in areas_leaflet_obj) {
                    this.enable_context_menu_items(area);
                }
            }
        }
        this.select_mode = false;
    }

    add_map_handler(map) {
        map.on('click', function(e) {
            if (!e.originalEvent.shiftKey) { // box select uses Shift to do selection
                select_areas.deselect_all_areas();
                select_areas.select_mode = false;
            }
        });
    }

    is_select_mode() {
        return (this.selected_areas.length > 0);
    }

    is_selected(area_leaflet_obj) {
        return area_leaflet_obj.selected;
    }

    get_selected_areas() {
        return this.selected_areas;
    }

    add_to_selected_list(areas_leaflet_obj, mapeditor_area_id) {
        this.selected_areas.push(mapeditor_area_id);
        // filter out duplicates as the current approach might fail in some corner cases
        this.selected_areas = this.selected_areas.filter((v, i, a) => a.indexOf(v) === i);
        //this.disable_context_menu_items(area_leaflet_obj);

        // only disable context menu when more than 1 is selected
        if (this.selected_areas.length == 2) {
            // when the second is selected also disable the context menus of the first selected area
            let first_selected_areas = this.find_selected_areas(this.selected_areas[0]);
            if (first_selected_areas !== undefined) {
                for (let i = 0; i < first_selected_areas.length; i++) {
                    this.disable_context_menu_items(first_selected_areas[i]);
                }
            }
            // disable context menus for second area
            for (let i = 0; i < areas_leaflet_obj.length; i++) {
                this.disable_context_menu_items(areas_leaflet_obj[i]);
            }
        } else if (this.selected_areas.length > 2) {
            for (let i = 0; i < areas_leaflet_obj.length; i++) {
                this.disable_context_menu_items(areas_leaflet_obj[i]);
            }
        }

        console.log(this.selected_areas);
    }

    remove_from_selected_list(areas_leaflet_obj, mapeditor_area_id) {
        let index = this.selected_areas.indexOf(mapeditor_area_id)
        this.selected_areas.splice(index, 1);
        if (this.selected_areas.length === 0)
            this.select_mode = false;
        for (let i=0; i<areas_leaflet_obj.length; i++) {
            this.enable_context_menu_items(areas_leaflet_obj[i]);
        }
    }

    toggle_selected(area_leaflet_obj) {
        // Can be called with area ID "... (1 of 3)" or with only "..." and then it will still handle all layers
        // console.log("area was selected: ", area_leaflet_obj.name, area_leaflet_obj.selected, area_leaflet_obj);

        let area_id_without_cntr = get_area_id_from_mapeditor_id(area_leaflet_obj.id);
        let areas = find_areas_by_id(active_layer_id, area_id_without_cntr);

        if (!areas[0].selected) {
            this.select_mode = true;
            for (let i=0; i<areas.length; i++) {
                areas[i].selected = true;
            }
            this.add_to_selected_list(areas, area_id_without_cntr);
        } else {
            for (let i=0; i<areas.length; i++) {
                areas[i].selected = false;
            }
            this.remove_from_selected_list(areas, area_id_without_cntr);
        }
        // console.log("area is now selected: ", area_leaflet_obj.selected);
        for (let i=0; i<areas.length; i++) {
            if (areas[i].feature && areas[i].setStyle) {
                if (areas[i].selected) {
                    // area_leaflet_obj.selectedStyle = {
                    //     weight: area_leaflet_obj.options.weight,
                    //     color: area_leaflet_obj.options.color,
                    //     dashArray: area_leaflet_obj.options.dashArray,
                    //     fillOpacity: area_leaflet_obj.options.fillOpacity
                    // };
                    setSelectedAreaStyle(areas[i])
                    // saveStyle(area_leaflet_obj);
                // } else if (area_leaflet_obj.selectedStyle) {
                //     area_leaflet_obj.setStyle(area_leaflet_obj.selectedStyle);
                //     delete area_leaflet_obj.selectedStyle;
                // }
                } else {
                    restoreStyle(areas[i]);
                }
            }
        }

        let areas2 = find_areas_by_id(active_layer_id, area_id_without_cntr);
    }

    add_area_handler(area_leaflet_obj) {
        area_leaflet_obj.on('click', function(e) {
            // console.log("test")
            if (e.originalEvent.ctrlKey || e.originalEvent.metaKey) {
                // console.log("area ctrl-clicked!")
                select_areas.select_mode = true;
                select_areas.toggle_selected(e.target);

                // stop propagation, else map will also receive click event
                L.DomEvent.stopPropagation(e);
            }
        });
    }

    enable_context_menu_items(area_leaflet_obj) {
        for (let i=0; i<area_leaflet_obj.options.contextmenuItems.length; i++) {
            let option = area_leaflet_obj.options.contextmenuItems[i];
            if (option != '-') {
                option['disabled'] = false;
            }
        }
    }

    disable_context_menu_items(area_leaflet_obj) {
        for (let i=0; i<area_leaflet_obj.options.contextmenuItems.length; i++) {
            let option = area_leaflet_obj.options.contextmenuItems[i];
            if (option != '-' && option.text != 'Delete') {
                option['disabled'] = true;
            }

            // Support for services that can run on multiple selected areas
            let extra_options = option['extra_options'] || {};
            let multiple_areas_support = extra_options['allow_multiple'] || false;
            if (multiple_areas_support) {
                option['disabled'] = false;
            }
        }
    }

}

var select_areas = new SelectAreas()

// -----------------------------
//  BoxSelectAreas
// -----------------------------

L.Map.BoxSelectAreas = L.Map.BoxZoom.extend({

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
        let area_objects = get_layers(active_layer_id, 'area_layer').getLayers();
        for (let i=0; i<area_objects.length; i++) {
            let area_object = area_objects[i];

            if (bounds.contains(area_object.getLatLngs())) {
                select_areas.toggle_selected(area_object);
            }
        }
    }

});

L.Map.mergeOptions({boxZoom: false});
L.Map.mergeOptions({boxSelectAreas: true});
L.Map.addInitHook('addHandler', 'boxSelectAreas', L.Map.BoxSelectAreas);
