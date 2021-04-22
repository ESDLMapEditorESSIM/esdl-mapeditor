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

ESSIM_simulation_URL_prefix = '/';
var attempt = 0;                // number of retries after an error occurs with the simulation_progress query

// ------------------------------------------------------------------------------------------------------------
//   ESSIM validation
// ------------------------------------------------------------------------------------------------------------
function validate_for_ESSIM() {
    socket.emit('command', {cmd: 'validate_for_ESSIM'});
}

function show_validate_for_ESSIM_window(results) {
    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>ESSIM Validation results:</h1>';

    table = '<table>';
    for (i=0; i<results.length; i++) {
        table += '<tr><td>' + results[i] + '</td></tr>'
    }
    table += '</table>';
    sidebar_ctr.innerHTML += table;

    sidebar_ctr.innerHTML += '<p id="button_close_validation_dialog"><button onclick="sidebar.hide();">Close</button></p>';

    sidebar.show();
}

// ------------------------------------------------------------------------------------------------------------
//   ESSIM simulation
// ------------------------------------------------------------------------------------------------------------
function set_simulation_URL_prefix(url_prefix) {
    ESSIM_simulation_URL_prefix = url_prefix;
}

function enable_disable_custom_year(id) {
    if (id === 'sim_custom_year') {
        document.getElementById('sim_start_datetime').disabled = false;
        document.getElementById('sim_end_datetime').disabled = false;
    } else {
        document.getElementById('sim_start_datetime').disabled = true;
        document.getElementById('sim_end_datetime').disabled = true;
    }
}

function set_simulation_id(sim_id) {
    console.log('set_simulation_id: '+sim_id);
    socket.emit('essim_set_simulation_id', sim_id);
}

function remove_sim_fav(sim_fav, sim_id) {
    $.ajax({
        url: ESSIM_simulation_URL_prefix + sim_fav + '/' + sim_id,
        type: 'DELETE',
        success: function(data){
            // Remove simulation / favorite from table
            $('#'+sim_id).remove();
        }
    });
}

function show_kpis(sim_id, sim_fav) {
//    socket.emit('essim_set_simulation_id', sim_id);
    socket.emit('show_previous_sim_kpis', { sim_id: sim_id, sim_fav: sim_fav });
}

function favorite_simulation(sim_id) {
    $.ajax({
        url: ESSIM_simulation_URL_prefix + 'simulation/' + sim_id + '/make_favorite',
        success: function(data){
            // Move simulation to favoritess
            let $tr = $('#'+sim_id).remove().clone();
            $tr.find('.favorite_button').remove();
            $tr.find('.remove_button').off('click').click( function(e) { remove_sim_fav('favorite', sim_id); });
            $('#fav_list tbody').append($tr);
        }
    });
}

