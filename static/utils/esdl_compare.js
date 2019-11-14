
function compare_esdl() {
    esdl_1 = document.getElementById('esdl_select_1').options[document.getElementById('esdl_select_1').selectedIndex].id;
    esdl_2 = document.getElementById('esdl_select_2').options[document.getElementById('esdl_select_2').selectedIndex].id;

    document.getElementById('esdl_compare_button').style.display = 'none';
    socket.emit('command', {cmd: 'compare_esdls', esdl1: esdl_1, esdl2: esdl_2});
}

function process_compare_results(results) {
    compare_results_div = document.getElementById('compare_results_div');

    // hide_loader();
}

function compare_esdl_window(esdl_list) {
    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>Compare ESDL</h1>';

    if (esdl_list) {
        sidebar_ctr.innerHTML += '<h3>Select first energysystem:</h3>';

        select = '<select id="esdl_select_1" style="width: 300px;">';
        for (i=0; i<esdl_list.length; i++) {
            // id, name
            select += '<option value="' + esdl_list[i]['id'] +
                '">' + esdl_list[i]['title'] + '</option>';
        }
        select += '</select>';
        sidebar_ctr.innerHTML += select;

        sidebar_ctr.innerHTML += '<h3>Select second energysystem:</h3>';

        select = '<select id="esdl_select_2" style="width: 300px;">';
        for (i=0; i<esdl_list.length; i++) {
            // id, name
            select += '<option value="' + esdl_list[i]['id'] +
                '">' + esdl_list[i]['title'] + '</option>';
        }
        select += '</select>';
        sidebar_ctr.innerHTML += select;
        sidebar_ctr.innerHTML += '<button id="esdl_compare_button" onclick="compare_esdl();">Compare</button>';
    } else {
        sidebar_ctr.innerHTML += 'No ESDLs found!';
        sidebar_ctr.innerHTML += '<button id="esdl_compare_close_button" onclick="sidebar.hide();">Close</button>';
    }

    sidebar_ctr.innerHTML += '<div id="compare_results_div"></div>';

    sidebar.show();
}