import {h} from 'vue';
import {mountApp} from '@/mounts';
import MapObjectPopup from '@/apps/MapObjectPopup.vue';

let activePopup = null;

/** Bind a read-only hover popup. */
export function bindMapObjectPopup(layer, getObjectInfo) {
    let popup = null;
    let closeTimer = null;

    function cancelClose() {
        clearTimeout(closeTimer);
    }

    function closePopup() {
        cancelClose();
        if (popup) {
            popup.remove();
        }
    }

    function scheduleClose() {
        cancelClose();
        // Allow the pointer to cross from the feature into the popup.
        closeTimer = setTimeout(closePopup, 250);
    }

    function openPopup(event) {
        cancelClose();
        if (popup || window.editing_objects || window.deleting_objects) {
            return;
        }
        const map = layer._map;
        if (map.contextmenu?.isVisible()) {
            return;
        }
        // Keep only one hover popup open across all map layers.
        if (activePopup) {
            activePopup.remove();
        }

        const content = document.createElement('div');
        popup = window.L.popup({
            className: 'map-object-hover-popup',
            autoPan: false,
            closeButton: false,
            minWidth: Math.min(320, map.getSize().x - 40),
            maxWidth: 360,
        }).setLatLng(event.latlng).setContent(content);
        activePopup = popup;
        popup.openOn(map);
        window.L.DomEvent.disableClickPropagation(content);
        window.L.DomEvent.disableScrollPropagation(content);

        function updatePopupPosition() {
            if (!popup) {
                return;
            }
            popup.update();
            // Keep the popup inside the map without panning.
            const bounds = popup.getElement().getBoundingClientRect();
            const mapBounds = map.getContainer().getBoundingClientRect();
            let x = 0;
            let y = 0;
            if (bounds.left < mapBounds.left) {
                x = mapBounds.left - bounds.left;
            } else if (bounds.right > mapBounds.right) {
                x = mapBounds.right - bounds.right;
            }
            if (bounds.top < mapBounds.top) {
                y = mapBounds.top - bounds.top;
            } else if (bounds.bottom > mapBounds.bottom) {
                y = mapBounds.bottom - bounds.bottom;
            }
            if (x || y) {
                const point = map.latLngToContainerPoint(popup.getLatLng()).add([x, y]);
                popup.setLatLng(map.containerPointToLatLng(point));
            }
        }

        const [app] = mountApp({
            render: () => h(MapObjectPopup, {objectInfo: getObjectInfo(), onResize: updatePopupPosition}),
        }, content);
        const element = popup.getElement();
        element.addEventListener('mouseenter', cancelClose);
        element.addEventListener('mouseleave', scheduleClose);
        map.on('movestart zoomstart', closePopup);
        popup.on('remove', () => {
            // Release the Vue component and map listeners with the popup.
            cancelClose();
            map.off('movestart zoomstart', closePopup);
            app.unmount();
            if (activePopup === popup) {
                activePopup = null;
            }
            popup = null;
        });
        updatePopupPosition();
    }

    layer.on('mouseover', openPopup);
    layer.on('mouseout', scheduleClose);
    layer.on('click contextmenu remove', closePopup);
}
