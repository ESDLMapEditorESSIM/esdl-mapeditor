const map = window.map;
const L = window.L;

const layersPopup = L.popup({
    autoPan: true,
    maxWidth: 400,
    maxHeight: 400
});

export function useServiceLayerFeaturePopup() {
    /**
     * Show the map popup of WMS or WFS layers features properties
     *
     * @param {Object} latlng a latlng object {lat: number, lng: number} for adding the popup.
     * @param {Array} layersFeatures an array of layer feature objects with structure { name: str, feature_props: Object | null }
     */
    function showServiceLayerFeaturePopup(latlng, layersFeatures) {
        if (layersFeatures.length === 0) {
            return;
        }

        const popupDivId = "layer-feature-popup-node";
        // Check if the popup already exists and removes it
        const existingPopupDiv = document.getElementById(popupDivId);
        if (existingPopupDiv) {
            existingPopupDiv.remove();
        }
        const popupDiv = document.createElement("div");
        popupDiv.setAttribute("id", popupDivId);
        popupDiv.classList.add("layer-feature-props-popup");

        // Updating the popup content
        layersFeatures.forEach((l) => {
            const layerName = l.name;
            const layerFeatureProps = l.feature_props;

            // Layer name node
            const layerNameNode = document.createElement("h4");
            layerNameNode.innerHTML = `${layerName}`;
            popupDiv.appendChild(layerNameNode);

            if (layerFeatureProps !== null) {
                if (Object.keys(layerFeatureProps).length) {
                    // Layer feature properties node
                    Object.keys(layerFeatureProps).forEach((pName) => {
                        const propNameNode = document.createElement("p");
                        const propValueNode = document.createElement("span");
                        propNameNode.innerHTML = `${pName}: `;
                        propValueNode.innerHTML = `${layerFeatureProps[pName]}`;
                        popupDiv.appendChild(propNameNode).appendChild(propValueNode);
                    });
                } else {
                    // If the event location has no feature, remove the layerNameNode from the popup
                    popupDiv.removeChild(layerNameNode);
                }
            } else {
                console.warn(`${layerName} has null props. An error occurred while fetching ${layerName} layer feature properties.`);
                const propErrorNode = document.createElement("p");
                propErrorNode.innerHTML = `An error occurred while fetching ${layerName} layer feature properties`;
                popupDiv.appendChild(propErrorNode);
            }
        });

        if (popupDiv.hasChildNodes()) {
            // Set the popup content and open it
            layersPopup.setLatLng(latlng).setContent(popupDiv);
            map.openPopup(layersPopup);
        }
    }

    return {
        showServiceLayerFeaturePopup,
    };
}
