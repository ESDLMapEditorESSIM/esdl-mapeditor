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
            // Store or replace the kpi info for this energy system
            set_kpi_info(es_id, {scope: scope, kpi_list: kpi_list});

            // Retrieve kpi info for all energy systems
            let all_kpi_data = get_all_kpi_info();
//            console.log(all_kpi_data);
//            {926fa9a2-9f04-45a8-adfd-813d29acd6c0: {…}}
//                926fa9a2-9f04-45a8-adfd-813d29acd6c0:
//                    kpi_list: Array(3)
//                        0: {id: "e95eadbd-3d41-41cc-82e1-eddf1072f490", name: "Energy neutrality", value: 23, type: "Int", targets: Array(1)}
//                        1: {id: "573ee9ee-43fd-4d98-a444-d1c5dcbff595", name: "Number of WindTurbines", value: 7, type: "Int", targets: Array(1)}
//                        2: {id: "08659497-f1ea-4763-91e9-d8d330449454", name: "Aandeel energiedragers", type: "Distribution", distribution: Array(3)}
//                        length: 3
//                    scope: "Untitled Area"

            let kpi_data = kpis.preprocess_all_kpis(all_kpi_data);
//            console.log(kpi_data);
//            let kpi_data = kpis.create_kpi_chart_data(kpi_list);
//            console.log(kpi_data);
//            (3) [{…}, {…}, {…}]
//                0: {id: "e95eadbd-3d41-41cc-82e1-eddf1072f490", name: "Energy neutrality", type: "Int", value: 23, targets: Array(1)}
//                1: {id: "573ee9ee-43fd-4d98-a444-d1c5dcbff595", name: "Number of WindTurbines", type: "Int", value: 7, targets: Array(1)}
//                2: {id: "08659497-f1ea-4763-91e9-d8d330449454", name: "Aandeel energiedragers", type: "Distribution", distribution: Array(3)}
//                length: 3

            if (kpicharts == null) {
                kpicharts = L.control.kpicharts('kpicharts', {position: 'bottomright', data: kpi_data});
                kpicharts.addTo(map);
            } else {
                kpicharts.update_data(kpi_data);
            }
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

    // This function generates a dictionairy with the KPI names as keys
    // Values are arrays of kpis in the different energysystems with that name
    // Assumes for now that KPIs can be distinguished based on their names
    preprocess_all_kpis(kpi_data) {
        let kpi_dict = {};
        for (let es_id in kpi_data) {
            let kpis_per_es = kpi_data[es_id];
            let kpi_scope = kpis_per_es['scope'];
            let kpi_list = kpis_per_es['kpi_list'];
            for (let i=0; i<kpi_list.length; i++) {
                let kpi_name = kpi_list[i].name;

                for (let j=0; j<kpi_list[i].sub_kpi.length; j++) {
                    let kpi_info = kpi_list[i].sub_kpi[j];
                    kpi_info['es_id'] = es_id;
                    kpi_info['scope'] = kpi_scope;

                    if (kpi_info['name'] in kpi_dict)
                        kpi_dict[kpi_info['name']].push(kpi_info)
                    else
                        kpi_dict[kpi_info['name']] = [kpi_info];
                }
            }
        }
        return kpi_dict;
    }
}

var kpis;

$(document).ready(function() {
    extensions.push(function(event) { KPIs.create(event) });
});