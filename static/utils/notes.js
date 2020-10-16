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

class Notes {
    constructor() {
        this.initSocketIO();
    }

    initSocketIO() {
        console.log("Registering socket io bindings for ESDL Notes extension")

        // ------------------------------------------------------------------------------------------------------------
        //  Add notes on the map
        // ------------------------------------------------------------------------------------------------------------
        socket.on('add_notes', function(options) {
            // coords = {'lng': map_location.lon, 'lat': map_location.lat}
            // {'id': n.id, 'location': coords, 'title': n.title, 'text': n.text, 'author': n.author, 'date': n.date}
            let list = options['notes_list'];
            let add_to_building = options['add_to_building'];
            let es_id = options['es_id'];

            let es_bld_id = es_id;
            if (add_to_building) {
               es_bld_id = bld_edit_id;
            }

            for (let i = 0; i<list.length; i++) {
                notes.add_note_to_map(list[i], es_bld_id)
            }

            $('.notes-img').tooltip({
                content: function() {
                    return $(this).attr('title');
                }
            });
        });
    }

    add_note_to_map(note_params, es_bld_id) {
        let note_text = '';
        if (note_params['title']) note_text += '<h3>'+note_params['title']+'</h3>';
        if (note_params['text']) note_text += '<p>'+note_params['text']+'</p>'

        let divicon = L.divIcon({
            html: '<div class="image-div" style="font-size:0px"><img data-html="true" title="'+note_text+'" class="notes-img" src="images/Note.png"></img></div>',
            className: 'notes-div-icon',
            iconSize: null
        });
        let note = L.marker(
            [note_params['location']['lat'], note_params['location']['lng']],
            {
                icon: divicon,
                riseOnHover: true,
                draggable: true
            }
        );

        note.id = note_params['id'];
        note.title = note_params['title'];
        note.text = note_params['text'];
        note.date = note_params['date'];
        note.author = note_params['author'];

        notes.set_note_handlers(note);
        add_object_to_layer(es_bld_id, 'notes_layer', note);

        notes.diable_note_created_event_handler();
        enable_esdl_layer_created_event_handler();
    }

    delete_note(e, id) {
        let layer = e.relatedTarget;
        remove_object_from_layer(active_layer_id, 'notes_layer', layer);

        socket.emit('command', {
            cmd: 'remove_object',
            id: id
        });
    }

    set_note_handlers(note) {
        let note_id = note.id
        note.bindContextMenu({
            contextmenu: true,
            contextmenuWidth: 140,
            contextmenuItems: [{
                text: 'Delete',
                icon: 'icons/Delete.png',
                callback: function(e) { notes.delete_note(e, note_id); }
            }],
            contextmenuInheritItems: false
        });

        note.on('dragend', function(e) {
            console.log(e);
            let note = e.target;
            let position = note.getLatLng();

            socket.emit('update-coord', {id: note.id, coordinates: {lat: position.lat, lng: position.lng}})
        });

        note.on('click', function(e) {
            console.log('Note clicked');
            console.log(e);

            let note = e.target;
            notes.open_sidebar_for_note(note);
        });
    }

    open_sidebar_for_note(note) {
        let $div = $('<div>');

        $div.append($('<h1>').text('Edit note properties'));

        let $table = $('<table>').addClass('pure-table pure-table-striped');
        let $tbody = $('<tbody>');
        $table.append($tbody);

        $tbody.append($('<tr>')
            .append($('<td>').append('Title'))
            .append($('<td>').append($('<input>').attr('id', 'input_note_title').attr('value', note.title)
                .attr('size',40)))
        );
        $tbody.append($('<tr>')
            .append($('<td>').append('Text'))
            .append($('<td>').append($('<textarea>').attr('id', 'textarea_note_text').text(note.text)
                .attr('rows',10).attr('cols',40)))
        );
        $tbody.append($('<tr>')
            .append($('<td>').append('Author'))
            .append($('<td>').append($('<input>').attr('id', 'input_note_author').attr('value', note.author)
                .attr('size',40).prop('disabled',true)))
        );
        $tbody.append($('<tr>')
            .append($('<td>').append('Date'))
            .append($('<td>').append($('<input>').attr('id', 'input_note_date').attr('value', note.date)
                .attr('size',40).prop('disabled',true)))
        );

        $div.append($table);

        let $save_button = $('<button>').text('Save').click(function() {notes.click_save(note);})
        let $discard_button = $('<button>').text('Discard').click(function() {notes.click_discard();})

        let $button_p = $('<p>').append($save_button).append($discard_button);
        $div.append($button_p);

        sidebar.setContent($div.get(0));
        sidebar.show();
    }

