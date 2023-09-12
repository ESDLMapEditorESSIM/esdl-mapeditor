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

function formatN(n) {
    // console.log("n: ", n);
    var nn = n.toExponential(2).split(/e/);
    // console.log("nn: ", nn)
    var u = Math.floor(+nn[1] / 3);
    // console.log("u: ", u)
    return Math.round(((nn[0] * Math.pow(10, +nn[1] - u * 3)) + Number.EPSILON) * 100) / 100 + ['p', 'n', 'u', 'm', '', 'k', 'M', 'G', 'T', 'P'][u+4];
}

function createChart(ctx, type, labels, datasets, options) {
    return new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: datasets
        },
        options: options
    });
}

function changeChart(canvas, table_div, chart, ctx, type, labels, datasets, options) {
    let local_options = options;
    if (type == 'doughnut') {
        // Don't show x and y axes in case of a doughut diagram
        delete(local_options.scales);
    }
    chart.destroy();
    $(table_div).hide();
    $(canvas).show();
    return createChart(ctx, type, labels, datasets, local_options);
}

function changeTable(canvas, table_div, distr_or_value, kpi_name, chart, labels, datasets) {
    chart.destroy();
    $(table_div).empty().show();
    $(canvas).hide();

    console.log(labels);
    console.log(datasets);

    $(table_div).append($('<p>').text(kpi_name).addClass('kpi_table_title'));
    let $table = $('<table>').addClass('pure-table pure-table-striped');
    let $tr = $('<tr>').append($('<th>').text('Label'));
    for (let i=0; i<labels.length; i++) {
        $tr.append($('<th>').text(labels[i]));
    }
    let $thead = $('<thead>').append($tr);
    let $tbody = $('<tbody>');
    $table.append($thead);
    $table.append($tbody);

    for (let i=0; i<datasets.length; i++) {
        let $tr = $('<tr>');
        if (distr_or_value === 'Distribution') {
            $tr.append($('<td>').text(datasets[i].label));
        } else {
            $tr.append($('<td>').text(i.toString()));
        }
        for (let j=0; j<datasets[i].data.length; j++) {
            let value = datasets[i].data[j];
            if (typeof value == 'number') {
                value = formatN(value);
            }
            $tr.append($('<td>').css('text-align', 'right').text(value));
        }
        $tbody.append($tr);
    }

    $(table_div).append($table);
}

