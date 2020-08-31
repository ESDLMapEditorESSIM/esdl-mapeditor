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

class ESSIMKPIs {
    constructor() {
        this.initSocketIO();
    }

    initSocketIO() {
        console.log("Registering socket io bindings for ESSIMKPIs")

        socket.on('essim-kpi-data', function(essim_kpi_data) {
            var essim_kpi_control = L.control.essim_kpis('essim_kpis_control', {position: 'bottomright', data: essim_kpi_data});
            essim_kpi_control.addTo(map);
            hide_loader();
        });
    }

    static create(event) {
        if (event.type === 'client_connected') {
            essim_kpis = new ESSIMKPIs();
            return essim_kpis;
        }
    }
}

var essim_kpis; // global essim_kpis variable

$(document).ready(function() {
    extensions.push(function(event) { ESSIMKPIs.create(event) });
});