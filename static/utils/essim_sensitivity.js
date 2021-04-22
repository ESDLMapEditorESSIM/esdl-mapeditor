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

class ESSIM_sensitivity{
    constructor() {
        this.initSocketIO();

        this.attempt = 0;
        this.kpi_progress_prev_progress = 0;
        this.kpi_progress_attempt = 0;
        this.kpis = false;
        this.asset_list = [];
        this.sim_start_datetime = "";
        this.sim_end_datetime = "";
    }

    initSocketIO() {
        console.log("Registering ESSIM sensitivity plugin");
    }

    show_ESSIM_sensitivity_analysis_window() {
        if (!(sidebar_b.isVisible())) {
            sidebar_b.setContent(essim_sensitivity_plugin.create_sidebar_content(null).get(0));
            sidebar_b.show();
        }
    }

    run_simulations() {
        let $select = $('#sens_ana_kpi_select');
        let selected_kpis = $select.val();
        if (selected_kpis == null) {
            selected_kpis = [];
        }
        essim_sensitivity_plugin.kpis = selected_kpis;

        let sens_anal_info = [];
        for (let i=0; i<essim_sensitivity_plugin.asset_list.length; i++) {
            let asset_info = essim_sensitivity_plugin.asset_list[i];

            sens_anal_info.push({
                asset_id: asset_info.id,
                attr: asset_info.attr,
                attr_start: asset_info.attr_start,
                attr_step: asset_info.attr_step,
                attr_end: asset_info.attr_end
            });
        }

        socket.emit('essim_sensitivity_run_simulations', {
            period: {
                start: this.sim_start_datetime,
                end: this.sim_end_datetime
            },
            selected_kpis: selected_kpis,
            sens_anal_info: sens_anal_info
        }, function(res) {
            if (res == 1) {
                essim_sensitivity_plugin.clean_div();
                essim_sensitivity_plugin.show_sensitivity_analyis_progress_monitoring();
            } else {
                $('#essim_sensitivity_title').text('ESSIM Sensitivity Analysis - Error starting ESSIM SA run');
                console.log("First SA ESSIM simulation could not be started")
            }
        });
    }

    clean_div() {
        $('#essim_sens_button_div').hide();
    }

    next_simulation() {
        socket.emit('essim_sensitivity_next_simulation', function(res) {
            if (res == 1) {
                setTimeout(essim_sensitivity_plugin.monitor_sensitivity_analysis_progress, 1000);
            } else {
                $('#essim_sensitivity_title').text('ESSIM Sensitivity Analysis - Simulations finished');
                $('#sens_analysis_progress').empty();
                if (essim_sensitivity_plugin.kpis.length) {
                    socket.emit('kpi_visualization');
                }
            }
        });
    }

    generate_kpi_calculation_status(status) {
        let $line = $('<div>');
        let text = 'KPIs: ';
        let summed_progress = 0.0;
        for (let i=0; i<status.length; i++) {
            let kpi_result_status = status[i];

            let kpi_name = kpi_result_status['name'];
            let kpi_calc_status = kpi_result_status['calc_status'];

            if (kpi_calc_status === 'Calculating') {
                let progr_str = kpi_result_status['progress'];
                let progr_float = Math.round(((100*parseFloat(progr_str))+Number.EPSILON) * 100) / 100;
                text = text + ((progr_float).toString() + '%-');
                summed_progress = summed_progress + progr_float;
            } else {
                text = text + kpi_calc_status+'-';
            }
        }
        $line.append($('<p>').text(text));
        return [$line, summed_progress];
    }

