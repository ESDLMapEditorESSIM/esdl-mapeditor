L.Control.KPICharts = L.Control.extend({
    options: {
        closeButton: true,
        position: 'bottomright'
    },

    initialize: function (placeholder, options) {
        L.setOptions(this, options);
        return this;
    },

    onAdd: function (map) {
        console.log('KPICharts.onAdd()')
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

        var chart_box = L.DomUtil.create('div', 'tiny-chartbox', container);
        chart_box.setAttribute('style', "margin-right: 10px;");
        var chart = L.DomUtil.create('div', '', chart_box);
        chart.id = 'windturbines';
        chart.setAttribute('chart-type', 'donut');
        chart.setAttribute('data-chart-max', "37");
        chart.setAttribute('data-chart-segments', '{ "0":["0","12","#55DB2E"], "1":["12","25","#19A7F5"] }');
        chart.setAttribute('data-chart-text', "1200/\n3700");
        chart.setAttribute('data-chart-caption', "Wind Turbines");
        makeDonutCharts(chart);

        var chart = L.DomUtil.create('div', '', chart_box);
        chart.id = 'EnergyNeutral';
        chart.setAttribute('chart-type', 'donut');
        chart.setAttribute('data-chart-max', "100");
        chart.setAttribute('data-chart-segments', '{ "0":["0","23","#55DB2E"], "1":["23","77","#CCCCCC"] }');
        chart.setAttribute('data-chart-text', "23%");
        chart.setAttribute('data-chart-caption', "Energy Neutral");
        makeDonutCharts(chart);

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
    },

    close: function() {
        this._map.removeControl(this);
    },
    show: function () {
        this._container.style.visibility = 'visible';
    },
    hide: function () {
        this._container.style.visibility = 'hidden';
    },
});

L.control.kpicharts = function (placeholder, options) {
    return new L.Control.KPICharts(placeholder, options);
};