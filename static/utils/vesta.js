class Vesta {
    constructor() {
        this.initSocketIO();
    }

    initSocketIO() {
        console.log("Registering socket io bindings for Vesta plugin")

        socket.on('vesta_restrictions_data', function(vesta_data) {
            console.log(vesta_data);
            let sidebar_ctr = sidebar.getContainer();
            sidebar_ctr.innerHTML = vesta_data['area_id'];
            sidebar.show();
        });
    }

    set_area_restrictions(event, id) {
        socket.emit('vesta_area_restrictions', id);
    }

    static create(event) {
        if (event.type === 'client_connected') {
            vesta_plugin = new Vesta();
            return vesta_plugin;
        }
        if (event.type === 'add_contextmenu') {
            let layer = event.layer;
            let layer_type = event.layer_type;
            let id = layer.id;
            if (layer_type === 'area') {
                layer.options.contextmenuItems.push({
                    text: 'set VESTA restrictions',
                    icon: resource_uri + 'icons/Vesta.png',
                    callback: function(e) {
                        vesta_plugin.set_area_restrictions(e, id);
                    }
                });
            }
        }
    }
}

var vesta_plugin;   // global variable for the Vesta plugin

$(document).ready(function() {
    extensions.push(function(event) { Vesta.create(event) });
});