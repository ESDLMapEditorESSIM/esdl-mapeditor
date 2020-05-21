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

//        var chart_box = L.DomUtil.create('div', 'tiny-chartbox', container);
//        chart_box.setAttribute('style', "margin-right: 10px;");
//        for (let i=0; i<this.options.data.length; i++) {
//            this.createChart(this.options.data[i], chart_box);
//        }
        var chart_box = L.DomUtil.create('div', '', container);
        chart_box.setAttribute('style', "margin-right: 10px;");
        for (let i=0; i<this.options.data.length; i++) {
            this.createChart2(this.options.data[i], chart_box);
        }

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
    createChart2: function(kpi_item, chart_box) {
        console.log(kpi_item);
        var chart_div = L.DomUtil.create('div', 'chart-container', chart_box);
        let canvas = L.DomUtil.create('canvas', '', chart_div);
        let ctx = canvas.getContext('2d');

        let type = null;
        let labels = [];
        let datasets = [];
        let options = {};

        if (kpi_item.type === 'Distribution') {
            labels = ['waarde'];
            for (let i=0; i<kpi_item.distribution.length; i++) {
                let distr_part = kpi_item.distribution[i]
                datasets.push({
                    label: distr_part.label,
                    backgroundColor: this.get_bg_color(i),
                    data: [distr_part.percentage]
                });
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
                    xAxes: [{
                        stacked: true,
                    }],
                    yAxes: [{
                        stacked: true
                    }]
                },
                title: {
                    display: true,
                    text: kpi_item.name
                }
            }
        } else {
            type = 'doughnut'
            labels = ['Current value', 'Still to go...'];
            let target = null
            if (kpi_item.targets) {
                target = kpi_item.targets[0].value;
            }
            datasets = [{
                label: labels,
                data: [kpi_item.value, target-kpi_item.value],
                backgroundColor: [this.get_bg_color(0), this.get_bg_color(1)]
            }];
            options = {
                legend: {
                    display: false,
                },
                title: {
                    display: true,
                    text: kpi_item.name
                }
            }
        }

        let chart = new Chart(ctx, {
            type: type,
            data: {
                labels: labels,
                datasets: datasets
            },
            options: options
        });
    },
});

L.control.kpicharts = function (placeholder, options) {
    return new L.Control.KPICharts(placeholder, options);
};