function formatN(n) {
    // console.log("n: ", n);
    var nn = n.toExponential(2).split(/e/);
    // console.log("nn: ", nn)
    var u = Math.floor(+nn[1] / 3);
    // console.log("u: ", u)
    return Math.round(((nn[0] * Math.pow(10, +nn[1] - u * 3)) + Number.EPSILON) * 100) / 100 + ['p', 'n', 'u', 'm', '', 'k', 'M', 'G', 'T', 'P'][u+4];
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
            this.createChart(kpi_info, this.charts_div);
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
    createChart: function(kpi_info, chart_box) {
        console.log(kpi_info);
        var chart_div = L.DomUtil.create('div', 'chart-container', chart_box);
        let canvas = L.DomUtil.create('canvas', '', chart_div);
        let ctx = canvas.getContext('2d');

        let type = null;
        let labels = [];
        let datasets = [];
        let options = {};

        // TODO: fix more than 1 kpi_info
        if (kpi_info[0].type === 'Distribution') {
            let kpi_item = null;
            let dataset_dict = {};
            for (let i=0; i<kpi_info.length; i++) {
                kpi_item = kpi_info[i];
                labels.push(i.toString());      // must be es name (or something like that)

                for (let i=0; i<kpi_item.distribution.length; i++) {
                    let distr_part = kpi_item.distribution[i]

                    if (distr_part.label in dataset_dict)
                        dataset_dict[distr_part.label].data.push(distr_part.value)
                    else {
                        dataset_dict[distr_part.label] = {
                            label: distr_part.label,
                            backgroundColor: this.get_bg_color(i),
                            data: [distr_part.value]
                        };
                    }
                }
            }

            for (let lbl in dataset_dict) {
                datasets.push(dataset_dict[lbl]);
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
                        stacked: true,
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
                    labels.push('Still to go...');
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