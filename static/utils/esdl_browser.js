// ESDL Browser


class ESDLBrowser {
    constructor(map, socketio) {
        this.map = map;
        this.socket = socketio;
        this.dialog = undefined;
        console.log("Map:");
        console.log(map);
        this.initSocketIO();
    }

    open_browser(esdl_object_id) {
        this.socket.emit('esdl_browse_get_objectinfo', {'id': esdl_object_id});
    }

    open_browser_with_event(e, id) {
        this.open_browser(id);
    }

    initSocketIO() {
        console.log(this.map)
        let myMap = this.map;
        console.log("Registering socket io bindings for ESDLBrowser")

        this.socket.on('esdl_browse_to', function(data) {
            console.log("ESDL_Brower: SocketIO call");
            console.log(data);

            let contents = ["<p>Yes</p>",
                        "<p>" + data.attributes +" </p>",
                        "<p>" + data.references +" </p>"].join('\n');
            if (this.dialog === undefined) {
                // create dialog
                let options = {
                        size: [ 1600, 700 ],
                        minSize: [ 100, 100 ],
                        maxSize: [ 2000, 200 ],
                        anchor: [ 10, 50 ],
                        initOpen: false
                };

               console.log(`creating dialog`)
               console.log(myMap)
               this.dialog = L.control.dialog(options)
                    .setContent("Hello World")
               myMap.addControl(this.dialog);
               this.dialog.open();
            } else {
                this.dialog.setContent(contents);
                this.dialog.open();
            }

        });
    }

    static create(event, map, socketio) {
        console.log("ESDL Browser create()")

        if (event.type === 'client_connected') {
            console.log(map);
            esdl_browser = new ESDLBrowser(map, socketio);
            return esdl_browser;
        }
        if (event.type === 'add_contextmenu') {
            let layer = event.layer;
            let id = layer.id;
            // console.log('Extension HeatNetwork add_contextmenu for id=' + id)
            layer.options.contextmenuItems.push(
                    { text: 'Edit', icon: resource_uri + 'icons/Edit.png', callback: function(e) { esdl_browser.open_browser_with_event(e, id); } });
        }
    }

}

console.log("HI");
var esdl_browser;
$(document).ready(function() {
    extensions.push(function(event) { ESDLBrowser.create(event, map, socket) });

});