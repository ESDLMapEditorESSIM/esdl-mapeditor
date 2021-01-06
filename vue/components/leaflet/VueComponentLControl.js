import { createApp } from "vue"

const VueComponentLControl = window.L.Control.extend({
    options: {
        position: 'bottomleft',
    },

    onAdd: function () {
        let container = window.L.DomUtil.create('div', `vue_control`);

        // Make sure w/e don't drag the map when we interact with the content
        let stop = window.L.DomEvent.stopPropagation;
        let fakeStop = window.L.DomEvent._fakeStop || stop;
        window.L.DomEvent
            .on(container, 'contextmenu', stop)
            .on(container, 'click', fakeStop)
            .on(container, 'mousedown', stop)
            .on(container, 'touchstart', stop)
            .on(container, 'dblclick', fakeStop)
            .on(container, 'mousewheel', stop)
            .on(container, 'MozMousePixelScroll', stop);

        return container;
    },

    onRemove: function () {
        console.log('VueComponentLControl.onRemove()')
    },

    mount: function (component) {
        createApp(component).mount(this.getContainer());
    }
});

export default VueComponentLControl;
