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
            let layer_type = event.layer_type;
            if (layer_type === 'marker' || layer_type === 'line') {
                layer.options.contextmenuItems.push({
                    text: 'Load Duration Curve',
                    icon: resource_uri + 'icons/Graph.png',
                    callback: function(e) {
                        load_duration_curve.calculate_load_duration_curve(e, id);
                    }
                });
            }
        }
    }
}

var load_duration_curve; // global load_duration_curve variable
$(document).ready(function() {
    extensions.push(function(event) { LoadDurationCurve.create(event) });
});