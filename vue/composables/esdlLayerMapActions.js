export function useEsdlLayerMapActions() {
    function showEsdlLayerOnMap(es_id, layer_name, parent_esdl_layer) {
        window.show_esdl_layer_on_map(es_id, layer_name, parent_esdl_layer);
        window.set_leaflet_sizes();
    }

    function hideEsdlLayerFromMap(es_id, layer_name, parent_esdl_layer) {
        window.hide_esdl_layer_from_map(es_id, layer_name, parent_esdl_layer);
    }

    return {
        hideEsdlLayerFromMap,
        showEsdlLayerOnMap,
    };
}