function show_favorites_list(div_id) {
    // console.log('retreiving ESSIM simulations list');
    $.ajax({
        url: ESSIM_simulation_URL_prefix + 'favorites_list',
        success: function(data){
            let $fav_list_div = $('#'+div_id);
            let $title = $('<h1>').text('Favorite ESSIM simulations')
            $fav_list_div.append($title)

            if (data.length > 0) {
                let $table = $('<table>').addClass('pure-table pure-table-striped simulations').attr("id", "fav_list");
                $fav_list_div.append($table);
                let $thead = $('<thead>').append($('<tr>').append($('<th>').text('Date')).append($('<th>')
                    .text('Description')).append($('<th>').text('Action')));
                let $tbody = $('<tbody>');
                $table.append($thead);
                $table.append($tbody);

                for (let i=0; i<data.length; i++) {
                    let simulation_id = data[i]['simulation_id']
                    let $tr = $("<tr>").attr("id", simulation_id);

                    let es_name = data[i]['simulation_es_name'];
                    if (es_name == null) es_name = "Untitled energysystem";
                    let more_info = 'Energysystem name: '+ es_name + ', Simulation ID: ' + simulation_id;

                    let $td_datetime = $("<td>").append(data[i]['simulation_datetime']).attr('title', more_info);
                    $tr.append($td_datetime);
                    let $td_descr = $("<td>").append(data[i]['simulation_descr']).attr('title', more_info);
                    $tr.append($td_descr);

                    let $actions = $('<div>');
                    let $select_scenario_button = $('<button>').addClass('btn')
                        .append($('<i>').addClass('fas fa-eye').css('color', 'black'))
                        .click( function(e) { sidebar.hide(); set_simulation_id(simulation_id); });
                    $actions.append($select_scenario_button);
                    let $remove_scenario_button = $('<button>').addClass('btn')
                        .append($('<i>').addClass('fas fa-trash-alt').css('color', 'black'))
                        .attr('title', 'Remove from list')
                        .click( function(e) { remove_sim_fav('favorite', simulation_id); });
                    $actions.append($remove_scenario_button);

                    if (data[i]['dashboard_url'] !== '') {
                        let $view_dashboard_button = $('<a>').attr('href', data[i]['dashboard_url']).attr('target', '#')
                            .append($('<button>').addClass('btn').append($('<i>').addClass('fas fa-chart-line').css('color', 'green'))).attr('title', 'Show Dashboard');
                        $actions.append($view_dashboard_button);
                    }
                    if (data[i]['kpi_result_list']) {
                        let $view_kpis_button = $('<button>').addClass('btn').append($('<i>')
                            .addClass('fas fa-tachometer-alt').css('color', 'blue')).attr('title', 'Show KPIs')
                            .click( function(e) { show_kpis(simulation_id, 'favorite'); });
                        $actions.append($view_kpis_button);
                    }

                    $tr.append($("<td>").append($actions));
                    $tbody.append($tr);
                }
            } else {
                $fav_list_div.append($('<p>').text('No previous ESSIM favorites stored'));
            }
        },
        dataType: "json",
        error: function(xhr, ajaxOptions, thrownError) {
            console.log('Error occurred in show_favorites_list: ' + xhr.status + ' - ' + thrownError);
        }
    });
}


function show_simulations_list(div_id) {
    // console.log('retreiving ESSIM simulations list');
    $.ajax({
        url: ESSIM_simulation_URL_prefix + 'simulations_list',
        success: function(data){
            let $sim_list_div = $('#'+div_id);
            let $title = $('<h1>').text('Previous ESSIM simulations')
            $sim_list_div.append($title)

            if (data.length > 0) {
                let $table = $('<table>').addClass('pure-table pure-table-striped simulations').attr("id", "sim_list");
                $sim_list_div.append($table);
                let $thead = $('<thead>').append($('<tr>').append($('<th>').text('Date')).append($('<th>')
                    .text('Description')).append($('<th>').text('Action')));
                let $tbody = $('<tbody>');
                $table.append($thead);
                $table.append($tbody);

                for (let i=0; i<data.length; i++) {
                    let simulation_id = data[i]['simulation_id']
                    let $tr = $("<tr>").attr("id", simulation_id);

                    let es_name = data[i]['simulation_es_name'];
                    if (es_name == null) es_name = "Untitled energysystem";
                    let more_info = 'Energysystem name: '+ es_name + ', Simulation ID: ' + simulation_id;

                    let $td_datetime = $("<td>").append(data[i]['simulation_datetime']).attr('title', more_info);
                    $tr.append($td_datetime);
                    let $td_descr = $("<td>").append(data[i]['simulation_descr']).attr('title', more_info);
                    $tr.append($td_descr);

                    $actions = $('<div>');
                    let $select_scenario_button = $('<button>').addClass('btn')
                        .append($('<i>').addClass('fas fa-eye').css('color', 'black'))
                        .click( function(e) { sidebar.hide(); set_simulation_id(simulation_id); });
                    $actions.append($select_scenario_button);
                    let $remove_scenario_button = $('<button>').addClass('btn remove_button')
                        .append($('<i>').addClass('fas fa-trash-alt').css('color', 'black'))
                        .attr('title', 'Remove from list')
                        .click( function(e) { remove_sim_fav('simulation', simulation_id); });
                    $actions.append($remove_scenario_button);
                    let $favorite_scenario_button = $('<button>').addClass('btn favorite_button')
                        .append($('<i>').addClass('far fa-star').css('color', 'black'))
                        .attr('title', 'Add to favorites')
                        .click( function(e) { favorite_simulation(simulation_id); });
                    $actions.append($favorite_scenario_button);

                    if (data[i]['dashboard_url'] !== '') {
                        let $view_dashboard_button = $('<a>').attr('href', data[i]['dashboard_url']).attr('target', '#')
                            .append($('<button>').addClass('btn').append($('<i>').addClass('fas fa-chart-line').css('color', 'green'))).attr('title', 'Show Dashboard');
                        $actions.append($view_dashboard_button);
                    }
                    if (data[i]['kpi_result_list']) {
                        let $view_kpis_button = $('<button>').addClass('btn').append($('<i>')
                            .addClass('fas fa-tachometer-alt').css('color', 'blue')).attr('title', 'Show KPIs')
                            .click( function(e) { show_kpis(simulation_id, 'simulation'); });
                        $actions.append($view_kpis_button);
                    }
                    $tr.append($("<td>").append($actions));
                    $tbody.append($tr);
                }
            } else {
                $sim_list_div.append($('<p>').text('No previous ESSIM simulations stored'));
            }
        },
        dataType: "json",
        error: function(xhr, ajaxOptions, thrownError) {
            console.log('Error occurred in show_simulations_list: ' + xhr.status + ' - ' + thrownError);
        }
    });
}

