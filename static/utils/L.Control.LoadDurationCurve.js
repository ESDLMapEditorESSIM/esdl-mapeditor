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

L.Control.LoadDurationCurve = L.Control.extend({
    options: {
        closeButton: true,
        position: 'bottomright',
        data: []
    },

    initialize: function(placeholder, options) {
        L.setOptions(this, options);
        console.log(options);
        return this;
    },

    onAdd: function(map) {
        console.log('LoadDurationCurve.onAdd()')
        var container = this._container = L.DomUtil.create('div', 'leaflet-ldc my-control');
        this._map = map;

        // Create close button and attach it if configured
        if (this.options.closeButton) {
            var close = this._closeButton =
                L.DomUtil.create('a', 'close', container);
            close.innerHTML = '&times;';

            L.DomEvent.on(close, 'click', this.close, this);
        }

        var title = L.DomUtil.create('div', 'title', container);
        title.innerHTML = 'Load Duration Curve';

        var chart_div = L.DomUtil.create('div', 'content', container);
        var chart_canvas = L.DomUtil.create('canvas', '', chart_div);
        chart_canvas.setAttribute('id', 'chart-ldc-canvas');
        this.create_ldc_chart(this.options.data, chart_canvas);

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

    onRemove: function(map) {
        console.log('LoadDurationCurve.onRemove()')
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

    close: function() {
        this._map.removeControl(this);
    },
    show: function() {
        this._container.style.visibility = 'visible';
    },
    hide: function() {
        this._container.style.visibility = 'hidden';
    },
    create_ldc_chart: function(data, canvas) {
        let labels = [];
        let power_pos_values = [];
        let power_neg_values = [];
        let power_pos = data["power_pos"]
        let power_neg = data["power_neg"]
        for (let i=0; i<data["ldc_series"].length; i++) {
            labels.push(i*40);
            if (power_pos) power_pos_values.push(power_pos);
            if (power_neg) power_neg_values.push(power_neg);
        }
        asset_name = data["asset_name"];
        if (asset_name == null || asset_name === "") asset_name = "Untitled asset";

        let datasets = [{
            data: data["ldc_series"],
            label: "ldc",
            borderColor: "#3e95cd"
        }]
        if (power_pos) {
            datasets.push({
                data: power_pos_values,
                label: "power",
                borderColor: "#ff0000",
                pointRadius: 0
            });
        }
        if (power_neg) {
            datasets.push({
                data: power_neg_values,
                label: "power",
                borderColor: "#ff0000",
                pointRadius: 0
            });
        }

        var ldc_chart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                title: {
                    display: true,
                    text: 'Load Duration Curve - ' + asset_name
                },
                scales: {
                    yAxes: [{
                        ticks: {
                            callback: function(value) {
                                return formatN(value).toString();
                            }
                        }
                    }]
                }
            }
        });
    },
});

L.control.load_duration_curve = function (placeholder, options) {
    return new L.Control.LoadDurationCurve(placeholder, options);
};