    click_save(note) {
        let title = $('#input_note_title').val();
        let text = $('#textarea_note_text').val();

        // Update note on map
        note.title = title;
        note.text = text;
        let note_text = '<h3>'+title+'</h3>' + '<p>'+text+'</p>';
        note._icon.innerHTML = '<div class="image-div" style="font-size:0px"><img data-html="true" title="' +
            note_text + '" class="notes-img" src="images/Note.png"></img></div>';

        // To render the HTML text properly in the tooltip window
        // TODO: Find better way? This updates EVERY note
        $('.notes-img').tooltip({
            content: function() {
                return $(this).attr('title');
            }
        });

        // Send info to backend
        socket.emit('command', {
            cmd: 'set_asset_param',
            id: note.id,
            param_name: 'title',
            param_value: title
        });
        socket.emit('command', {
            cmd: 'set_asset_param',
            id: note.id,
            param_name: 'text',
            param_value: text
        });
        socket.emit('command', {
            cmd: 'set_asset_param',
            id: note.id,
            param_name: 'date',
            param_value: new Date().today() + " " + new Date().timeNow()
        });

        sidebar.hide();
    }

    click_discard() {
        sidebar.hide();
    }

    add_note() {
        diable_esdl_layer_created_event_handler();
        notes.enable_note_created_event_handler();

        console.log(L.Icon.Default.prototype.options);

//        L.Icon.Default.imagePath = '';
//        L.Icon.Default.prototype.options.iconUrl = 'http://localhost:8111/images/Note.png';
//        L.Icon.Default.prototype.options.iconUrl = 'http://localhost:8111/images/Note.png';

        add_note_draw_handler.enable();
    }

    note_created_event_handler(e) {
        console.log(e);
        let note = e.layer;
        let id = uuidv4();
        let author = user_info['email'];
        let date = new Date().today() + " " + new Date().timeNow();

        let coords = {'lng': e.layer.getLatLng().lng, 'lat': e.layer.getLatLng().lat};
        let note_params = {id: id, location: coords, title: '', text: '', author: author, date: date};

        socket.emit('command', {cmd: 'add_note', id: id, location: coords, author: author, date: date});

        notes.add_note_to_map(note_params, active_layer_id);
    }

    enable_note_created_event_handler() {
        map.on('draw:created', notes.note_created_event_handler);
    }

    diable_note_created_event_handler() {
        map.off('draw:created', notes.note_created_event_handler);
    }

    static create(event) {
        if (event.type === 'client_connected') {
            notes = new Notes();
        }
        if (event.type === 'add_contextmenu') {

        }
    }
}

var notes; // global notes variable
var add_note_draw_handler;

$(document).ready(function() {
    extensions.push(function(event) { Notes.create(event) });

    add_note_draw_handler = new L.Draw.Marker(map);
    let my_options = add_note_draw_handler.options;
    my_options['icon'] = new L.Icon({
        iconUrl: 'images/Note.png',

        iconSize: [20, 20],
        shadowSize: [0, 0],
        iconAnchor: [0, 0],
        shadowAnchor: [0, 0],
        popupAnchor: [0, 0]
    });
});



// ----------------------------------------------------------------------------------------------------------------
//  Leaflet Control for a button to add a note to the map
// ----------------------------------------------------------------------------------------------------------------
var AddNote = L.Toolbar2.Action.extend({
    options: {
        toolbarIcon: {html: '<div class="ui-icon ui-icon-document-b">&nbsp;</div>', tooltip: 'Add note'}
    },
    addHooks: function () {
        notes.add_note();
    }
});

var NotesToolbarControl = L.Toolbar2.Control.extend({
//    position: 'topleft',
//    actions: [AddNote]
});

notesToolbarControl = function() {
    return new NotesToolbarControl({
        position: 'topleft',
        actions: [AddNote]
    });
}