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

class ESStatistics {
    constructor() {
        this.initSocketIO();

        let width = map.getSize();
        this.width = 1200;
        this.height = 750;
        this.x = 10;
        this.y = (width.x/2)-(this.width/2);
    }

    initSocketIO() {
        console.log("Registering socket io bindings for ESStatistics");

        socket.on('tmp', function(data) {
            console.log(data);
        });
    }

    generate_content() {
        let $main_div = $('<div>').addClass('statistics_window').attr('id', 'es_statistics_div');

        show_loader();

        socket.emit('get_es_statistics', function(result) {
//            console.log(result)
            hide_loader();
            $main_div.append(es_statistics.generate_energysystem_info(result));
            $main_div.append(es_statistics.generate_asset_number_info(result));
            $main_div.append(es_statistics.generate_asset_power_info(result));
            $main_div.append(es_statistics.generate_area_info(result));
        });

        return $main_div;
    }

    generate_energysystem_info(info) {
        let $div = $('<div>').append($('<h2>').text('Energy system information'));

        if ('energysystem' in info) {
            let es_info = info['energysystem']

            let $table = $('<table>').addClass('pure-table pure-table-striped').attr('id', 'es_info_table');
            let $thead = $('<thead>').append($('<tr>').append($('<th>').text('Parameter')).append($('<th>')
               .text('Value')));
            let $tbody = $('<tbody>');
            $table.append($thead);
            $table.append($tbody);

            $tbody.append($('<tr>').append($('<td>').text('Energy system ID')).append($('<td>').text(es_info['es_id'])));
            $tbody.append($('<tr>').append($('<td>').text('Energy system name')).append($('<td>').text(es_info['es_name'])));
            $tbody.append($('<tr>').append($('<td>').text('Energy system description')).append($('<td>').text(es_info['es_description'])));
            $tbody.append($('<tr>').append($('<td>').text('Instance ID')).append($('<td>').text(es_info['inst_id'])));
            $tbody.append($('<tr>').append($('<td>').text('Instance name')).append($('<td>').text(es_info['inst_name'])));

            $div.append($table);
        } else {
            $div.append($('<p>').text('No energy system information.'));
        }

        return $div;
    }

    generate_bld_stats(bld_info) {
        if (Object.keys(bld_info).length !== 0) {
            let $table = $('<table>').addClass('pure-table pure-table-striped').attr('id', 'es_info_table');
            let $thead = $('<thead>').append($('<tr>').append($('<th>').text('Type')).append($('<th>')
               .text('Number')).append($('<th>').text('Floor area')));
            let $tbody = $('<tbody>');
            $table.append($thead);
            $table.append($tbody);

            for (key in bld_info) {
                let type_info = bld_info[key];

                $tbody.append(
                    $('<tr>').append($('<td>').text(key)).append($('<td>').text(type_info['number'])).append($('<td>').text(type_info['floor_area']))
                );
            }

            return $table;
        } else {
            return $('<p>').text('No information');
        }
    }

    generate_spatial_info(spatial_info) {
        if (Object.keys(spatial_info).length !== 0) {
            let $table = $('<table>').addClass('pure-table pure-table-striped').attr('id', 'es_info_table');
            let $thead = $('<thead>').append($('<tr>')
                .append($('<th>').text('Type'))
                .append($('<th>').text('Number'))
                .append($('<th>').text('Area [m2] (approx.)')
                  .attr('title', 'Area calculations are not perfect because circles must be approximated by a polygon'))
                .append($('<th>').text('Non-overlapping area [m2] (approx.)')
                  .attr('title', 'Area calculations are not perfect because circles must be approximated by a polygon')));
            let $tbody = $('<tbody>');
            $table.append($thead);
            $table.append($tbody);

            for (let key in spatial_info['number']) {
                let number_info = spatial_info['number'][key];
                let area_info = '';
                if (key in spatial_info['area']) {
                    area_info = spatial_info['area'][key];
                }
                let non_overlapping_area_info = '';
                if (key in spatial_info['area']) {
                    non_overlapping_area_info = spatial_info['non_overlapping'][key];
                }
                $tbody.append(
                    $('<tr>')
                      .append($('<td>').text(key))
                      .append($('<td>').text(number_info))
                      .append($('<td>').text(area_info))
                      .append($('<td>').text(non_overlapping_area_info))
                );
            }

            return $table;
        } else {
            return $('<p>').text('No information');
        }    }

