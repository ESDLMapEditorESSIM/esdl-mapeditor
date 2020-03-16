ESSIM_simulation_URL_prefix = '';

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

function run_ESSIM_simulation_window() {
    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<div id="essim_title"><h1>Run ESSIM simulation</h1></div>';

    essim_settings = '<div id="essim_settings">';
    essim_settings += 'Please enter a description for this simulation. This description will be shown in the simulation results.';
    essim_settings += '<p><input id="sim_description" type="text" width="600"/></p>';
    essim_settings += 'The following settings should only be changed if you know exactly what you\'re doing';
    essim_settings += '<p>';
    essim_settings += '<input type="radio" id="sim_y2015" name="sim_period" value="y2015" checked onclick="enable_disable_custom_year(id);">';
    essim_settings += '<label for="y2015">Year 2015</label><br>';
    essim_settings += '<input type="radio" id="sim_y2019" name="sim_period" value="y2019" onclick="enable_disable_custom_year(id);">';
    essim_settings += '<label for="y2015">Year 2019</label><br>';
    essim_settings += '<input type="radio" id="sim_custom_year" name="sim_period" value="custom_year" onclick="enable_disable_custom_year(id);">';
    essim_settings += '<label for="y2015">Custom year</label><br>';

    table = '<table>';
    table += '<tr><td width=180>Start datetime</td><td><input type="text" width="60" id="sim_start_datetime" disabled value="2015-01-01T00:00:00+0100"></td></tr>';
    table += '<tr><td width=180>End datetime</td><td><input type="text" width="60" id="sim_end_datetime" disabled value="2016-01-01T00:00:00+0100"></td></tr>';
    table += '</table>';
    essim_settings += table;
    essim_settings += '</p>';
    essim_settings += '</div>';
    sidebar_ctr.innerHTML += essim_settings;

    sidebar_ctr.innerHTML += '<p id="run_essim_simulation_button"><button id="run_ESSIM_button" onclick="run_ESSIM_simulation();">Run</button></p>';

    sidebar_ctr.innerHTML += '<div id="simulation_progress_div"></div>';

    sidebar.show();
}

function run_ESSIM_simulation() {
    document.getElementById('essim_title').innerHTML = '<h1>ESSIM simulation started</h1>';
    document.getElementById('essim_settings').style.display = 'none';
    document.getElementById('run_essim_simulation_button').style.display = 'none';
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
    socket.emit('command', {cmd: 'run_ESSIM_simulation', sim_description: sim_description,
        sim_start_datetime: sim_start_datetime, sim_end_datetime: sim_end_datetime});
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

            if (data["percentage"] == "1") {
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

            } else {
                let percentage = Math.round(parseFloat(data["percentage"]) * 100);
                let progress = document.getElementById('progress_percentage');
                progress.innerHTML =  percentage + '%';
                setTimeout(poll_simulation_progress, 1000);
            }
        },
        dataType: "json"
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

function show_ESSIM_KPIs(results) {
    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>ESSIM KPI\'s</h1>';

    let category = null;
    let table = "";

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
