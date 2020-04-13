L.Control.KPICharts = L.Control.extend({
    options: {
        closeButton: true,
        position: 'bottomright',
        data: []
    },

    initialize: function(placeholder, options) {
        L.setOptions(this, options);
//        console.log(options);
        return this;
    },

    onAdd: function(map) {
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

        for (let i=0; i<this.options.data.length; i++) {
            this.createChart(this.options.data[i], chart_box);
        }

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
    show: function() {
        this._container.style.visibility = 'visible';
    },
    hide: function() {
        this._container.style.visibility = 'hidden';
    },
    set_data: function(data) {
        self.data = data;
    },
    createChart: function(kpi_item, chart_box) {
        var chart = L.DomUtil.create('div', '', chart_box);
        for (let key in kpi_item) {
            chart.setAttribute(key, kpi_item[key]);
        }
        makeDonutCharts(chart);
    },
});

L.control.kpicharts = function (placeholder, options) {
    return new L.Control.KPICharts(placeholder, options);
};