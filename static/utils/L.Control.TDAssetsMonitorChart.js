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
    return Math.round(((nn[0] * Math.pow(10, +nn[1] - u * 3)) + Number.EPSILON) * 100) / 100 + ['p', 'n', 'u', 'm', '', 'k', 'M', 'G', 'T', 'P'][u + 4];
}

function addColors(data) {
    const colors = [
        "#8b0000",
        "#3e95cd",
        "#008000",
        "#ffa500",
        "#800080",
        "#00ffff",
        "#a52a2a",
        "#00ff00",
        "#ffff00",
        "#e9967a"
    ]
    let data_index = 0;
    for (let key in data["data"]) {
        data["data"][key]["color"] = colors[data_index % colors.length];
        data_index++;
    }
}

L.Control.TDAssetsMonitorChart = L.Control.extend({
    options: {
        closeButton: true,
        position: 'bottomright',
        data: []
    },

    initialize: function (placeholder, options) {
        L.setOptions(this, options);
        this.td_monitor_assets_chart = null;
        console.log(options);
        return this;
    },

    onAdd: function (map) {
        console.log('TDAssetsMonitorChart.onAdd()')
        var container = this._container = L.DomUtil.create('div', 'leaflet-td-assets-monitor my-control');
        this._map = map;

        // Create close button and attach it if configured
        if (this.options.closeButton) {
            var close = this._closeButton =
                L.DomUtil.create('a', 'close', container);
            close.innerHTML = '&times;';

            L.DomEvent.on(close, 'click', this.close, this);
        }

        var title = L.DomUtil.create('div', 'title', container);
        title.innerHTML = 'Assets monitor';

        var ctrl_div = L.DomUtil.create('div', 'td-assets-monitor-control', container);
        this.create_control(ctrl_div);

        var chart_div = L.DomUtil.create('div', 'content', container);
        var chart_canvas = L.DomUtil.create('canvas', '', chart_div);
        chart_canvas.setAttribute('id', 'chart-td-assets-monitor-canvas');
        this.create_td_monitor_assets_chart(this.options.data, chart_canvas);

        // Make sure we don't drag the map when we interact with the content
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

    onRemove: function (map) {
        console.log('TDAssetsMonitorChart.onRemove()')
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
    },

    close: function () {
        this._map.removeControl(this);
        tdAssetsMonitorChart.chart = null;
        socket.emit('td_monitor_asset', {});
    },
    show: function () {
        this._container.style.visibility = 'visible';
    },
    hide: function () {
        this._container.style.visibility = 'hidden';
    },
    update_data: function (data) {
        addColors(data);
        this.td_monitor_assets_chart.data.datasets = [];
        for (let key in data["data"]) {
            this.td_monitor_assets_chart.data.labels = data["data"][key]["data_x"];
            this.td_monitor_assets_chart.data.datasets.push({
                data: data["data"][key]["data_y"],
                label: data["data"][key]["name"],
                borderColor: data["data"][key]["color"],
            });
            this.td_monitor_assets_chart.options.title.text = 'LControlTDAssetsMonitorChart chart - ' + data["time"]
        }
        this.td_monitor_assets_chart.update();
    },
    create_td_monitor_assets_chart: function (data, canvas) {
        let datasets = [];
        let labels;
        addColors(data);
        for (let key in data["data"]) {
            labels = data["data"][key]["data_x"];
            datasets.push({
                data: data["data"][key]["data_y"],
                label: data["data"][key]["name"],
                borderColor: data["data"][key]["color"],
            });
        }

        this.td_monitor_assets_chart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                title: {
                    display: true,
                    text: 'LControlTDAssetsMonitorChart chart - ' + data["time"]
                },
                scales: {
                    y: {
                        ticks: {
                            callback: function (value) {
                                return formatN(value).toString();
                            }
                        }
                    }
                }
            }
        });
    },

    create_control: function (content_div) {
        let $select_asset = $('<select>').attr('id', 'sel_asset');
        socket.emit('timedimension_get_asset_ids', function (asset_ids) {
            for (let key in asset_ids) {
                let $optgroup = $('<optgroup>').attr('label', key);
                for (let i = 0; i < asset_ids[key].length; i++) {
                    let $option = $('<option>').attr('value', asset_ids[key][i]).text(asset_ids[key][i])
                    $optgroup.append($option);
                }
                $select_asset.append($optgroup);
            }
        });

        $select_asset.change(function () {
            let selected_value = $select_asset.val();
            socket.emit('td_monitor_asset', {'id': selected_value});
        })
        $(content_div).append($select_asset)
    }
});

L.control.td_monitor_assets_chart = function (placeholder, options) {
    return new L.Control.TDAssetsMonitorChart(placeholder, options);
};

class LControlTDAssetsMonitorChart {
    constructor() {
        this.initSocketIO();
        this.chart = null;
    }

    initSocketIO() {
        console.log("Registering socketio bindings for LControlTDAssetsMonitorChart");
        socket.on('td_monitor_asset_data', function (td_monitor_asset_data) {
            if (tdAssetsMonitorChart.chart) {
                tdAssetsMonitorChart.chart.update_data(td_monitor_asset_data);
            } else {
                tdAssetsMonitorChart.chart = L.control.td_monitor_assets_chart(
                    'tdmonitorcontrol',
                    {position: 'bottomright', data: td_monitor_asset_data}
                );
                tdAssetsMonitorChart.chart.addTo(map);
            }
        });
    }

    update_select() {
        console.log('update_select');
    }

    static create(event) {
        if (event.type === 'client_connected') {
            tdAssetsMonitorChart = new LControlTDAssetsMonitorChart();
            return tdAssetsMonitorChart;
        }
    }
}

var tdAssetsMonitorChart; // global tdAssetsMonitorChart variable
$(document).ready(function () {
    extensions.push(function (event) {
        LControlTDAssetsMonitorChart.create(event)
    });
});

