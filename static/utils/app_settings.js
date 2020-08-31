/**
 *  This work is based on original code developed and copyrighted by TNO 2020.
 *  Subsequent contributions are licensed to you by the developers of such code and are
 *  made available to the Project under one or several contributor license agreements.
 *
 *  This work is licensed to you under the Apache License, Version 2.0.
 *  You may obtain a copy of the license at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Contributors:
 *      TNO         - Initial implementation
 *  Manager:
 *      TNO
 */

 // Application settings
// requires:
// dialog, map and socketio as global variables

class AppSettings {
    constructor() {
        this.initSocketIO();

        let width = map.getSize();
        this.width = 1200;
        this.height = 750;
        this.x = 10;
        this.y = (width.x/2)-(this.width/2);

        this.modules_settings_list = this.get_modules_settings_list();
    }

    initSocketIO() {
        console.log("Registering socket io bindings for AppSettings");

        socket.on('tmp', function(data) {
            console.log(data);
        });
    }

    get_modules_settings_list() {
        let modules_settings_list = [];
        for (let i=0; i<extensions.length; i++) {
            let extensions_function = extensions[i];
            let res = extensions_function({type: 'settings_menu_items'});
            if (res) modules_settings_list.push(res);
        }
        console.log(modules_settings_list);
        return modules_settings_list;
    }

    generate_content() {
        let $main_div = $('<div>').addClass('settings_window');
        let $modules_list_div = $('<div>').addClass('settings_modules_list');
        let $module_content_div = $('<div>').addClass('settings_module_content').attr('id', 'settings_module_contents');
        $main_div.append($modules_list_div).append($module_content_div);
        this.generate_settings_modules_list($modules_list_div);
        return $main_div;
    }

    construct_tree_data() {
        let menu_item_list = [];

        for (let i=0; i<this.modules_settings_list.length; i++) {
            let item = {
                id : this.modules_settings_list[i].value,
                text: this.modules_settings_list[i].text,
                icon: "",
                type: "",
                data: {},
                state: {
                    opened : true
                },
                children: [],
                li_attr: {},
                a_attr: {}
            }

            if (this.modules_settings_list[i].sub_menu_items.length > 0) {
                for (let j=0; j<this.modules_settings_list[i].sub_menu_items.length; j++) {
                    let sub_item = {
                        id : this.modules_settings_list[i].sub_menu_items[j].value,
                        text: this.modules_settings_list[i].sub_menu_items[j].text,
                        icon: "",
                        type: "",
                        data: {},
                        state: {},
                        children: [],
                        li_attr: {},
                        a_attr: {}
                    }
                    item.children.push(sub_item);
                }
            }

            menu_item_list.push(item);
        }

        return menu_item_list;
    }

    find_function_to_call(lst, id) {
        for (let i=0; i<lst.length; i++) {
            if (lst[i].value == id) {
                return lst[i].settings_func;
            }
            if (lst[i].sub_menu_items.length > 0) {
                let ret = this.find_function_to_call(lst[i].sub_menu_items, id);
                if (ret) return ret;
            }
        }
        return null
    }

    init_tree() {
        $('#settings_list_jstree')
            .jstree({
                'core' : {
                    'multiple': false,
                    'data' : this.construct_tree_data()
                }
            })
            .on('select_node.jstree', function (e, data) {
                let $div = $('#settings_module_contents');
                $div.empty();
                if (data.node) {
                    let func = app_settings.find_function_to_call(app_settings.modules_settings_list, data.node.id);
                    if (func) {
                        $div.append(func());
                    }
                }
            });
    }

    generate_settings_modules_list(list_div) {
        let $settings_list_jstree = $('<div>').attr("id", "settings_list_jstree");
        list_div.append($settings_list_jstree);
    }

    open_window() {
        let jqueryNode = this.generate_content();

        if (dialog === undefined) {
            console.log("ERROR: dialog not defined")
            // create dialog
            return;
        }
        dialog.setContent(jqueryNode.get(0));
        this.init_tree();

        dialog.setSize([app_settings.width, app_settings.height]);
        dialog.setLocation([app_settings.x, app_settings.y]);
        dialog.setTitle('Application Settings');
        $('.leaflet-control-dialog-contents').scrollTop(0);
        dialog.open();
    }

    // all globals in here
    static handle_dialog_resize_move() {
        app_settings.width = dialog.options.size[0];
        app_settings.height = dialog.options.size[1];
        app_settings.x = dialog.options.anchor[0];
        app_settings.y = dialog.options.anchor[1];
    }

    static create(event) {
        if (event.type === 'client_connected') {
            app_settings = new AppSettings();
            map.on('dialog:resizeend', AppSettings.handle_dialog_resize_move);
            map.on('dialog:moving', AppSettings.handle_dialog_resize_move);
            map.on('dialog:closed', function(e) {
                socket.emit('app_settings_closed');
            });
            return app_settings;
        }
    }
}

var app_settings; // global app_settings variable
$(document).ready(function() {
    extensions.push(function(event) { AppSettings.create(event) });
});