L.Control.KPICharts = L.Control.extend({
    options: {
        closeButton: true,
        position: 'bottomright',
        data: []
    },

    initialize: function(placeholder, options) {
        L.setOptions(this, options);
        return this;
    },

    onAdd: function(map) {
        var container = this._container = L.DomUtil.create('div', 'leaflet-kpicharts my-control');
        this._map = map;

        // Create close button and attach it if configured
        if (this.options.closeButton) {
            var close = this._closeButton =
                L.DomUtil.create('a', 'close', container);
            close.innerHTML = '&times;';

            L.DomEvent.on(close, 'click', this.close, this);
        }

        var title = L.DomUtil.create('div', 'title', container);
        title.innerHTML = 'KPIs';

        var content = L.DomUtil.create('div', 'content', container);
        var control_div = L.DomUtil.create('div', '', content);
        var charts_div = L.DomUtil.create('div', '', content);

        this.charts_div = charts_div;
        this.draw_KPIs();
//        for (let i=0; i<this.options.data.length; i++) {
//            this.createChart(this.options.data[i], chart_box);
//        }


        // Make sure w/e don't drag the map when we interact with the content
        var stop = L.DomEvent.stopPropagation;
        var fakeStop = L.DomEvent._fakeStop || stop;
        L.DomEvent
            .on(container, 'contextmenu', stop)
            .on(container, 'click', fakeStop)
            .on(container, 'mousedown', stop)
            .on(container, 'touchstart', stop)
            .on(container, 'dblclick', fakeStop)
            .on(container, 'mousewheel', stop)
            .on(container, 'MozMousePixelScroll', stop);

        return container;
    },

    onRemove: function(map) {
        console.log('KPICharts.onRemove()')
        var container = this._container;

        // If the control is visible, hide it before removing it.
        this.hide();

        if (this._closeButton) {
            var close = this._closeButton;

            L.DomEvent.off(close, 'click', this.close, this);
        }

        // Unregister events to prevent memory leak
        var stop = L.DomEvent.stopPropagation;
        var fakeStop = L.DomEvent._fakeStop || stop;
        L.DomEvent
            .off(container, 'contextmenu', stop)
            .off(container, 'click', fakeStop)
            .off(container, 'mousedown', stop)
            .off(container, 'touchstart', stop)
            .off(container, 'dblclick', fakeStop)
            .off(container, 'mousewheel', stop)
            .off(container, 'MozMousePixelScroll', stop);

        // TODO: what is the proper way of doing this?
        kpicharts = null;
    },

    close: function() {
        this._map.removeControl(this);
    },
    show: function() {
        this._container.style.visibility = 'visible';
    },
    hide: function() {
        this._container.style.visibility = 'hidden';
    },
    set_data: function(data) {
        this.options.data = data;
    },
    update_data: function(data) {
        this.set_data(data);
        this.draw_KPIs();
    },
    draw_KPIs: function() {
        $(this.charts_div).empty();

        for (let kpi_name in this.options.data) {
            let kpi_info = this.options.data[kpi_name];
            this.createKPIvis(kpi_info, this.charts_div);
        }
    },
    get_bg_color: function(idx) {
        let colors = [
            'rgba(255, 99, 132, 0.2)',
            'rgba(54, 162, 235, 0.2)',
            'rgba(255, 206, 86, 0.2)',
            'rgba(75, 192, 192, 0.2)',
            'rgba(153, 102, 255, 0.2)',
            'rgba(255, 159, 64, 0.2)'
        ];
        return colors[idx];
    },
    createKPIvis: function(kpi_info, chart_box) {
        // This function is being called with a parameter kpi_info that is an array with objects for each loaded
        // energy system. It allows side-by-side comparison of different energy system scenarios. The format of the
        // data is shown below

        console.log(kpi_info);
        // Example KPI object (with just one energy system)
        //    0:
        //        distribution: Array(3)
        //            0: {label: "Warmte", value: 3.3085894444545933e-13}
        //            1: {label: "Electricity", value: 5.774796217681515e-11}
        //            2: {label: "Aardgas", value: 1.3353686339893772e-10}
        //        es_id: "2d8533b2-6b7e-4a70-a6e2-a9720e587d7b"
        //        name: "Total excess production [Percentages]"
        //        scope: "essim kpis"
        //        type: "Distribution"
        //        unit: "Percentages"

        // Other example
        //  0:
        //      es_id: "926fa9a2-9f04-45a8-adfd-813d29acd6c0"
        //      name: "Energy neutrality"
        //      scope: "Untitled Area"
        //      targets: Array(1)
        //          0: {year: 2050, value: 100}
        //      type: "Int"
        //      unit: "N/A"
        //      value: 23

        var chart_div = L.DomUtil.create('div', 'chart-container', chart_box);
        let ctrl_div = L.DomUtil.create('div', '', chart_div);
        let table_div = L.DomUtil.create('div', '', chart_div);
        let canvas = L.DomUtil.create('canvas', '', chart_div);
        let ctx = canvas.getContext('2d');

        let type = null;
        let labels = [];
        let datasets = [];
        let options = {};

        // TODO: we now assume that the same KPI in different energy systems has the same type
        let distr_or_value = kpi_info[0].type;

        if (distr_or_value === 'Distribution') {
            let kpi_item = null;
            let dataset_dict = {};
// This works for bar charts, but not for doughnuts
// For barcharts, energysystems are shown side by side
// ---------------------------------------------------
//            for (let i=0; i<kpi_info.length; i++) {
//                kpi_item = kpi_info[i];
//                labels.push(i.toString());      // must be es name (or something like that)
//
//                for (let i=0; i<kpi_item.distribution.length; i++) {
//                    let distr_part = kpi_item.distribution[i]
//
//                    if (distr_part.label in dataset_dict)
//                        dataset_dict[distr_part.label].data.push(distr_part.value)
//                    else {
//                        dataset_dict[distr_part.label] = {
//                            label: distr_part.label,
//                            backgroundColor: this.get_bg_color(i),
//                            data: [distr_part.value]
//                        };
//                    }
//                }
//            }
//
//            for (let lbl in dataset_dict) {
//                datasets.push(dataset_dict[lbl]);
//            }

// This works both for bar charts and doughnuts
// For barcharts, energysystems are mixed per distribution label
// ---------------------------------------------------
            // Create a dict with keys of all distribution labels for the kpi for all energy systems
            let distr_labels_dict = {}
            let num_distr_labels = 0
            for (let i=0; i<kpi_info.length; i++) {
                kpi_item = kpi_info[i];

                for (let j=0; j<kpi_item.distribution.length; j++) {
                    if (!(kpi_item.distribution[j].label in distr_labels_dict)) {
                        distr_labels_dict[kpi_item.distribution[j].label] = {
                            backgroundColor: this.get_bg_color(num_distr_labels),
                            data: {}        // key=es, data=value for that kpi for that es
                        }
                        num_distr_labels = num_distr_labels + 1;
                    }
                }
            }
            console.log(distr_labels_dict);

            // Fill in energy system data
            for (let i=0; i<kpi_info.length; i++) {
                kpi_item = kpi_info[i];

                for (let j=0; j<kpi_item.distribution.length; j++) {
                    let distr_part = kpi_item.distribution[j]
                    distr_labels_dict[distr_part.label]['data'][kpi_item['es_id']] = distr_part.value;
                }
            }

            // Convert to list to preserve order (Is this required?)
            let label_info_array = [];
            let bgColor_array = [];
            for (let lbl in distr_labels_dict) {
                labels.push(lbl);
                label_info_array.push(distr_labels_dict[lbl]);
                bgColor_array.push(distr_labels_dict[lbl]['backgroundColor'])
            }

            // Now transpose the data structure to a format that chartjs accepts
            // Iterate over all EnergySystems
            for (let i=0; i<kpi_info.length; i++) {
                kpi_item = kpi_info[i];

                let dataset = {}
                // dataset['label'] = i.toString();  // kpi_item['es_id'];
                let label = kpi_item['kpis_description'];
                if (!label) {
                    label = i.toString();   // if no kpis_description was given, use an index
                } else {
                    // make sure labels are not longer than 10 characters
                    if (label.length > 10) {
                        label = label.substring(0, 7) + '...';
                    }
                }
                dataset['label'] = label;

                let data = new Array(labels.length);
                data = data.fill(0);
                for (let lbl_info in label_info_array) {
                    for (let es_id in label_info_array[lbl_info]['data']) {
                        if (es_id == kpi_item['es_id']) {
                            data[lbl_info] = label_info_array[lbl_info]['data'][es_id];
                        }
                    }
                }
                dataset['data'] = data;
                dataset['backgroundColor'] = bgColor_array;
                datasets.push(dataset)
            }

            type = 'bar'
            options = {
                legend: {
                    display: true,
                    position: 'right',
                    labels: {
                        boxWidth: 10,
                        fontSize: 9
                    }
                },
                scales: {
 //                   xAxes: [{
 //                       stacked: false,
 //                   }],
                    yAxes: [{
 //                       stacked: true,
                        ticks: {
                            beginAtZero: true,
//                            maxTicksLimit: 6,
                            callback: function(value) {
                                return formatN(value).toString();
                            }
                        }
                    }]
                },
                title: {
                    display: true,
                    text: kpi_item.name
                }
            }
        } else {
            labels = ['Current value'];

            for (let i=0; i<kpi_info.length; i++) {
                kpi_item = kpi_info[i];
                let target = null;
                if ('targets' in kpi_item) {
                    if (kpi_item.targets.length > 0) {
                        target = kpi_item.targets[0].value;
                        type = 'doughnut';
                    } else {
                        type = 'bar';
                    }
                } else {
                    type = 'bar';
                }

                if (type === 'bar') {
                    data = [kpi_item.value];
                } else {
                    data = [kpi_item.value, target-kpi_item.value];
                    if (labels.length < 2) { labels.push('Still to go...'); }
                }

                datasets.push({
                    label: labels,
                    data: data,
                    backgroundColor: [this.get_bg_color(0), this.get_bg_color(1)]
                });
            }

            options = {
                legend: {
                    display: false,
                },
                title: {
                    display: true,
                    text: kpi_item.name
                },
                scales: {
                    yAxes: [{
                        ticks: {
                            beginAtZero: true,
//                            maxTicksLimit: 6,
                            callback: function(value) {
                                return formatN(value).toString();
                            }
                        }
                    }]
                }
            }
        }

        let chart = createChart(ctx, type, labels, datasets, options)

        if (distr_or_value === 'Distribution')
            $(ctrl_div).append($('<button>').addClass('btn')
                .append($('<i>').addClass('fas fa-chart-pie').css('color', 'black'))
                .click( function(e) { chart = changeChart(canvas, table_div, chart, ctx, 'doughnut', labels, datasets, options); }));
        $(ctrl_div).append($('<button>').addClass('btn')
            .append($('<i>').addClass('fas fa-chart-bar').css('color', 'black'))
            .click( function(e) { chart = changeChart(canvas, table_div, chart, ctx, 'bar', labels, datasets, options); }));
        if (distr_or_value === 'Distribution')
            $(ctrl_div).append($('<button>').addClass('btn')
                .append($('<i>').addClass('fas fa-chart-line').css('color', 'black'))
                .click( function(e) { chart = changeChart(canvas, table_div, chart, ctx, 'line', labels, datasets, options); }));
        $(ctrl_div).append($('<button>').addClass('btn')
            .append($('<i>').addClass('fas fa-table').css('color', 'black'))
            .click( function(e) { changeTable(canvas, table_div, distr_or_value, kpi_info[0].name, chart, labels, datasets); }));
    },
});

L.control.kpicharts = function (placeholder, options) {
    return new L.Control.KPICharts(placeholder, options);
};