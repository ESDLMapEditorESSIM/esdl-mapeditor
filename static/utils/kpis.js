class KPIs {
    constructor() {
        this.initSocketIO();
    }

    initSocketIO() {
        console.log("Registering socket io bindings for KPIs module")

        socket.on('kpis', function(data) {
            console.log("KPIs plugin: kpis SocketIO call");
            console.log(data);

            let es_id = data['es_id'];
            let scope = data['scope'];
            let kpi_list = data['kpi_list'];
            set_kpi_info(es_id, {scope: scope, kpi_list: kpi_list});

            let kpi_data = kpis.create_kpi_chart_data2(kpi_list);
//            console.log(kpi_data);
            kpicharts = L.control.kpicharts('kpicharts', {position: 'bottomright', data: kpi_data});
            kpicharts.addTo(map);
        });
    }

    static create(event) {
        if (event.type === 'client_connected') {
            kpis = new KPIs();
            return kpis;
        }
    }

    // format-number-with-si-prefix.js
    // https://gist.github.com/cho45/9968462
    formatN (n) {
        // console.log("n: ", n);
        var nn = n.toExponential(2).split(/e/);
        // console.log("nn: ", nn)
        var u = Math.floor(+nn[1] / 3);
        // console.log("u: ", u)
        return Math.round(((nn[0] * Math.pow(10, +nn[1] - u * 3)) + Number.EPSILON) * 100) / 100 + ['p', 'n', 'u', 'm', '', 'k', 'M', 'G', 'T', 'P'][u+4];
    }

    create_kpi_chart_data(kpi_list) {
        var kpi_data = []

        for (let idx in kpi_list) {
            let kpi = kpi_list[idx];
            let kpi_donut_value = kpi.value.toString();

            let kpi_donut_max;
            let kpi_donut_delta_to_max;
            let kpi_text;
            if (kpi.targets.length > 0) {
                kpi_donut_max = kpi.targets[0].value.toString();
                kpi_donut_delta_to_max = (kpi.targets[0].value - kpi.value).toString();
                kpi_text = this.formatN(kpi.value) + "/" + this.formatN(kpi.targets[0].value - kpi.value);
            } else {
                kpi_donut_max = kpi_donut_value;
                kpi_donut_delta_to_max = 0;
                kpi_text = this.formatN(kpi.value);
            }

            let kpi_data_id = kpi.name.replace(/ /g, "_");  // id must be unique and without spaces
            kpi_data.push(
                {
                    'id': kpi_data_id,
                    'chart-type': 'donut',
                    'data-chart-max': kpi_donut_max,
                    'data-chart-segments': '{ "0":["0","'+kpi_donut_value+'","#55DB2E"], "1":["'+kpi_donut_value+
                        '","'+kpi_donut_delta_to_max+'","#19A7F5"] }',
                    'data-chart-text': kpi_text,
                    'data-chart-caption': kpi.name
                }
            );
        }

        return kpi_data;
    }

    create_kpi_chart_data2(kpi_list) {
        var kpi_data_list = []

        for (let idx in kpi_list) {
            let kpi = kpi_list[idx];
            let kpi_type = kpi.type;

            let kpi_data = {
                'id': kpi.id,
                'name': kpi.name,
                'type': kpi_type
            }

            if (kpi_type === 'Distribution') {
//                let distr = [];
//                for (let i=0; i<kpi.distribution.length; i++) {
//                    let part = {
//                        'label':  kpi.distribution[i].label,
//                        'percentage': kpi.distribution[i].percentage
//                    };
//                    distr.push(part);
//                }
                kpi_data['distribution'] = kpi.distribution;
            } else {
                kpi_data['value'] = kpi.value;
                kpi_data['targets'] = kpi.targets;
            }

            kpi_data_list.push(kpi_data);
        }

        return kpi_data_list;
    }
}

var kpis;

$(document).ready(function() {
    extensions.push(function(event) { KPIs.create(event) });
});