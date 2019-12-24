// ESDL Browser
// requires:
// dialog, map and socketio as global variables

class ESDLBrowser {
    constructor() {
        this.initSocketIO();
    }

    open_browser(esdl_object_id) {
        socket.emit('esdl_browse_get_objectinfo', {'id': esdl_object_id});
    }

    open_browser_with_event(e, id) {
        this.open_browser(id);
    }

    static generateTable(data) {
        let $div = $('<div>');
        let $h1 = $('<h1>').text(`${data.object.type} - ${data.object.name}`).attr('title',data.object.doc);
        $div.append($h1);
        if (data.container != null) {
            let $parent = $('<h3>').append('<span>').text(`Part of container ${data.container.type} `).addClass('italic')
                .append($('<a>').text(data.container.name).attr('href','#').click(
                    function(e) {
                        e.preventDefault(); console.log('navigating to '+data.container.id);
                        esdl_browser.open_browser(data.container.id);
                        return false;
                    })
                );
            $div.append($parent);
        }
        let $table = $('<table>').addClass('pure-table pure-table-striped');
        $div.append($table);
        let $thead = $('<thead>').append($('<tr>').append(  $('<th>').text('Name')   ).append(  $('<th>').text('Value') ));
        let $tbody = $('<tbody>')
        $table.append($thead)
        $table.append($tbody)


        for (let i=0; i<data.attributes.length; i++) {
            let $tr = $("<tr>");
            let name = data.attributes[i].name;
            let value = data.attributes[i].value;
            let doc = data.attributes[i].doc;
            var $repr;
            if (data.attributes[i].type === "EEnum" || data.attributes[i].type=="EBoolean" ) {
                //<select width="60" style="width:145px" id="'+ asset_attrs[i]['name']+idgen +'" assetid="' + asset_id + '" name="' +
                //asset_attrs[i]['name'] + '" onchange="change_param(this);">';
                $repr = $('<select>')
                    .attr("id", data.attributes[i].name + i)
                    .attr('assetid', data.object.id)
                    .attr('name', data.attributes[i].name)
                    .change(function (e) { change_param(this);});

                for (let j = 0; j< data.attributes[i].options.length; j++) {
                    let caption = data.attributes[i].options[j].charAt(0).toUpperCase() + data.attributes[i].options[j].slice(1).toLowerCase();
                    caption = caption.replace(/_/g, ' '); // replace _ with space to render nicely
                    let $option = $('<option>').attr('value', data.attributes[i].options[j]).text(caption);
                    if (options[j] == value) $option.attr('selected', 'selected')
                    $repr.append($option)
                }
            } else {
                //'<td><input type="text" width="60" id="'+ asset_attrs[i]['name']+idgen +'" assetid="' + asset_id + '" name="' +
                            //asset_attrs[i]['name'] + '" value="' + value +'" onchange="change_param(this);" ' + edate + '></td></tr>';
                $repr = $('<input>')
                    .attr('type', "text")
                    .attr("id", data.attributes[i].name + i)
                    .attr('assetid', data.object.id)
                    .attr('name', data.attributes[i].name)
                    .attr('value', data.attributes[i].value)
                    .change(function(e) { change_param(this); });
                    // edate


            }
            let $td_key = $("<td>").text(camelCaseToWords(name)).attr('title',doc);;
            let $td_value = $("<td>").append($repr);
            $tr.append($td_key)
            $tr.append($td_value)
            $tbody.append($tr)
        }

        for (let i=0; i<data.references.length; i++) {
            let $tr = $("<tr>");
            let name = data.references[i].name;
            let value = data.references[i].value;
            let doc = data.references[i].doc;
            var $repr = $('<div>');
            if (data.references[i].many) {
                for (let j = 0; j< data.references[i].value.length; j++) {
                    let $sub = $('<div>');
                    let v = data.references[i].value[j];
                    let $a = $('<a>').text(v.repr).attr('href', "#");
                    $a.click( function(e) { e.preventDefault(); console.log('navigating to '+v.id);esdl_browser.open_browser(v.id); return false; });
                    $sub.append($a)
                    $repr.append($sub);
                }
            } else {
                if (value.repr == null) value.repr = '';
                if (value.hasOwnProperty('id')) {
                    let $a = $('<a>').text(value.repr).attr('href', "#");
                    //.attr('href', 'javascript:esdl_browser.open_browser(\''+value.id+'\')')
                    $a.click( function(e) { e.preventDefault(); console.log('navigating to '+value.id);esdl_browser.open_browser(value.id); return false; });
                    $repr.append($a);
                } else {
                    $repr.text(value.repr);
                }
            }
            let $td_key = $("<td>").text(camelCaseToWords(name)).attr('title',doc);;
            let $td_value = $("<td>").append($repr);
            $tr.append($td_key)
            $tr.append($td_value)
            $tbody.append($tr)
        }

        return $div;

    }

    initSocketIO() {
        console.log("Registering socket io bindings for ESDLBrowser")

        socket.on('esdl_browse_to', function(data) {
            //console.log("ESDL_Brower: browse_to SocketIO call");
            console.log(data);

            let jqueryNode = ESDLBrowser.generateTable(data);

            if (dialog === undefined) {
                console.log("ERROR: dialog not defined")
                // create dialog
                return;
            }
            dialog.setContent(jqueryNode.get(0));
            dialog.setSize([800,500]);
            let width = map.getSize()
            dialog.setLocation([10, (width.x/2)-(800/2)]);
            dialog.open();

        });
    }

    static create(event) {
        if (event.type === 'client_connected') {
            esdl_browser = new ESDLBrowser();
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

var esdl_browser; // global esdl_browser variable
$(document).ready(function() {
    extensions.push(function(event) { ESDLBrowser.create(event) });

});