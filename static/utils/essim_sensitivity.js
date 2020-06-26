class ESSIM_sensitivity{
    constructor() {
        this.initSocketIO();

        this.attempt = 0;
        this.kpis = false;
        this.asset_list = [];
    }

    initSocketIO() {
        console.log("Registering socket io bindings for ESSIM sensitivity plugin");

        socket.on('essim_sensitivity', function(data) {
            console.log(data);
            sidebar_b.setContent(essim_sensitivity_plugin.create_sidebar_content(data).get(0));
            sidebar_b.show();
        });
    }

    show_ESSIM_sensitivity_analysis_window() {
        sidebar_b.setContent(essim_sensitivity_plugin.create_sidebar_content(null).get(0));
        sidebar_b.show();
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
                start: '2015-01-01T00:00:00+0100',
                end: '2016-01-01T00:00:00+0100'
            },
            selected_kpis: selected_kpis,
            sens_anal_info: sens_anal_info
        });
        essim_sensitivity_plugin.clean_div();
        essim_sensitivity_plugin.show_sensitivity_analyis_progress_monitoring();
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
                if (essim_sensitivity_plugin.kpis) {
                    socket.emit('kpi_visualization');
                }
            }
        });
    }

    generate_line_with_kpi_calculation_status(status) {
        let $line = $('<div>');
        let text = 'KPIs: ';
        for (let i=0; i<status.length; i++) {
            let kpi_result_status = status[i];

            let kpi_name = kpi_result_status['name'];
            let kpi_calc_status = kpi_result_status['calc_status'];

            let $span_progress = $('<span>');
            if (kpi_calc_status === 'Calculating') {
                let progr_str = kpi_result_status['progress'];
                let progr_float = Math.round(((100*parseFloat(progr_str))+Number.EPSILON) * 100) / 100;
                text = text + ((progr_float).toString() + '%-');
            } else {
                text = text + kpi_calc_status+'-';
            }
        }
        return $line.append($('<p>').text(text));
    }

    monitor_sensitivity_analysis_kpi_progress() {
        $.ajax({
            url: ESSIM_simulation_URL_prefix + 'essim_kpi_results',
            success: function(data){
                console.log(data);

                $('#kpi_progress_div').empty();
                if (data['still_calculating']) {
                    let status = data['results'];
                    let $line = essim_sensitivity_plugin.generate_line_with_kpi_calculation_status(status);
                    $('#sens_analysis_progress').empty().append($line);
                    setTimeout(essim_sensitivity_plugin.monitor_sensitivity_analysis_kpi_progress, 1000);
                } else {
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
                if (data["percentage"] == "-1") {
                    let description = data["description"];
                    let more_info = data["moreInfo"];

                    $('#essim_sensitivity_title').text('ESSIM Sensitivity Analysis - Simulation error');
                    document.getElementById('sens_analysis_progress').innerHTML = '<p style="font-size:70%;" title="'+more_info+'">'+description+'</p>';
                } else if (data["percentage"] == "1") {
                    let dashboardURL = data["url"];
                    let simulationRun = data["simulationRun"];

                    $('#essim_sens_finished_div').append($('<p>').text(simulationRun + ': Go to ')
                        .append($('<a>').attr('href', dashboardURL).attr('target', '#').text('dashboard')));

                    let progress = document.getElementById('sens_analysis_progress');
                    progress.innerHTML =  '';

                    essim_sensitivity_plugin.attempt = 0;
                    if (essim_sensitivity_plugin.kpis)
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

        setTimeout(essim_sensitivity_plugin.monitor_sensitivity_analysis_progress, 1000);
    }

    select_kpis_window() {
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

    select_period_window() {
        $('#essim_sensitivity_title').text('ESSIM Sensitivity Analysis - Select simulation period');
        let $div = $('#essim_sens_content_div');
        $div.empty();

        $div.append($('<p>').text('Still needs implementation - defaults to year 2015'));

        let $button_div = $('#essim_sens_button_div');
        $button_div.empty()
        let $button = $('<button>').text('Next');
        $button.click(function () { essim_sensitivity_plugin.select_kpis_window(); });
        $button_div.append($button);
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
            essim_sensitivity_plugin.add_row_to_table(asset_info);
        }

        $table.append($thead);
        $table.append($tbody);

        $content_div.append($table);

        let $button_div = $('<div>').attr('id', 'essim_sens_button_div').addClass('sidebar-div');
        $div.append($button_div);
        let $button = $('<button>').text('Next');
        $button.click(function () { essim_sensitivity_plugin.select_period_window(); });
        $button_div.append($button);

        return $div;
    }

    // Finds the first asset attribute of type EInt
    find_asset_attr_eint(asset_info, attrs_sorted) {
        for (let i=0; i<attrs_sorted.length; i++) {
            if (attrs_sorted[i].type === 'EInt') {
                asset_info.attr = attrs_sorted[i].name;
                let value = attrs_sorted[i].value;

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
            essim_sensitivity_plugin.add_row_to_table(asset_info);
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

        console.log(selected_option);

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
                            let value = attrs[j].value;

                            // TODO: fix integer assumption
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
    }

    change_start_step_stop(param, asset_id) {
        let $input = $('#input_'+param+'_'+asset_id);

        let value = $input.val();
        console.log(value);

        for (let i=0; i<essim_sensitivity_plugin.asset_list.length; i++) {
            if (essim_sensitivity_plugin.asset_list[i].id === asset_id) {
                essim_sensitivity_plugin.asset_list[i]['attr_'+param] = value;
            }
        }
    }

    add_row_to_table(asset_info) {
        let $tbody = $('#essim_sensitivity_table_body');

        let asset_id = asset_info.id;
        let asset_name = asset_info.name;
        let asset_attr = asset_info.attr;
        let asset_attrs = asset_info.attrs;
        let asset_attr_start = asset_info.attr_start;
        let asset_attr_step = asset_info.attr_step;
        let asset_attr_end = asset_info.attr_end;
        let num_steps = ((asset_attr_end - asset_attr_start) / asset_attr_step) + 1;
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
            .append($('<td>').text(num_steps.toString()))
            .append($('<td>').text('No'));
        $tbody.append($row);
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

var essim_sensitivity_plugin;   // global variable for the Vesta plugin

$(document).ready(function() {
    extensions.push(function(event) { ESSIM_sensitivity.create(event) });
});
