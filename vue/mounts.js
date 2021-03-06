/**
 * Mounting functions, to mount Vue components somewhere in the MapEditor.
 */
import { createApp } from "vue"
import VueComponentLControl from './components/leaflet/VueComponentLControl'
// Import everything.
// import Antd from 'ant-design-vue';
// import 'ant-design-vue/dist/antd.min.css';
// Import subset.
import { Button, Card, Collapse, DatePicker, Dropdown, Input, Form, Modal, Select, Space, Table, Tree, Upload, Row, Col, InputNumber, Radio, Switch, Divider } from 'ant-design-vue';

export function mountSidebarComponent(component) {
    let sidebar_ctr = window.sidebar.getContainer();
    sidebar_ctr.innerHTML = '<div id="vue_sidebar_app"></div';
    window.sidebar.show();
    mountApp(component, '#vue_sidebar_app');
}

export function createVueLControl(component, options) {
    const lcontrol = new VueComponentLControl(options);
    lcontrol.addTo(window.map).mount(component);
}

export function mountApp(component, elementSelector) {
    const app = createApp(component)
    // app.use(Antd);
    // app.use(Badge);
    app.use(Button);
    app.use(Card);
    app.use(Radio);
    app.use(Collapse);
    app.use(DatePicker);
    app.use(Dropdown);
    app.use(Input);
    app.use(InputNumber);
    app.use(Form);
    app.use(Modal);
    app.use(Select);
    app.use(Space);
    app.use(Table);
    app.use(Col);
    app.use(Row);
    app.use(Switch);
    app.use(Tree);
    app.use(Upload);
    app.use(Row);
    app.use(Col);
    app.use(Divider);
    app.mount(elementSelector);
}
