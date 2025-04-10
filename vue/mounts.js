/**
 * Mounting functions, to mount Vue components somewhere in the MapEditor.
 */
import {createApp} from "vue";
import VueComponentLControl from './components/leaflet/VueComponentLControl';
import VueGridLayout from 'vue-grid-layout';
// Import everything.
// import Antd from 'ant-design-vue';
// import 'ant-design-vue/dist/antd.min.css';
// Import subset.
import {
    AutoComplete,
    Breadcrumb,
    Button,
    Card,
    Cascader,
    Checkbox,
    Col,
    Collapse,
    DatePicker,
    Divider,
    Dropdown,
    Empty,
    Form,
    Input,
    InputNumber,
    Layout,
    List,
    Menu,
    Modal,
    Popover,
    Progress,
    Radio,
    Row,
    Select,
    Segmented,
    Slider,
    Space,
    Spin,
    Switch,
    Table,
    Tabs,
    Tag,
    Tooltip,
    Transfer,
    Tree,
    TreeSelect,
    Typography,
    Upload
} from 'ant-design-vue';

let sidebar_app= null;
export function mountSidebarComponent(component) {
    if (sidebar_app !== null) {
        sidebar_app.unmount();
    }
    let sidebar_ctr = window.sidebar.getContainer();
    sidebar_ctr.innerHTML = '<div id="vue_sidebar_app"></div>';
    window.sidebar.show();
    [sidebar_app] = mountApp(component, '#vue_sidebar_app');
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

export function mountTooltipComponent(component, el_id) {
    mountApp(component, `#${el_id}`);
}

export function mountApp(component, elementSelector) {
    const app = createApp(component);

    // Components from ant-design-vue
    app.use(AutoComplete);
    app.use(Breadcrumb);
    app.use(Button);
    app.use(Card);
    app.use(Cascader);
    app.use(Checkbox);
    app.use(Col);
    app.use(Collapse);
    app.use(DatePicker);
    app.use(Divider);
    app.use(Dropdown);
    app.use(Empty);
    app.use(Form);
    app.use(Input);
    app.use(InputNumber);
    app.use(Layout);
    app.use(List);
    app.use(Menu);
    app.use(Modal);
    app.use(Popover);
    app.use(Progress);
    app.use(Radio);
    app.use(Row);
    app.use(Select);
    app.use(Segmented);
    app.use(Slider);
    app.use(Space);
    app.use(Spin);
    app.use(Switch);
    app.use(Table);
    app.use(Tabs);
    app.use(Tag);
    app.use(Tooltip);
    app.use(Transfer);
    app.use(Tree);
    app.use(TreeSelect);
    app.use(Typography);
    app.use(Upload);
    app.use(VueGridLayout);

    const componentInstance = app.mount(elementSelector);
    return [app, componentInstance];
}
