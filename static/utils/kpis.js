class KPIs {
    constructor() {
        this.initSocketIO();
    }

    initSocketIO() {
        console.log("Registering socket io bindings for KPIs module")

        socket.on('kpis', function(data) {
            console.log("KPIs plugin: kpis SocketIO call");
            console.log(data);
        });
    }

    static create(event) {
        if (event.type === 'client_connected') {
            kpis = new KPIs();
            return kpis;
        }
    }
}

var kpis;

$(document).ready(function() {
    extensions.push(function(event) { KPIs.create(event) });
});