function show_essim_kpi_selection(select_id) {
    $.ajax({
        url: ESSIM_simulation_URL_prefix + 'essim_kpis',
        success: function(data){
            let $select = $('#'+select_id);
            $select.empty();

            for (let i=0; i<data.length; i++) {
                let $option = $('<option>').attr('value', data[i].id).text(data[i].name);
                $select.append($option);
            }
        },
        dataType: "json",
        error: function(xhr, ajaxOptions, thrownError) {
            console.log('Error occurred in show_essim_kpi_selection: ' + xhr.status + ' - ' + thrownError);
        }
    });

}

function run_ESSIM_simulation_window() {
    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<div id="essim_title"><h1>Run ESSIM simulation</h1></div>';

    essim_settings = '<div id="essim_settings">';
    essim_settings += 'Please enter a description for this simulation. This description will be shown in the simulation results.';
    essim_settings += '<p><input id="sim_description" type="text" width="600"/></p>';
    essim_settings += 'The following settings should only be changed if you know exactly what you\'re doing';
    essim_settings += '<p>';
    essim_settings += '<input type="radio" id="sim_y2015" name="sim_period" value="y2015" onclick="enable_disable_custom_year(id);">';
    essim_settings += '<label for="y2015">Year 2015</label><br>';
    essim_settings += '<input type="radio" id="sim_y2019" name="sim_period" value="y2019" checked onclick="enable_disable_custom_year(id);">';
    essim_settings += '<label for="y2015">Year 2019</label><br>';
    essim_settings += '<input type="radio" id="sim_custom_year" name="sim_period" value="custom_year" onclick="enable_disable_custom_year(id);">';
    essim_settings += '<label for="y2015">Custom year</label><br>';

    table = '<table>';
    table += '<tr><td width=180>Start datetime</td><td><input type="text" width="60" id="sim_start_datetime" disabled value="2015-01-01T00:00:00+0100"></td></tr>';
    table += '<tr><td width=180>End datetime</td><td><input type="text" width="60" id="sim_end_datetime" disabled value="2015-02-01T00:00:00+0100"></td></tr>';
    table += '</table>';
    essim_settings += table;
    essim_settings += '</p>';
    essim_settings += '</div>';
    sidebar_ctr.innerHTML += essim_settings;

    sidebar.show();

    essim_kpi_selection = '<div id="essim_kpi_selection_div">';
    essim_kpi_selection += 'Please select the KPIs that you want to be calculated after the simulation';
    essim_kpi_selection += '<p><select id="essim_kpi_select" multiple size="10"></select></p>';
    essim_kpi_selection += '</div>';
    sidebar_ctr.innerHTML += essim_kpi_selection;
    show_essim_kpi_selection('essim_kpi_select');

    let essim_loadflow_div = '<div id="essim_loadflow_div">';
    essim_loadflow_div += '<input type="checkbox" id="essim_loadflow_cb" name="essim_loadflow"><label for="essim_loadflow_cb"> Use ESSIM with loadflow engine</label>';
    essim_loadflow_div += '</div>';
    sidebar_ctr.innerHTML += essim_loadflow_div;

    sidebar_ctr.innerHTML += '<p id="run_essim_simulation_button"><button id="run_ESSIM_button" onclick="run_ESSIM_simulation();">Run</button></p>';

    sidebar_ctr.innerHTML += '<div id="simulation_progress_div"></div>';
    sidebar_ctr.innerHTML += '<div id="kpi_progress_div"></div>';
    sidebar_ctr.innerHTML += '<div id="favorites_list_div"></div>';
    show_favorites_list('favorites_list_div');
    sidebar_ctr.innerHTML += '<div id="simulations_list_div"></div>';
    show_simulations_list('simulations_list_div');

}

