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