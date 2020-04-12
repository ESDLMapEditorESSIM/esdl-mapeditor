class LoadDurationCurve {
    constructor() {
        this.initSocketIO();
    }

    initSocketIO() {
        console.log("Registering socket io bindings for LoadDurationCurve")

        socket.on('ldc-data', function(ldc_data) {
            ldc_control = L.control.load_duration_curve('ldccontrol', {position: 'bottomright', data: ldc_data});
            ldc_control.addTo(map);
        });
    }

    calculate_load_duration_curve(event, id) {
        socket.emit('calculate_load_duration_curve', id);
    }

    static create(event) {
        if (event.type === 'client_connected') {
            load_duration_curve = new LoadDurationCurve();
            return load_duration_curve;
        }
        if (event.type === 'add_contextmenu') {
            let layer = event.layer;
            let id = layer.id;
            layer.options.contextmenuItems.push(
                    { text: 'Load Duration Curve', icon: resource_uri + 'icons/Graph.png', callback: function(e) { load_duration_curve.calculate_load_duration_curve(e, id); } });
        }
    }
}

var load_duration_curve; // global load_duration_curve variable
$(document).ready(function() {
    extensions.push(function(event) { LoadDurationCurve.create(event) });
});