function run_ESSIM_simulation() {
    document.getElementById('essim_title').innerHTML = '<h1>ESSIM simulation started</h1>';
    document.getElementById('essim_settings').style.display = 'none';
    document.getElementById('essim_loadflow_div').style.display = 'none';
    document.getElementById('run_essim_simulation_button').style.display = 'none';
    document.getElementById('essim_kpi_selection_div').style.display = 'none';
    document.getElementById('favorites_list_div').style.display = 'none';
    document.getElementById('simulations_list_div').style.display = 'none';

    simulation_progress_div = document.getElementById('simulation_progress_div');
    table = '<div id="simulation_progress"><table>';
    table = table + '<tr><td width=180>Progress</td>';
    table = table + '<td id="progress_percentage">0%</td></tr>';
    table += '</table></div>';
    simulation_progress_div.innerHTML = table;

    simulation_progress_div.innerHTML += '<p id="dashboard_url"></p>';
    simulation_progress_div.innerHTML += '<p id="simulationRun"></p>';

    simulation_progress_div.innerHTML += '<p id="button_cancel_simulation"><button onclick="cancel_ESSIM_simulation(); sidebar.hide();">Cancel simulation</button></p>';
    simulation_progress_div.innerHTML += '<p id="button_close_simulation_dialog" hidden><button onclick="sidebar.hide();">Close</button></p>';

    sim_description = document.getElementById('sim_description').value;

    if (document.getElementById('sim_y2015').checked) {
        sim_start_datetime = '2015-01-01T00:00:00+0100';
        sim_end_datetime = '2016-01-01T00:00:00+0100';
    } else if (document.getElementById('sim_y2019').checked) {
        sim_start_datetime = '2019-01-01T00:00:00+0100';
        sim_end_datetime = '2020-01-01T00:00:00+0100';
    } else {
        sim_start_datetime = document.getElementById('sim_start_datetime').value;
        sim_end_datetime = document.getElementById('sim_end_datetime').value;
    }

    let essim_loadflow = $('#essim_loadflow_cb').prop('checked');
    let selected_kpis = $('#essim_kpi_select').val();
    console.log(essim_loadflow);

    socket.emit('command', {cmd: 'run_ESSIM_simulation', sim_description: sim_description,
        sim_start_datetime: sim_start_datetime, sim_end_datetime: sim_end_datetime, essim_kpis: selected_kpis,
        essim_loadflow: essim_loadflow});
    attempt = 0;
    setTimeout(poll_simulation_progress, 1000);
}

function simulation_not_started() {
    sidebar.hide();
}

function cancel_ESSIM_simulation() {
    socket.emit('command', {cmd: 'cancel_ESSIM_simulation'});
}