    monitor_sensitivity_analysis_kpi_progress() {
        $.ajax({
            url: ESSIM_simulation_URL_prefix + 'essim_kpi_results',
            success: function(data){
                console.log(data);

                $('#kpi_progress_div').empty();
                if (data['still_calculating']) {
                    let status = data['results'];
                    let result = essim_sensitivity_plugin.generate_kpi_calculation_status(status);
                    let $line = result[0];
                    let summed_progress = result[1];
                    $('#sens_analysis_progress').empty().append($line);

                    if (essim_sensitivity_plugin.kpi_progress_prev_progress < 1e-6) {
                        if (Math.abs(summed_progress - essim_sensitivity_plugin.kpi_progress_prev_progress) < 1e-6) {
                            essim_sensitivity_plugin.kpi_progress_attempt = essim_sensitivity_plugin.kpi_progress_attempt + 1;
                            if (essim_sensitivity_plugin.kpi_progress_attempt == 20) {
                                $('#sens_analysis_progress').append($('<div>').append($('<p>').text('No KPI progress anymore')));
                                essim_sensitivity_plugin.kpi_progress_prev_progress = 0.0;
                                essim_sensitivity_plugin.kpi_progress_attempt = 0;
                                return;
                            }
                        } else {
                            essim_sensitivity_plugin.kpi_progress_prev_progress = summed_progress;
                            essim_sensitivity_plugin.kpi_progress_attempt = 0;
                        }
                    } else
                        essim_sensitivity_plugin.kpi_progress_prev_progress = summed_progress;

                    setTimeout(essim_sensitivity_plugin.monitor_sensitivity_analysis_kpi_progress, 1000);
                } else {
                    essim_sensitivity_plugin.kpi_progress_prev_line = null;
                    essim_sensitivity_plugin.kpi_progress_attempt = 0;
                    essim_sensitivity_plugin.next_simulation();
                }
            },
            dataType: "json",
            error: function(xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);

                if (essim_sensitivity_plugin.attempt<5) {
                    essim_sensitivity_plugin.attempt = essim_sensitivity_plugin.attempt + 1;
                    setTimeout(essim_sensitivity_plugin.monitor_sensitivity_analysis_kpi_progress, 1000);
                } else {
                    essim_sensitivity_plugin.attempt = 0;
                }
            }
        });
    }

    monitor_sensitivity_analysis_progress() {
        $.ajax({
            url: ESSIM_simulation_URL_prefix + 'simulation_progress',
            success: function(data){
                // console.log(data);
                if (data["status"] == "ERROR") {
                    let description = data["description"];
                    let more_info = data["moreInfo"];

                    $('#essim_sensitivity_title').text('ESSIM Sensitivity Analysis - Simulation error');
                    document.getElementById('sens_analysis_progress').innerHTML = '<p style="font-size:70%;" title="'+more_info+'">'+description+'</p>';
                } else if (data["status"] == "COMPLETE") {
                    let dashboardURL = data["url"];
                    let simulationRun = data["simulationRun"];

                    $('#essim_sens_finished_div').append($('<p>').text(simulationRun + ': Go to ')
                        .append($('<a>').attr('href', dashboardURL).attr('target', '#').text('dashboard')));

                    let progress = document.getElementById('sens_analysis_progress');
                    progress.innerHTML =  '';

                    essim_sensitivity_plugin.attempt = 0;
                    if (essim_sensitivity_plugin.kpis.length)
                        essim_sensitivity_plugin.monitor_sensitivity_analysis_kpi_progress();
                    else
                        essim_sensitivity_plugin.next_simulation();
                } else {
                    let percentage = Math.round(parseFloat(data["percentage"]) * 100);
                    let progress = document.getElementById('sens_analysis_progress');
                    progress.innerHTML = 'ESSIM simulation progress: ' + percentage + '%';
                    setTimeout(essim_sensitivity_plugin.monitor_sensitivity_analysis_progress, 1000);
                }
            },
            dataType: "json",
            error: function(xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);

                if (essim_sensitivity_plugin.attempt<5) {
                    essim_sensitivity_plugin.attempt = essim_sensitivity_plugin.attempt + 1;
                    setTimeout(essim_sensitivity_plugin.monitor_sensitivity_analysis_progress, 1000);
                } else {
                    essim_sensitivity_plugin.attempt = 0;
                }
            }
        });
    }

    show_sensitivity_analyis_progress_monitoring() {
        $('#essim_sensitivity_title').text('ESSIM Sensitivity Analysis - Running simulations');
        let $div = $('#essim_sens_content_div');
        $div.empty();

        let $finished_div = $('<div>').attr('id', 'essim_sens_finished_div').addClass('sidebar-div');
        $div.append($finished_div);

        let $progress_div = $('<div>').attr('id', 'essim_sens_progress_div').addClass('sidebar-div');
        $div.append($progress_div);
        $progress_div.append($('<p>').attr('id', 'sens_analysis_progress'));
        $progress_div.append($('<p>').attr('id', 'sens_analysis_dashboard_url'));
        $progress_div.append($('<p>').attr('id', 'sens_analysis_simulationRun'));

        // Query progress
        essim_sensitivity_plugin.monitor_sensitivity_analysis_progress();
        // setTimeout(essim_sensitivity_plugin.monitor_sensitivity_analysis_progress, 1000);
    }

    select_kpis_window() {
        if ($('#sa_y2015').prop('checked')) {
            this.sim_start_datetime = "2015-01-01T00:00:00+0100";
            this.sim_end_datetime = "2016-01-01T00:00:00+0100";
        } else if ($('#sa_y2019').prop('checked')) {
            this.sim_start_datetime = "2019-01-01T00:00:00+0100";
            this.sim_end_datetime = "2020-01-01T00:00:00+0100";
        } else if ($('#sa_custy').prop('checked')) {
            this.sim_start_datetime = $('#sa_sim_start_datetime').val();
            this.sim_end_datetime = $('#sa_sim_end_datetime').val();
        }

        essim_sensitivity_plugin.kpis = false;
        $('#essim_sensitivity_title').text('ESSIM Sensitivity Analysis - Select KPIs');
        let $div = $('#essim_sens_content_div')
        $div.empty();

        let $kpi_div = $('<div>').attr('id', 'essim_sens_kpi_div').addClass('sidebar-div');
        $div.append($kpi_div);
        let $kpi_select = $('<select>').attr('id', 'sens_ana_kpi_select').attr('size', '10').attr('multiple', 'multiple');
        $kpi_div.append($kpi_select);
        show_essim_kpi_selection('sens_ana_kpi_select');

        let $button_div = $('#essim_sens_button_div');
        $button_div.empty()
        let $button = $('<button>').text('Run simulations');
        $button.click(function () { essim_sensitivity_plugin.run_simulations(); });
        $button_div.append($button);
    }

    enable_custom_year(tf) {
        if (tf) {
            $('#sa_sim_start_datetime').prop('disabled', false);
            $('#sa_sim_end_datetime').prop('disabled', false);
        } else {
            $('#sa_sim_start_datetime').prop('disabled', true);
            $('#sa_sim_end_datetime').prop('disabled', true);
        }
    }

    select_period_window() {
        $('#essim_sensitivity_title').text('ESSIM Sensitivity Analysis - Select simulation period');
        let $div = $('#essim_sens_content_div');
        $div.empty();

        $div.append($('<div>').append($('<input>').attr('type', 'radio').attr('id', 'sa_y2015').attr('value', 'y2015')
            .attr('name', 'sa_sim_period').click(function() {essim_sensitivity_plugin.enable_custom_year(false);}))
            .append($('<label>').attr('for', 'y2015').text('2015')));
        $div.append($('<div>').append($('<input>').attr('type', 'radio').prop('checked',true).attr('id', 'sa_y2019').attr('value', 'y2019')
            .attr('name', 'sa_sim_period').click(function() {essim_sensitivity_plugin.enable_custom_year(false);}))
            .append($('<label>').attr('for', 'y2019').text('2019')));
        $div.append($('<div>').append($('<input>').attr('type', 'radio').attr('id', 'sa_custy').attr('value', 'custom_date')
            .attr('name', 'sa_sim_period').click(function() {essim_sensitivity_plugin.enable_custom_year(true);}))
            .append($('<label>').attr('for', 'custy').text('Custom date')));

        $div.append($('<table>')
            .append($('<tbody>')
                .append($('<tr>')
                    .append($('<td>').text('Start datetime: '))
                    .append($('<td>').append($('<input>').attr('type', 'text').attr('width','60')
                        .attr('id', 'sa_sim_start_datetime').attr('value','2019-01-01T00:00:00+0100').prop('disabled', true))))
                .append($('<tr>')
                    .append($('<td>').text('End datetime: '))
                    .append($('<td>').append($('<input>').attr('type', 'text').attr('width','60')
                        .attr('id', 'sa_sim_end_datetime').attr('value','2019-02-01T00:00:00+0100').prop('disabled', true))))
            ));

        let $button_div = $('#essim_sens_button_div');
        $button_div.empty()
        let $button = $('<button>').text('Next');
        $button.click(function () { essim_sensitivity_plugin.select_kpis_window(); });
        $button_div.append($button);
    }

    clear_sa_assets() {
        this.asset_list = [];
        $('#essim_sensitivity_table_body tr').remove();
    }

    create_sidebar_content(data) {
        let $div = $('<div>').attr('id', 'essim_sensitivity_main_div');
        let $title = $('<h1>').attr('id', 'essim_sensitivity_title').text('ESSIM Sensitivity Analysis - Select attributes');
        $div.append($title);

        let $content_div = $('<div>').attr('id', 'essim_sens_content_div').addClass('sidebar-div');
        $div.append($content_div);

        let $table = $('<table>').addClass('pure-table pure-table-striped');
        let $thead = $('<thead>').append($('<tr>')
            .append($('<th>').text('Item'))
            .append($('<th>').text('Parameter'))
            .append($('<th>').text('Start'))
            .append($('<th>').text('Step'))
            .append($('<th>').text('End'))
            .append($('<th>').text('#'))
            .append($('<th>').text('Connect to previous')));
        let $tbody = $('<tbody>').attr('id', 'essim_sensitivity_table_body');

        for (let i=0; i<essim_sensitivity_plugin.asset_list.length; i++) {
            let asset_info = essim_sensitivity_plugin.asset_list[i];
            $tbody.append(essim_sensitivity_plugin.create_table_row(asset_info));
        }

        $table.append($thead);
        $table.append($tbody);

        $content_div.append($table);

        let $button_div = $('<div>').attr('id', 'essim_sens_button_div').addClass('sidebar-div');
        $div.append($button_div);
        let $clear_button = $('<button>').text('Clear');
        $clear_button.click(function() { essim_sensitivity_plugin.clear_sa_assets(); });
        $button_div.append($clear_button);
        let $button = $('<button>').text('Next');
        $button.click(function() { essim_sensitivity_plugin.select_period_window(); });
        $button_div.append($button);

        return $div;
    }

    // Finds the first asset attribute of type EInt
    find_asset_attr_eint(asset_info, attrs_sorted) {
        for (let i=0; i<attrs_sorted.length; i++) {
            if (attrs_sorted[i].type === 'EInt') {
                asset_info.attr = attrs_sorted[i].name;
                let value = parseFloat(attrs_sorted[i].value);

                if (value != 0) {
                    let step = Math.round(value / 4);
                    let start = Math.round(value - step);
                    let end = Math.round(value + step);

                    asset_info.attr_start = start;
                    asset_info.attr_step = step;
                    asset_info.attr_end = end;
                } else {
                    asset_info.attr_start = 0;
                    asset_info.attr_step = 0;
                    asset_info.attr_end = 0;
                }
            }
        }
    }

    add_asset_sensitivity(e, id) {
        socket.emit('essim_sensitivity_add_asset', id, function(res) {
            let attrs_sorted = res['attrs_sorted'];
            let port_profile_list = res['port_profile_list'];

            let asset_info = {};
            asset_info.id = essim_sensitivity_plugin.get_attr_value_from_list(attrs_sorted, 'id');
            asset_info.name = essim_sensitivity_plugin.get_attr_value_from_list(attrs_sorted, 'name');
            asset_info.attrs = attrs_sorted;
            essim_sensitivity_plugin.find_asset_attr_eint(asset_info, attrs_sorted);
            asset_info.port_profile_list = port_profile_list;

            essim_sensitivity_plugin.show_ESSIM_sensitivity_analysis_window();
            essim_sensitivity_plugin.asset_list.push(asset_info);

            $('#essim_sensitivity_table_body').append(essim_sensitivity_plugin.create_table_row(asset_info));
        });
    }

    get_attr_value_from_list(lst, attr_name) {
        for (let i=0; i<lst.length; i++) {
            if (lst[i].name === attr_name) {
                return lst[i].value;
            }
        }
    }

    change_select_attr(asset_id) {
        let $select = $('#select_attr_'+asset_id);
        let selected_option = $select.val();

        let $input_attr_start = $('#input_start_'+asset_id);
        let $input_attr_step = $('#input_step_'+asset_id);
        let $input_attr_end = $('#input_end_'+asset_id);

        for (let i=0; i<essim_sensitivity_plugin.asset_list.length; i++) {
            if (essim_sensitivity_plugin.asset_list[i].id === asset_id) {
                essim_sensitivity_plugin.asset_list[i].attr = selected_option;
                let step;
                let start;
                let end;

                if (selected_option.startsWith('attr_name_')) {
                    let selected_name = selected_option.substring(10,selected_option.length);
                    let attrs = essim_sensitivity_plugin.asset_list[i].attrs;

                    for (let j=0; j<attrs.length; j++) {
                        if (attrs[j].name === selected_name) {
                            let value = parseFloat(attrs[j].value);

                            if (value != 0) {
                                step = Math.round(value / 4);
                                start = Math.round(value - step);
                                end = Math.round(value + step);
                            } else {
                                step = 0;
                                start = 0;
                                end = 0;
                            }
                        }
                    }
                } else {
                    // selected_option.startsWith('profile_id_'
                    let profile_id = selected_option.substring(11,selected_option.length);
                    let port_profile_list = essim_sensitivity_plugin.asset_list[i].port_profile_list;

                    for (let j=0; j<port_profile_list.length; j++) {
                        let port = port_profile_list[j];
                        for (let k=0; k<port.profiles.length; k++) {
                            let profile = port.profiles[k];

                            if (profile.id === profile_id) {
                                let multiplier = profile.multiplier;

                                // TODO: fix integer assumption
                                if (multiplier != 0) {
                                    step = Math.round(multiplier / 4);
                                    start = Math.round(multiplier - step);
                                    end = Math.round(multiplier + step);
                                } else {
                                    step = 0;
                                    start = 0;
                                    end = 0;
                                }
                            }
                        }
                    }
                }

                $input_attr_start.attr('value', start.toString());
                $input_attr_step.attr('value', step.toString());
                $input_attr_end.attr('value', end.toString());

                essim_sensitivity_plugin.asset_list[i].attr_start = start;
                essim_sensitivity_plugin.asset_list[i].attr_step = step;
                essim_sensitivity_plugin.asset_list[i].attr_end = end;
            }
        }
        essim_sensitivity_plugin.update_num_steps(asset_id);
    }

    change_start_step_stop(param, asset_id) {
        let value = $('#input_'+param+'_'+asset_id).val();

        for (let i=0; i<essim_sensitivity_plugin.asset_list.length; i++) {
            if (essim_sensitivity_plugin.asset_list[i].id === asset_id) {
                essim_sensitivity_plugin.asset_list[i]['attr_'+param] = value;
            }
        }

        essim_sensitivity_plugin.update_num_steps(asset_id);
    }

    update_num_steps(asset_id) {
        let start = parseFloat($('#input_start_'+asset_id).val());
        let step = parseFloat($('#input_step_'+asset_id).val());
        let end = parseFloat($('#input_end_'+asset_id).val());

        let num_steps = essim_sensitivity_plugin.calc_num_steps(start, step, end);
        $('#row_'+asset_id+' #num_steps').text(num_steps);
    }

    create_table_row(asset_info) {
        let asset_id = asset_info.id;
        let asset_name = asset_info.name;
        let asset_attr = asset_info.attr;
        let asset_attrs = asset_info.attrs;
        let asset_attr_start = asset_info.attr_start;
        let asset_attr_step = asset_info.attr_step;
        let asset_attr_end = asset_info.attr_end;
        let num_steps = essim_sensitivity_plugin.calc_num_steps(asset_attr_start, asset_attr_step, asset_attr_end);
        let port_profile_list = asset_info.port_profile_list;

        let $select = $('<select>').attr('id', 'select_attr_'+asset_id);
        let $optgroup_aa = $('<optgroup>').attr('label', 'Asset attributes');
        $optgroup_aa.style = 'font-face: bold; font-size: 10px';
        for (let i=0; i<asset_attrs.length; i++) {
            let $option = $('<option>')
                .attr('value', 'attr_name_'+asset_attrs[i].name)
                .text(asset_attrs[i].name);
            if (asset_attr === asset_attrs[i].name) $option = $option.attr('selected', 'selected');
            $optgroup_aa.append($option);
        }
        $select.append($optgroup_aa);

        let $optgroup_prof = $('<optgroup>').attr('label', 'Asset profile');
        $optgroup_prof.style = 'font-face: bold; font-size: 10px';
        for (let i=0; i<port_profile_list.length; i++) {
            let port = port_profile_list[i];
            for (let j=0; j<port.profiles.length; j++) {
                let profile = port.profiles[j];

                let $option = $('<option>')
                    .attr('value', 'profile_id_' + profile.id)
                    .text(profile.uiname + ' - multiplier');
                if (asset_attr === profile.id) $option = $option.attr('selected', 'selected');
                $optgroup_prof.append($option);
            }
        }
        $select.change(function() {
            let id = asset_id;
            essim_sensitivity_plugin.change_select_attr(id);
        });
        $select.append($optgroup_prof);

        let $input_attr_start = $('<input>').attr('id', 'input_start_'+asset_id).attr('value', asset_attr_start.toString());
        $input_attr_start.change(function() { let a_id = asset_id; essim_sensitivity_plugin.change_start_step_stop('start', a_id); });
        let $input_attr_step = $('<input>').attr('id', 'input_step_'+asset_id).attr('value', asset_attr_step.toString());
        $input_attr_step.change(function() { let a_id = asset_id; essim_sensitivity_plugin.change_start_step_stop('step', a_id); });
        let $input_attr_end = $('<input>').attr('id', 'input_end_'+asset_id).attr('value', asset_attr_end.toString());
        $input_attr_end.change(function() { let a_id = asset_id; essim_sensitivity_plugin.change_start_step_stop('end', a_id); });

        // TODO: dynamically adjust num_steps
        let $row = $('<tr>').attr('id', 'row_'+asset_id)
            .append($('<td>').text(asset_name))
            .append($('<td>').append($select))
            .append($('<td>').append($input_attr_start))
            .append($('<td>').append($input_attr_step))
            .append($('<td>').append($input_attr_end))
            .append($('<td id="num_steps">').text(num_steps))
            .append($('<td>').text('No'));
        return $row;
    }

    calc_num_steps(start, step, end) {
        if (end >= start) {
            if (step < 1e-9) return 0;
            return Math.floor((end-start)/step)+1;
        } else {
            return 0;
        }
    }

    static create(event) {
        if (event.type === 'client_connected') {
            essim_sensitivity_plugin = new ESSIM_sensitivity();
            return essim_sensitivity_plugin;
        }
        if (event.type === 'add_contextmenu') {
            let layer = event.layer;
            let layer_type = event.layer_type;
            let id = layer.id;
            if (layer_type === 'marker' || layer_type === 'line') {
                layer.options.contextmenuItems.push({
                    text: 'ESSIM sensitivity analysis',
                    icon: resource_uri + 'icons/Sensitivity.png',
                    callback: function(e) {
                        essim_sensitivity_plugin.add_asset_sensitivity(e, id);
                    }
                });
            }
        }
    }
}

var essim_sensitivity_plugin;   // global variable for the ESSIM_sensitivity plugin

$(document).ready(function() {
    extensions.push(function(event) { ESSIM_sensitivity.create(event) });
});
