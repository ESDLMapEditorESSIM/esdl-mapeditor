var kpi_colors = ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99','#b15928']
var num_colors = 12

L.Control.ESSIMKPIs = L.Control.extend({
    options: {
        closeButton: true,
        position: 'bottomright',
        data: []
    },

    initialize: function(placeholder, options) {
        L.setOptions(this, options);
        console.log('-------------------------------------------------------------');
        console.log(options);
        console.log('-------------------------------------------------------------');
        return this;
    },

    onAdd: function(map) {
        console.log('ESSIMKPIs.onAdd()')
        var container = this._container = L.DomUtil.create('div', 'leaflet-essim-kpi my-control');
        this._map = map;

        // Create close button and attach it if configured
        if (this.options.closeButton) {
            var close = this._closeButton =
                L.DomUtil.create('a', 'close', container);
            close.innerHTML = '&times;';

            L.DomEvent.on(close, 'click', this.close, this);
        }

        var title = L.DomUtil.create('div', 'title', container);
        title.innerHTML = 'ESSIM KPIs';

        var chart_div = L.DomUtil.create('div', 'content', container);
        this.create_bar_chart(this.options.data, chart_div);

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
        console.log('ESSIMKPIs.onRemove()')
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

    create_labels_vales_colors: function(data) {
        labels = [];
        values = [];
        colors = [];
        for (let i=0; i<data.length; i++) {
            labels.push(data[i]["name"]);
            values.push(data[i]["value"]);
            colors.push(kpi_colors[i % num_colors]);
        }
        return [labels, values, colors];
    },

    create_bar_chart: function(data, chart_div) {
        console.log(data);
        keys = Object.keys(data);

        for (let i=0; i<keys.length; i++) {

            let chart_canvas = L.DomUtil.create('canvas', '', chart_div);
            chart_canvas.setAttribute('id', 'chart-essim-kpis-canvas-'+keys[i]);

            let this_chart_data = data[keys[i]];
            unit = this_chart_data[0]["unit"];

            let res = this.create_labels_vales_colors(this_chart_data);
            let labels = res[0];
            let values = res[1];
            let colors = res[2];

            let bar_chart = new Chart(chart_canvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        label: unit,
                        maxBarThickness: 20,
                        backgroundColor: colors,
                        borderColor: "#3e95cd",
                    }]
                },
                options: {
                    title: {
                        display: true,
                        text: keys[i]
                    },
                    scales: {
                        yAxes: [{
                            ticks: {
                                beginAtZero: true,
                                callback: function(value) {
                                    return formatN(value).toString();
                                }
                            }
                        }]
                    }
                }
            });
        }
    },
});

L.control.essim_kpis = function (placeholder, options) {
    return new L.Control.ESSIMKPIs(placeholder, options);
};