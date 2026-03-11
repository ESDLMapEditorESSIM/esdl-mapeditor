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

class PortProfileViewer{
    constructor(event) {
        this.init(event);
    }

    init(event) {
        const layer = event.layer;
        const layer_type = event.layer_type;
        const es_id = layer.esid;
        const object_id = layer.id;
        if (layer_type === 'marker' || layer_type === 'line') {
            layer.options.contextmenuItems.push({
                text: 'Port profile viewer',
                icon: 'icons/Graph.png',
                callback: function() {
                    window.activate_port_profile_viewer(es_id, object_id)
                }
            });
        }
    }
}

$(document).ready(function() {
    extensions.push(function(event) {
        if (event.type === 'client_connected') {
            console.log("Registering Port profile viewer plugin");
        }
        if (event.type === 'add_contextmenu') {
            new PortProfileViewer(event);
        }
    });
});
