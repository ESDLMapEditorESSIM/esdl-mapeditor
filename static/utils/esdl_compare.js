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

// ESDL Browser
// requires:
// dialog, map and socketio as global variables

class ESDLCompare {
    constructor() {
        this.initSocketIO();
        this.history = [];

        let width = map.getSize()
        this.width = 1200;
        this.height = 750;
        this.x = 10;
        this.y = (width.x/2)-(this.width/2);
    }

    open_window() {
    //        socket.emit();

        let data = '';
        let content = this.generateContent(data);

        if (dialog === undefined) {
            console.log("ERROR: dialog not defined")
            // create dialog
            return;
        }
        //dialog.setSize([800,500]);
        //let width = map.getSize();
        //dialog.setLocation([10, (width.x/2)-(800/2)]);
        dialog.setContent(content);
        dialog.setSize([esdl_compare_window.width, esdl_compare_window.height]);
        dialog.setLocation([esdl_compare_window.x, esdl_compare_window.y]);
        dialog.setTitle('ESDL compare results');
        $('.leaflet-control-dialog-contents').scrollTop(0);
        dialog.open();
    }

    generateContent(data) {
        return "<div>Test</div>";
    }

    initSocketIO() {
        console.log("Registering socket io bindings for ESDLCompare")

        socket.on('esdl_compare_window', function(data) {
            //console.log("ESDL_Brower: browse_to SocketIO call");
            console.log(data);

//            let content = ESDLCompare.generateContent(data);
            let content = '<table>';
            for (let i=0; i<data.length; i++) {
                content += '<tr><td>'+data[i][0]+'</td><td>'+data[i][1]+'</td><td>'+data[i][2]+'</td></tr>';
            }
            content += '</table>';

            if (dialog === undefined) {
                console.log("ERROR: dialog not defined");
                // create dialog
                return;
            }
            //dialog.setSize([800,500]);
            //let width = map.getSize();
            //dialog.setLocation([10, (width.x/2)-(800/2)]);
            dialog.setContent(content);
            dialog.setSize([esdl_compare_window.width, esdl_compare_window.height]);
            dialog.setLocation([esdl_compare_window.x, esdl_compare_window.y]);
            dialog.setTitle('ESDL compare results');
            $('.leaflet-control-dialog-contents').scrollTop(0);
            dialog.open();
        });
    }

    // all globals in here
    static handle_dialog_resize_move() {
        esdl_compare_window.width = dialog.options.size[0];
        esdl_compare_window.height = dialog.options.size[1];
        esdl_compare_window.x = dialog.options.anchor[0];
        esdl_compare_window.y = dialog.options.anchor[1];
    }

    static create(event) {
        if (event.type === 'client_connected') {
            esdl_compare_window = new ESDLCompare();
            map.on('dialog:resizeend', ESDLCompare.handle_dialog_resize_move);
            map.on('dialog:moving', ESDLCompare.handle_dialog_resize_move);
            map.on('dialog:closed', function(e) {
                // socket.emit('esdl_compare_closed');
                console.log('ESDL compare window closed');
            });
            return esdl_compare_window;
        }
    }
}

var esdl_compare_window; // global esdl_compare_window variable

$(document).ready(function() {
    extensions.push(function(event) { ESDLCompare.create(event) });
});

function compare_esdl() {
    esdl_1 = document.getElementById('esdl_select_1').options[document.getElementById('esdl_select_1').selectedIndex].value;
    esdl_2 = document.getElementById('esdl_select_2').options[document.getElementById('esdl_select_2').selectedIndex].value;

    document.getElementById('esdl_compare_button').style.display = 'none';
    socket.emit('esdl_compare', {esdl1: esdl_1, esdl2: esdl_2});
//    socket.emit('esdl_compare', esdl_1, esdl_2);
}

function process_compare_results(results) {
    compare_results_div = document.getElementById('compare_results_div');

    // hide_loader();
}

function compare_esdl_window() {
    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>Compare ESDL</h1>';

    if (esdl_list) {
        sidebar_ctr.innerHTML += '<h3>Select first energysystem:</h3>';

        select = '<select id="esdl_select_1" style="width: 300px;">';

        for (let id in esdl_list) {
            es = esdl_list[id];
            select += '<option value="' + id +
                '">' + es['title'] + '</option>';
        }
        select += '</select>';
        sidebar_ctr.innerHTML += select;

        sidebar_ctr.innerHTML += '<h3>Select second energysystem:</h3>';

        select = '<select id="esdl_select_2" style="width: 300px;">';
        for (let id in esdl_list) {
            es = esdl_list[id];
            select += '<option value="' + id +
                '">' + es['title'] + '</option>';
        }
        select += '</select>';
        sidebar_ctr.innerHTML += select;
        sidebar_ctr.innerHTML += '<p><button id="esdl_compare_button" onclick="sidebar.hide();compare_esdl();">Compare</button></p>';
    } else {
        sidebar_ctr.innerHTML += 'No ESDLs found!';
        sidebar_ctr.innerHTML += '<button id="esdl_compare_close_button" onclick="sidebar.hide();">Close</button>';
    }

    sidebar_ctr.innerHTML += '<div id="compare_results_div"></div>';

    sidebar.show();
}