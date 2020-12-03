/**
 * Mounting functions, to mount Vue components somewhere in the MapEditor.
 */
import { createApp } from "vue"
import VueComponentLControl from './components/leaflet/VueComponentLControl'
// Import everything.
// import Antd from 'ant-design-vue';
// import 'ant-design-vue/dist/antd.min.css';
// Import subset.
import { Button, Card, Collapse, DatePicker, Dropdown, Input, Form, Modal, Select, Space, Table, Tree, Upload } from 'ant-design-vue';


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
    // app.use(Antd);
    app.use(Button);
    app.use(Card);
    app.use(Collapse);
    app.use(DatePicker);
    app.use(Dropdown);
    app.use(Input);
    app.use(Form);
    app.use(Modal);
    app.use(Select);
    app.use(Space);
    app.use(Table);
    app.use(Tree);
    app.use(Upload);
    app.mount(elementSelector);
}