    generate_area_tables(div, area_info, level) {
        let $p = $('<p>');
        let $table = $('<table>').addClass('pure-table pure-table-striped').attr('id', 'es_info_table');
        let $thead = $('<thead>').append($('<tr>').append($('<th>').text('Parameter')).append($('<th>')
           .text('Value')));
        let $tbody = $('<tbody>');
        $table.append($thead);
        $table.append($tbody);

        $tbody.append($('<tr>').append($('<td>').text('Area ID')).append($('<td>').text(area_info['id'])));
        $tbody.append($('<tr>').append($('<td>').text('Area name')).append($('<td>').text(area_info['name'])));
        $tbody.append($('<tr>').append($('<td>').text('Area scope')).append($('<td>').text(area_info['scope'])));
        $tbody.append($('<tr>').append($('<td>').text('Area level')).append($('<td>').text(level.toString())));
        let sub_areas = area_info['sub_areas'];
        $tbody.append($('<tr>').append($('<td>').text('Number of sub areas')).append($('<td>').text(sub_areas.length.toString())));
        $tbody.append($('<tr>').append($('<td>').text('Building statistics')).append($('<td>').append(es_statistics.generate_bld_stats(area_info['bld_info']))));
        $tbody.append($('<tr>').append($('<td>').text('Spatial information')).append($('<td>').append(es_statistics.generate_spatial_info(area_info['spatial_info']))));

        div.append($p.append($table));

        for (let sub_area_idx in area_info.sub_areas) {
            es_statistics.generate_area_tables(div, area_info.sub_areas[sub_area_idx], level+1);
        }
    }

    generate_area_info(info) {
        let $div = $('<div>').append($('<h2>').text('Area information'));

        if ('areas' in info) {
            let area_info = info['areas']
            es_statistics.generate_area_tables($div, area_info, 1);
        } else {
            $div.append($('<p>').text('No area information.'));
        }

        return $div;
    }

    generate_asset_number_info(info) {
        let $div = $('<div>').append($('<h2>').text('Total number of assets'));

        if ('number_of_assets' in info) {
            let asset_cnt_info = info['number_of_assets']

            let $table = $('<table>').addClass('pure-table pure-table-striped').attr('id', 'number_assets_table');
            let $thead = $('<thead>').append($('<tr>').append($('<th>').text('Asset')).append($('<th>')
               .text('Number')).append($('<th>').text('aggregationCount')));
            let $tbody = $('<tbody>');
            $table.append($thead);
            $table.append($tbody);

            for (let asset_cnt_idx in Object.entries(asset_cnt_info)) {
                let asset = Object.entries(asset_cnt_info)[asset_cnt_idx];
                $tbody.append($('<tr>')
                    .append($('<td>').text(asset[0]))
                    .append($('<td>').css('text-align','right').text(asset[1]['cnt'].toString()))
                    .append($('<td>').css('text-align','right').text(asset[1]['aggr_cnt'].toString()))
                );
            }
            $div.append($table);
        } else {
            $div.append($('<p>').text('No information about the total number of assets.'));
        }

        return $div;
    }

    formatN(n) {
        // console.log("n: ", n);
        var nn = n.toExponential(2).split(/e/);
        // console.log("nn: ", nn)
        var u = Math.floor(+nn[1] / 3);
        // console.log("u: ", u)
        return Math.round(((nn[0] * Math.pow(10, +nn[1] - u * 3)) + Number.EPSILON) * 100) / 100 + ' '+['p', 'n', 'u', 'm', '', 'k', 'M', 'G', 'T', 'P'][u+4];
    }

    generate_asset_power_info(info) {
        let $div = $('<div>').append($('<h2>').text('Total installed capacity of assets'));

        if ('power_of_assets' in info) {
            let asset_power_info = info['power_of_assets']

            let $table = $('<table>').addClass('pure-table pure-table-striped').attr('id', 'capacity_assets_table');
            let $thead = $('<thead>').append($('<tr>').append($('<th>').text('Asset')).append($('<th>')
               .text('Capacity')));
            let $tbody = $('<tbody>');
            $table.append($thead);
            $table.append($tbody);

            for (let asset_cnt_idx in Object.entries(asset_power_info)) {
                let asset = Object.entries(asset_power_info)[asset_cnt_idx];
                let power = (this.formatN(asset[1])).toString()+'W';
                $tbody.append($('<tr>').append($('<td>').text(asset[0])).append($('<td>').css('text-align','right').text(power)));
            }
            $div.append($table);
        } else {
            $div.append($('<p>').text('No information about the total installed capacity of assets.'));
        }

        return $div;
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
        dialog.setTitle('Energy system statistics');
        $('.leaflet-control-dialog-contents').scrollTop(0);
        dialog.open();
    }

    // all globals in here
    static handle_dialog_resize_move() {
        es_statistics.width = dialog.options.size[0];
        es_statistics.height = dialog.options.size[1];
        es_statistics.x = dialog.options.anchor[0];
        es_statistics.y = dialog.options.anchor[1];
    }

    static create(event) {
        if (event.type === 'client_connected') {
            es_statistics = new ESStatistics();
            map.on('dialog:resizeend', ESStatistics.handle_dialog_resize_move);
            map.on('dialog:moving', ESStatistics.handle_dialog_resize_move);
            map.on('dialog:closed', function(e) {
                socket.emit('app_settings_closed');
            });
            return es_statistics;
        }
    }
}

var es_statistics; // global es_statistics variable
$(document).ready(function() {
    extensions.push(function(event) { ESStatistics.create(event) });
});