function poll_simulation_progress() {
    $.ajax({
        url: ESSIM_simulation_URL_prefix + 'simulation_progress',
        success: function(data){
            // console.log(data);
            if (data["status"] == "ERROR") {
                let description = data["description"];
                let more_info = data["moreInfo"];

                document.getElementById('essim_title').innerHTML = '<h1>ESSIM simulation error</h1>';
                document.getElementById('simulation_progress').innerHTML = '<p style="font-size:70%;" title="'+more_info+'">'+description+'</p>';

                document.getElementById('button_close_simulation_dialog').style.display = "block";
                document.getElementById('button_cancel_simulation').style.display = "none";
            } else if (data["status"] == "COMPLETE") {
                let dashboardURL = data["url"];
                let simulationRun = data["simulationRun"];
                // console.log(dashboardURL);

                document.getElementById('essim_title').innerHTML = '<h1>ESSIM simulation finished</h1>';
                document.getElementById('simulation_progress').style.display = 'none';

                let dbURL_location = document.getElementById('dashboard_url');
                dbURL_location.innerHTML = 'Go to <a href="' + dashboardURL + '" target="#">dashboard</a>';
                let simRun_location = document.getElementById('simulationRun');
                simRun_location.innerHTML = simulationRun;

                document.getElementById('button_close_simulation_dialog').style.display = "block";
                document.getElementById('button_cancel_simulation').style.display = "none";

                attempt = 0;
                let selected_kpis = $('#essim_kpi_select').val();
                if (selected_kpis && selected_kpis.length > 0)
                    poll_kpi_progress();
            } else {
                let percentage = Math.round(parseFloat(data["percentage"]) * 100);
                let progress = document.getElementById('progress_percentage');
                progress.innerHTML =  percentage + '%';
                setTimeout(poll_simulation_progress, 1000);
            }
        },
        dataType: "json",
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);

            if (attempt<5) {
                attempt = attempt + 1;
                setTimeout(poll_simulation_progress, 1000);
            } else {
                attempt = 0;
            }
        }
    });
}

function generate_table_with_kpi_calculation_status(status) {
    let $table = $('<table>').addClass('pure-table pure-table-striped simulations').attr('id', 'kpi_results_table');
    let $thead = $('<thead>').append($('<tr>').append($('<th>').text('KPI')).append($('<th>')
        .text('Status')).append($('<th>').text('Progress')));
    let $tbody = $('<tbody>');
    $table.append($thead);
    $table.append($tbody);

    for (let i=0; i<status.length; i++) {
        let kpi_result_status = status[i];
        let $tr = $('<tr>').attr('id', kpi_result_status['id']);

        let kpi_name = kpi_result_status['name'];
        let kpi_descr = kpi_result_status['descr'];
        let kpi_calc_status = kpi_result_status['calc_status'];

        let $td_name = $('<td>').append(kpi_name).attr('title', kpi_descr);
        $tr.append($td_name);
        let $td_status = $('<td>').append(kpi_calc_status);
        $tr.append($td_status);

        let $td_progress = $('<td>');
        if (kpi_calc_status === 'Calculating') {
            let progr_str = kpi_result_status['progress'];
            let progr_float = Math.round(((100*parseFloat(progr_str))+Number.EPSILON) * 100) / 100;
            $td_progress.append((progr_float).toString() + '%');
        }
        $tr.append($td_progress);
        $tbody.append($tr);
    }
    return $table;
}

function poll_kpi_progress() {
    $.ajax({
        url: ESSIM_simulation_URL_prefix + 'essim_kpi_results',
        success: function(data){
            console.log(data);
            $('#kpi_progress_div').empty();
            if (data['still_calculating']) {
                let status = data['results'];
                let $table = generate_table_with_kpi_calculation_status(status);

                $('#kpi_progress_div').append($table);
                setTimeout(poll_kpi_progress, 1000);
            } else {
                sidebar.hide();
                socket.emit('kpi_visualization');
            }
        },
        dataType: "json",
        error: function(xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);

            if (attempt<5) {
                attempt = attempt + 1;
                setTimeout(poll_kpi_progress, 1000);
            } else {
                attempt = 0;
            }
        }
    });
}

// ------------------------------------------------------------------------------------------------------------
//   ESSIM KPIs
// ------------------------------------------------------------------------------------------------------------
function calculate_ESSIM_KPIs() {
    socket.emit('command', {cmd: 'calculate_ESSIM_KPIs'});

    // show loader
    show_loader();
}

