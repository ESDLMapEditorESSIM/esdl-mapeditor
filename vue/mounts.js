/**
 * Mounting functions, to mount Vue components somewhere in the MapEditor.
 */
import { createApp } from "vue"
import VueComponentLControl from './components/leaflet/VueComponentLControl'
import Antd from 'ant-design-vue';
import 'ant-design-vue/dist/antd.css';


export function mountSidebarComponent(component) {
    let sidebar_ctr = window.sidebar.getContainer();
    sidebar_ctr.innerHTML = '<div id="vue_sidebar_app"></div';
    window.sidebar.show();
    mountApp(component, '#vue_sidebar_app');
}

export function createVueLControl(component) {
    const simulation_control = new VueComponentLControl();
    simulation_control.addTo(window.map).mount(component);
}

export function mountApp(component, elementSelector) {
    const app = createApp(component)
    app.use(Antd);
    app.mount(elementSelector);
}
