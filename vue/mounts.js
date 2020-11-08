import { createApp } from "vue"
import Antd from 'ant-design-vue';
import 'ant-design-vue/dist/antd.css';

export function mountSidebarComponent(component) {
    let sidebar_ctr = window.sidebar.getContainer();
    sidebar_ctr.innerHTML = '<div id="vue_sidebar_app"></div>';
    window.sidebar.show();
    mountApp(component, '#vue_sidebar_app');
}

export function mountApp(component, elementSelector) {
    const app = createApp(component)
    app.use(Antd);
    app.mount(elementSelector);
}
