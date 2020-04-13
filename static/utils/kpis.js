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

            let kpi_data = kpis.create_kpi_chart_data(kpi_list);
            console.log(kpi_data);
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

    create_kpi_chart_data(kpi_list) {
        var kpi_data = []

        for (let idx in kpi_list) {
            let kpi = kpi_list[idx];
            let kpi_donut_max = kpi.targets[0].ambition.toString();
            let kpi_donut_value = kpi.value.toString();
            let kpi_donut_delta_to_max = (kpi.targets[0].ambition - kpi.value).toString();
            let kpi_data_id = kpi.name.replace(/ /g, "_");  // id must be unique and without spaces
            kpi_data.push(
                {
                    'id': kpi_data_id,
                    'chart-type': 'donut',
                    'data-chart-max': kpi_donut_max,
                    'data-chart-segments': '{ "0":["0","'+kpi_donut_value+'","#55DB2E"], "1":["'+kpi_donut_value+
                        '","'+kpi_donut_delta_to_max+'","#19A7F5"] }',
                    'data-chart-text': kpi_donut_value + "/" + kpi_donut_max,
                    'data-chart-caption': kpi.name
                }
            );
        }

        return kpi_data;
    }
}

var kpis;

$(document).ready(function() {
    extensions.push(function(event) { KPIs.create(event) });
});