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


var edr_asset_list;

function get_edr_assets(url) {
    $.ajax({
        url: url,
        success: function(data){
            edr_asset_list = data["asset_list"];
        },
        dataType: "json"
    });
}

function select_edr_asset() {
    var select_box = document.getElementById("edr_asset_select");
    var selected_value = select_box.options[select_box.selectedIndex].value;
    sidebar.hide();

    socket.emit('command', {cmd: 'get_edr_asset', edr_asset_id: selected_value});
}

function select_edr_asset_window(url) {
    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>EDR assets:</h1>';

    if (edr_asset_list) {
        var size;
        if (edr_asset_list.length < 15) { size = 15; } else { size = edr_asset_list.length; }
        select = '<select id="edr_asset_select" size="'+size+'" onchange="select_edr_asset();" style="width: 300px;">';
        for (i=0; i<edr_asset_list.length; i++) {
            // id, name
            select += '<option value="' + edr_asset_list[i]['id'] +
                '">' + edr_asset_list[i]['title'] + '</option>';
        }
        select += '</select>';
        sidebar_ctr.innerHTML += select;
    } else {
        sidebar_ctr.innerHTML += 'No assets found in EDR';
    }

    sidebar.show();
}
