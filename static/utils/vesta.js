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

class Vesta {
    constructor() {
        this.restrictions_list = [];
        this.measures_list = [];

        this.current_measures = null;
        this.current_area_id = null;

        this.initSocketIO();
    }

    initSocketIO() {
        console.log("Registering socket io bindings for Vesta plugin")

        socket.on('vesta_restrictions_data', function(vesta_data) {
//            console.log(vesta_data);

            vesta_plugin.current_measures = vesta_data['current_measures'];
            vesta_plugin.current_area_id = vesta_data['area_id'];

            sidebar.setContent(vesta_plugin.create_vesta_sidebar_content(vesta_data).get(0));
            sidebar.show();
            vesta_plugin.load_measures();
        });

        this.get_vesta_restrictions_list();
    }

    get_vesta_restrictions_list() {
        console.log('http get /vesta_restrictions');
        $.ajax({
            url: resource_uri + '/vesta_restrictions',
            success: function(data){
                for (let i=0; i<data.length; i++) {
                    vesta_plugin.restrictions_list.push({id: data[i]["id"], title: data[i]["title"]});
                }
            }
        });
    }

    create_vesta_sidebar_content(data) {
        let $div = $('<div>').attr('id', 'vesta-main-div');
        let $title = $('<h1>').text('VESTA');
        $div.append($title);

        let $select_div = $('<div>').addClass('sidebar-div');
        let $select = $('<select>').attr('id', 'select_restrictions_list');
        this.create_restrictions_list_select($select);
        $select.change(function() { vesta_plugin.load_measures(); });
        $select_div.append($select);
        $div.append($select_div);

        let $measures_div = $('<div>').attr('id', 'measures_div').addClass('sidebar-div');
        $measures_div.append($('<p>').text('Please select your restrictions for ' + data["area_id"]));
        let $measures_p = $('<p>').attr('id', 'measures_p');
        let $measures_button_p = $('<p>').attr('id', 'measures_button_p');
        $measures_div.append($measures_p).append($measures_button_p);
        $div.append($measures_div);

        return $div;
    }

    create_restrictions_list_select($select) {
        for (let i=0; i<this.restrictions_list.length; i++) {
            let $option = $('<option>').attr('value', this.restrictions_list[i]['id']).text(this.restrictions_list[i]['title']);
            $select.append($option);
        }
    }

    load_measures() {
        let $select = $('#select_restrictions_list');
        let selected_value = $select.val();
        console.log(selected_value);

        $.ajax({
            url: resource_uri + '/vesta_restriction/' + selected_value,
            success: function(data){
                if (data.length > 0) {
                    let $ul = $('<ul>').css('list-style-type', 'none');
                    $('#measures_p').empty().append($ul);
                    for (let i=0; i<data.length; i++) {
//                        console.log(data[i]);

                        let $li = $('<li>');
                        let $cb = $('<input>').attr('type', 'checkbox').attr('value', data[i]['id']).attr('name', 'measures');
                        for (let j=0; j<vesta_plugin.current_measures.length; j++) {
                            if (vesta_plugin.current_measures[j]['id'] ==  data[i]['id']) $cb.prop('checked', true);
                        }
                        let $label = $('<label>').attr('for', data[i]["id"]).text(data[i]["name"]);
                        $li.append($cb).append($label);
                        $ul.append($li);
                    }
                    let $button = $('<button>').attr('type', 'button').attr('id', 'id_sel_restr').attr('name', 'Select restrictions').text('Select restrictions');
                    $button.click(function(e){
                        vesta_plugin.set_area_restrictions();
                        sidebar.hide();
                    });
                    $('#measures_button_p').empty().append($button);
                }
            }
        });
    }

    area_restrictions_window(event, id) {
        socket.emit('vesta_area_restrictions', id);
    }

    set_area_restrictions(event) {
        let selected_measures = [];
        $.each($("input[name='measures']:checked"), function(){
            selected_measures.push($(this).val());
        });

        socket.emit('select_area_restrictions', {area_id: this.current_area_id, selected_measures: selected_measures});
    }

    static create(event) {
        if (event.type === 'client_connected') {
            vesta_plugin = new Vesta();
            return vesta_plugin;
        }
        if (event.type === 'add_contextmenu') {
            let layer = event.layer;
            let layer_type = event.layer_type;
            let id = layer.id;
            if (layer_type === 'area') {
                layer.options.contextmenuItems.push({
                    text: 'set VESTA restrictions',
                    icon: resource_uri + 'icons/Vesta.png',
                    callback: function(e) {
                        vesta_plugin.area_restrictions_window(e, id);
                    }
                });
            }
        }
        if (event.type === 'settings_menu_items') {
            let menu_items = {
                'value': 'vesta_plugin_settings',
                'text': 'VESTA plugin',
                'settings_func': function() { return $('<p>').text('VESTA plugin')},
                'sub_menu_items': []
            };

            return menu_items;
        }
    }
}

var vesta_plugin;   // global variable for the Vesta plugin

$(document).ready(function() {
    extensions.push(function(event) { return Vesta.create(event) });
});