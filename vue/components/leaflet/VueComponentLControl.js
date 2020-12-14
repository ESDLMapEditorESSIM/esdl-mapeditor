import { createApp } from "vue"

const VueComponentLControl = window.L.Control.extend({
    options: {
        position: 'bottomleft',
    },

    onAdd: function () {
        return window.L.DomUtil.create('div', `vue_control`);
    },

    onRemove: function () {
        console.log('VueComponentLControl.onRemove()')
    },

    mount: function (component) {
        createApp(component).mount(this.getContainer());
    }
});

export default VueComponentLControl;
