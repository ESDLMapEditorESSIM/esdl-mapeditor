/**
 * Mounting functions, to mount Vue components somewhere in the MapEditor.
 */
import {createApp} from "vue"
import VueComponentLControl from './components/leaflet/VueComponentLControl'
import VueGridLayout from 'vue-grid-layout'
// Import everything.
// import Antd from 'ant-design-vue';
// import 'ant-design-vue/dist/antd.min.css';
// Import subset.
import {
    Breadcrumb,
    Button,
    Card,
    Checkbox,
    Col,
    Collapse,
    DatePicker,
    Divider,
    Dropdown,
    Form,
    Input,
    InputNumber,
    Menu,
    Modal,
    Radio,
    Row,
    Select,
    Space,
    Spin,
    Switch,
    Table,
    Tag,
    Transfer,
    Tree,
    Upload
} from 'ant-design-vue';

export function mountSidebarComponent(component) {
    let sidebar_ctr = window.sidebar.getContainer();
    sidebar_ctr.innerHTML = '<div id="vue_sidebar_app"></div>';
    window.sidebar.show();
    mountApp(component, '#vue_sidebar_app');
}

export function mountSettingsComponent(component) {
    let settings_div = document.getElementById('settings_module_contents');
    settings_div.innerHTML = '<div id="mount_settings_component_div"></div>';
    mountApp(component, '#mount_settings_component_div');
}

export function createVueLControl(component, options) {
    const lcontrol = new VueComponentLControl(options);
    lcontrol.addTo(window.map).mount(component);
}

export function mountTooltipComponent(component) {
    mountApp(component, '#tooltip_contents_div');
}

export function mountApp(component, elementSelector) {
    const app = createApp(component)

    // Components from ant-design-vue
    app.use(Breadcrumb);
    app.use(Button);
    app.use(Card);
    app.use(Checkbox);
    app.use(Col);
    app.use(Collapse);
    app.use(DatePicker);
    app.use(Divider);
    app.use(Dropdown);
    app.use(Form);
    app.use(Input);
    app.use(InputNumber);
    app.use(Menu);
    app.use(Modal);
    app.use(Radio);
    app.use(Row);
    app.use(Select);
    app.use(Space);
    app.use(Spin);
    app.use(Switch);
    app.use(Table);
    app.use(Tag);
    app.use(Transfer);
    app.use(Tree);
    app.use(Upload);
    app.use(VueGridLayout);

    app.mount(elementSelector);
}
