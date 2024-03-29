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
            let kpi_info = data['kpi_info'];    // kpi_info: {'kpis_description': ..., 'kpi_list': ...}
            // Store or replace the kpi info for this energy system
            set_kpi_info(es_id, {scope: scope, kpis_description: kpi_info.kpis_description, kpi_list: kpi_info.kpi_list});

            // Don't show the old small KPI dialog anymore by default.
            // There is an AnnounceKPI control, that allows to open the bigger dashboard.
            // The old small KPI dialog can still be opened from the menu
            // kpis.show_all_kpis();
        });

        socket.on('show_kpis', function() {
            kpis.show_all_kpis();
        });
    }

    show_all_kpis() {
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
            kpicharts.addTo(map);
        }
    }

    static create(event) {
        if (event.type === 'client_connected') {
            kpis = new KPIs();
            return kpis;
        }
    }

    // This function generates a dictionairy with the KPI names as keys
    // Values are arrays of kpis in the different energysystems with that name
    // Assumes for now that KPIs can be distinguished based on their names
    preprocess_all_kpis(kpi_data) {
        let kpi_dict = {};
        for (let es_id in kpi_data) {
            let kpis_per_es = kpi_data[es_id];
            let kpi_scope = kpis_per_es['scope'];
            let kpis_description = kpis_per_es['kpis_description'];
            let kpi_list = kpis_per_es['kpi_list'];
            for (let i=0; i<kpi_list.length; i++) {
                let kpi_name = kpi_list[i].name;
                let kpi_es_sim_id = es_id;
                // For sensitivity analysis purposes the same KPI is calculated for the same energy system
                // In order to visualize them all, distinguish them based in simulationID
                if ('sim_id' in kpi_list[i])
                    kpi_es_sim_id += '-' + kpi_list[i]['sim_id']

                for (let j=0; j<kpi_list[i].sub_kpi.length; j++) {
                    let kpi_info = kpi_list[i].sub_kpi[j];
                    kpi_info['es_id'] = kpi_es_sim_id;
                    kpi_info['scope'] = kpi_scope;
                    kpi_info['kpis_description'] = kpis_description;

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