// format-number-with-si-prefix.js
// https://gist.github.com/cho45/9968462
function formatN (n) {
    // console.log("n: ", n);
    var nn = n.toExponential(2).split(/e/);
    // console.log("nn: ", nn)
    var u = Math.floor(+nn[1] / 3);
    // console.log("u: ", u)
    return nn[0] * Math.pow(10, +nn[1] - u * 3) + ['p', 'n', 'u', 'm', '', 'k', 'M', 'G', 'T', 'P'][u+4];
}

function print_value_unit(val, unit) {
    if (unit == 'kgCO2') {
        val_s = parseFloat(Number(val / 1e6).toPrecision(2)).toString();
        return val_s + ' kton CO2';
    } else {
        val_s = formatN(val);
        // console.log(val);
        // console.log(unit);
        // console.log(val_s);
        return val_s + unit;
    }
}

function create_bar_chart(title, labels, values) {

    console.log(title);
    console.log(labels);
    console.log(values);

    let title_for_id = title.replace(/ /g, "_");

    let bc_div = L.DomUtil.create('div');
    bc_div.setAttribute('id', 'bc_div_'+title_for_id);
    let bc_canvas = L.DomUtil.create('canvas', '', bc_div);
    bc_canvas.setAttribute('id', 'bc_canvas_'+title_for_id);

    var bar_chart = new Chart(bc_canvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    label: "test",
                    borderColor: "#3e95cd",
                }]
            },
            options: {
                title: {
                    display: true,
                    text: title
                }
            }
        });

    return bc_div
}

function show_ESSIM_KPIs(results) {
    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>ESSIM KPI\'s</h1>';

    let category = null;
    let table = "";
    let labels = [];
    let values = [];

    console.log(results);

    for (let i=0; i<results.length; i++) {
        let name = results[i]['name'];
        let cat_kpi = name.split("-");
        let cat = cat_kpi[0];
        let kpi = cat_kpi[1];

        if (cat != category) {            // stop table, start new one
            if (table != "") {
                table += '</table>';
                sidebar_ctr.innerHTML += table;
                table = "";

                sidebar_ctr.innerHTML += '<div id="graph-'+cat+'"></div>';
                $('#graph-'+category).append(create_bar_chart(category, labels, values));
                labels = [];
                values = [];
            }

            sidebar_ctr.innerHTML += '<h2>'+cat+'</h2>';
            table = '<table>';
            category = cat;
        }
        if (kpi.indexOf("Total") == 0) {
            bold_start = "<b>";
            bold_end = "</b>";
        } else {
            bold_start = "";
            bold_end = "";

            labels.push(kpi);
            values.push(results[i]['value']);
        }
        table += '<tr><td width=180>'+bold_start+kpi+bold_end+'</td>';
        table += '<td>'+bold_start+print_value_unit(results[i]['value'], results[i]['unit'])+bold_end+'</td></tr>';
    }
    table += '</table>';
    sidebar_ctr.innerHTML += table;

    sidebar.show();
}

// ------------------------------------------------------------------------------------------------------------
//   ESSIM animate load
// ------------------------------------------------------------------------------------------------------------
function animate_ESSIM_load() {
    show_loader();
    $.ajax({
        url: ESSIM_simulation_URL_prefix + 'load_animation',
        success: function(data){
            // console.log('succes');
            // console.log(data);

            var geoJsonLayer = L.geoJson(data, {
                style: function(feature) {
                    return {
                        "color": feature.properties.stroke,
                        "weight": feature.properties.strokewidth,
                        "opacity": 1
                    };
                }
            });

            var geoJsonTimeLayer = L.timeDimension.layer.geoJson.geometryCollection(geoJsonLayer, {
                updateTimeDimension: true,
                updateTimeDimensionMode: 'replace',
                duration: 'PT1H',
            });

            geoJsonTimeLayer.addTo(sim_layer);
            hide_loader();
        },
        error: function() {
            hide_loader();
            alert("Error in getting load animation from backend");
        },
        dataType: "json"
    });
}
