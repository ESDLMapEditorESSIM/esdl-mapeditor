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
        this.generate_settings_modules_contents($module_content_div);

        return $main_div;
    }

    generate_settings_modules_list(list_div) {
        let $select = $('<select>').attr('id','select_module').attr('size', 10);
        for (let i = 0; i < this.modules_settings_list.length; i++) {
            let $option = $('<option>')
                .attr('value', this.modules_settings_list[i].value)
                .text(this.modules_settings_list[i].text);
            $select.append($option);
        }

        $select.change(function() {app_settings.generate_settings_modules_contents();});

        list_div.append($select);
    }

    generate_settings_modules_contents() {
        let $div = $('#settings_module_contents');
        $div.empty();

        let $select = $('#select_module');
        let selected_value = $select.val();
        console.log(selected_value);

        for (let i = 0; i < this.modules_settings_list.length; i++) {
            if (this.modules_settings_list[i].value == selected_value) {
                $div.append(this.modules_settings_list[i].settings_func());
            }
        }
    }

    open_window() {
        let jqueryNode = this.generate_content();

        if (dialog === undefined) {
            console.log("ERROR: dialog not defined")
            // create dialog
            return;
        }
        dialog.setContent(jqueryNode.get(0));
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