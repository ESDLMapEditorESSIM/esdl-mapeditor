// ESDL Browser
// requires:
// dialog, map and socketio as global variables

class ESDLBrowser {
    constructor() {
        this.initSocketIO();
        this.history = [];
    }

    open_browser(esdl_object_id) {
        socket.emit('esdl_browse_get_objectinfo', {'id': esdl_object_id});
    }

    // browse based on a fragment instead of an id
    open_browser_fragment(esdl_object_fragment) {
        socket.emit('esdl_browse_get_objectinfo_fragment', {'fragment': esdl_object_fragment});
    }

    open_browser_identifier(esdl_object_identifier) {
        if (esdl_object_identifier.id != null) {
            socket.emit('esdl_browse_get_objectinfo', {'id': esdl_object_identifier.id});
        } else {
            socket.emit('esdl_browse_get_objectinfo_fragment', {'fragment': esdl_object_identifier.fragment});
        }
    }

    open_browser_with_event(e, id) {
        this.open_browser(id);
    }

    static generateXRefSelection(data) {
        //returnmsg = {'parent': message['parent'],
        //             'ref': {'name': reference_name, 'type': reference.eType.name},
        //             'xreferences': reference_list}
        let parent_object_identifier = data['parent']
        let $div = $('<div>');
        let $h1 = $('<h1>').text(`Select a cross-reference for ${data.ref.name} relation`);
        let $h4 = $('<h4>').html(`The following options of type ${data.ref.type} are available for the <i>${data.ref.name}</i> cross-reference. Please select one from the list.`);
        let $select = $("<select>").attr('id', 'ref_select');

        for (let i = 0; i < data.xreferences.length; i++) {
            let $option = $('<option>').attr('value', i).text(data.xreferences[i].repr);
            $select.append($option);
        }

        let $div2 = $('<div>')
                .append($("<span>").text(`Select cross-reference for ${data.ref.name}: `))
                .append($("<span>").text(' '))
                .append($select);
        let $back_button = $('<button>').addClass('btn').append($('<i>').addClass('fa fa-arrow-left')).append($('<span>').text(' Back'));
        let $button = $('<button>').addClass('btn').append($('<span>').text('Next ')).append($('<i>').addClass('fa fa-arrow-right'));
        let $div3 = $('<div>').append($back_button).append($('<span>').css('width', '300px').css('float', 'left').html('&nbsp;')).append($button);
        $button.click(function (e) {
                let selected_ref = [$('#ref_select').val()];
                socket.emit('esdl_browse_set_reference', {'parent': parent_object_identifier, 'name': data.ref.name, 'xref': data.xreferences[selected_ref]});
            });
        $back_button.click(function (e) {
                esdl_browser.open_browser_identifier(parent_object_identifier);
            });


        $div.append($h1);
        $div.append($h4);
        $div.append($div2);
        $div.append($('<div>').css('height', '40px'))
        $div.append($div3);

        return $div;
    }

    static generateTable(data) {
        let $div = $('<div>');
        let object_name = data.object.name;
        if (object_name == null || object_name === '') {
            object_name = 'Unnamed';
        }

        let $back_button = $('<button>').addClass('btn').append($('<i>').addClass('fa fa-arrow-left')).append($('<span>').text(' Back'));
        if (esdl_browser.history.length == 0) {
            $back_button.attr("disabled", true);
        }
        $back_button.click(function (e) {
            esdl_browser.open_browser_identifier(esdl_browser.history.pop());
        });
        $div.append($back_button);

        let $h2 = $('<h2>').text(`${data.object.type} - ${object_name}`).attr('title',data.object.doc);
        $div.append($h2);
        if (data.container != null) {
            let intro = 'Part of container ';
            let linktext = data.container.type;
            if (data.container.name != null) {
                intro += data.container.type + " ";
                linktext = data.container.name;
            }
            let $parent = $('<h4>').append('<span>').text(intro)
                .css('font-style', 'italic')
                .append($('<a>').text(linktext).attr('href','#').click(
                    function(e) {
                        esdl_browser.history.push(ESDLBrowser.identifier(data.object));
                        if (data.container.id == null) {
                            console.log('navigating to fragment '+data.container.fragment);
                            esdl_browser.open_browser_fragment(data.container.fragment);
                        } else {
                            console.log('navigating to '+data.container.id);
                            esdl_browser.open_browser(data.container.id);
                        }
                        return false;
                    })
                );
            $div.append($parent);
        }

        //path
        let $pathSpan = $('<span>')
        let $pathDiv = $('<div>').append($('<span>').text('Location: ')).append($pathSpan);
        var currentContainer = data.container;
        while(currentContainer != null) {
            let containerName = currentContainer.name;
            if (containerName == null || containerName==='') containerName = currentContainer.type;
            let $cA = $('<a>').text(containerName)
                .attr('href','#')
                .attr('title', currentContainer.type)
                .css('text-decoration', 'none')
                .click(
                    function(container) {
                        return function() {
                            $(".ui-tooltip-content").parents('div').remove(); // remove tooltip as it is shown when clicking
                            esdl_browser.history.push(ESDLBrowser.identifier(data.object));
                            if (container.id == null) {
                                console.log('navigating to fragment '+container.fragment);
                                esdl_browser.open_browser_fragment(container.fragment);
                            } else {
                                console.log('navigating to '+container.id);
                                esdl_browser.open_browser(container.id);
                            }
                            return false;
                        }
                    }(currentContainer));
            $pathSpan.prepend($cA);
            $pathSpan.prepend($('<span>').text('/').css('font-face', 'bold'));
            currentContainer = currentContainer.container;
        }
        $div.append($pathDiv);

        let $table = $('<table>').addClass('pure-table pure-table-striped');
        $div.append($table);
        let $thead = $('<thead>').append($('<tr>').append(  $('<th>').text('Name')   ).append(  $('<th>').text('Value') ).append(  $('<th>').text('Action') )  );
        let $tbody = $('<tbody>')
        $table.append($thead)
        $table.append($tbody)


        for (let i=0; i<data.attributes.length; i++) {
            let $tr = $("<tr>");
            let name = data.attributes[i].name;
            let value = data.attributes[i].value;
            let doc = data.attributes[i].doc;
            var $repr;
            if (data.attributes[i].type === "EEnum" || data.attributes[i].type === "EBoolean" ) {
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
                    if (data.attributes[i].options[j] == value) $option = $option.attr('selected', 'selected')
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
            let $td_key = $("<td>").text(camelCaseToWords(name)).attr('title',doc);
            if (data.attributes[i].required == true) {
                console.log(data.attributes[i].name + " is required");
                $td_key = $td_key.css("text-decoration", "underline dotted red");
            }
            let $td_value = $("<td>").append($repr);
            $tr.append($td_key)
            $tr.append($td_value)
            $tr.append($("<td>"))
            $tbody.append($tr)
        }

        for (let i=0; i<data.references.length; i++) {
            let $tr = $("<tr>");
            let name = data.references[i].name;
            let value = data.references[i].value;
            let doc = data.references[i].doc;
            let $addButton = null;
            var $repr = $('<div>');
            var $actions = $('<div>');
            if (data.references[i].many) {
                for (let j = 0; j< data.references[i].value.length; j++) {
                    let $sub = $('<div>');
                    let v = data.references[i].value[j];
                    let $a = $('<a>').text(v.repr).attr('href', "#");
                    $a.click( function(e) { esdl_browser.history.push(ESDLBrowser.identifier(data.object)); esdl_browser.open_browser_identifier(ESDLBrowser.identifier(v)); return false; });
                    let $span = $('<span>').text(' (' + v.type + ')');


                    $sub.append($a);
                    $sub.append($span);

                    if (!data.references[i].eopposite) {
                        let $spanSpacer = $('<span>').html('&nbsp;');
                        let $delSpan = $('<span>').css('text-align', 'right').css('float', 'right');
                        let $delButton = $('<button>').addClass('browse-btn-small').append($('<i>').addClass('fa fa-trash').addClass('small-icon').css('color', 'dark-grey'));
                        $delSpan.append($delButton);
                        $sub.append($spanSpacer);
                        $sub.append($delSpan);
                        $delButton.click( function(e) { esdl_browser.del(v.repr, name, ESDLBrowser.identifier(v), ESDLBrowser.identifier(data.object), true); });
                    }
                    $repr.append($sub);
                    // actions

                }
                if (data.references[i].containment == true) {
                    let $addButton = $('<button>').addClass('btn').append($('<i>').addClass('fa fa-plus-circle')
                        .css('color', 'green'))
                        .click( function(e) {
                            esdl_browser.add(data.object, data.references[i], data.references[i].types);
                        });
                    $actions.append($('<div>').append($addButton));
                } else {
                    if (!data.references[i].eopposite) {
                        let $browseButton = $('<button>').addClass('btn').append($('<i>').addClass('fa fa-ellipsis-h').css('color', 'blue')).click( function(e) { esdl_browser.select_ref(data.object, data.references[i], data.references[i].types); })
                        $actions.append($('<div>').append($browseButton));
                    }
                }

            } else {
                if (value.repr == null) {
                    value.repr = '';
                    if (data.references[i].containment == true) {
                        let $addButton = $('<button>').addClass('btn').append($('<i>').addClass('fa fa-plus-circle').css('color', 'green')).click( function(e) { esdl_browser.add(data.object, data.references[i], data.references[i].types); });
                        $actions.append($addButton);
                    } else {
                        if (!data.references[i].eopposite) {
                            let $browseButton = $('<button>').addClass('btn').append($('<i>').addClass('fa fa-ellipsis-h').css('color', 'blue')).click( function(e) { esdl_browser.select_ref(data.object, data.references[i], data.references[i].types); })
                            $actions.append($('<div>').append($browseButton));
                        }
                    }
                } else {
                    if (value.hasOwnProperty('id') && value.id != null) {
                        let $a = $('<a>').text(value.repr).attr('href', "#");
                        //.attr('href', 'javascript:esdl_browser.open_browser(\''+value.id+'\')')
                        $a.click( function(e) { esdl_browser.history.push(ESDLBrowser.identifier(data.object)); esdl_browser.open_browser(value.id); return false; });
                        $repr.append($a);
                        //let $span = $('<span>').text(' (' + value.type + ')');
                        //$repr.append($span)
                    } else {
                        // try browsing using a URI fragment //instance.0/area/asset.0/
                        if (data.references[i].fragment !== undefined) {
                            let $a = $('<a>').text(value.repr).attr('href', "#");
                            //.attr('href', 'javascript:esdl_browser.open_browser(\''+value.id+'\')')
                            $a.click( function(e) { esdl_browser.history.push(ESDLBrowser.identifier(data.object)); esdl_browser.open_browser_fragment(data.references[i].fragment); return false; });
                            $repr.append($a);
                        } else {
                            $repr.text(value.repr);
                        }
                    }

                    if (!data.references[i].eopposite) {
                        let $spanSpacer = $('<span>').html('&nbsp;');
                        let $delSpan = $('<span>').css('text-align', 'right').css('float', 'right');
                        let $delButton = $('<button>').addClass('browse-btn-small').append($('<i>').addClass('fa fa-trash').addClass('small-icon').css('color', 'dark-grey'));
                        $delSpan.append($delButton);
                        $delButton.click( function(e) { esdl_browser.del(value.repr, name, ESDLBrowser.identifier(value), ESDLBrowser.identifier(data.object), true); });
                        $repr.append($spanSpacer);
                        $repr.append($delSpan);
                    }

                }
            }
            let $td_key = $("<td>").text(camelCaseToWords(name)).attr('title',doc);;
            let $td_value = $("<td>").append($repr);

            $tr.append($td_key)
            $tr.append($td_value)
            $tr.append($("<td>").append($actions))
            $tbody.append($tr)
        }

        return $div;

    }

    static identifier(esdl_object) {
        return {'id': esdl_object.id, 'fragment': esdl_object.fragment};
    }

    add(parent_object_identifier, reference_data, types) {
        console.log(parent_object_identifier, reference_data);
        let last = esdl_browser.history[history.length - 1];
        // only add if it is not in the history already
        if (JSON.stringify(last) !== JSON.stringify(parent_object_identifier)) {
            esdl_browser.history.push(parent_object_identifier);
        }
        //let types = reference_data.types;
        if (types.length == 1) {
             socket.emit('esdl_browse_create_object', {'parent': parent_object_identifier, 'name': reference_data.name, 'type': types[0]});
        } else if (types.length > 1) {
            // select type
            this.select_asset_type(parent_object_identifier, reference_data);
        }
    }



    // delete a reference (recursively!)
    del(ref_repr, ref_name, ref_identifier, parent_identifier, show_dialog) {
        if (show_dialog == false) {
            socket.emit('esdl_browse_delete_ref', {'name': ref_name, 'ref_id': ref_identifier, 'parent': parent_identifier});
        } else {
            let $div = $('<div>');
            let $h1 = $('<h1>').text(`Delete ${ref_repr}`);
            let $h4 = $('<h4>').text(`Are you sure to delete ${ref_repr} and all content contained in it?`);

            let $ok_button = $('<button>').addClass('btn').append($('<span>').text('Ok ')).append($('<i>').addClass('fa fa-check'));
            let $back_button = $('<button>').addClass('btn').append($('<i>').addClass('fa fa-arrow-left')).append($('<span>').text(' Back'));
            let $div3 = $('<div>').append($back_button).append($('<span>').css('width', '300px').css('float', 'left').html('&nbsp;')).append($ok_button);
            $ok_button.click(function (e) {
                esdl_browser.del(ref_repr, ref_name, ref_identifier, parent_identifier, false);
            });
            $back_button.click(function (e) {
                console.log(parent_identifier);
                esdl_browser.open_browser_identifier(parent_identifier);
            });

            $div.append($h1);
            $div.append($h4);
            $div.append($div3)


            if (dialog === undefined) {
                console.log("ERROR: dialog not defined")
                // create dialog
                return;
            }
            dialog.setContent($div.get(0));
            dialog.setSize([800,500]);
            let width = map.getSize();
            dialog.setLocation([10, (width.x/2)-(800/2)]);
            $('.leaflet-control-dialog-contents').scrollTop(0);
            dialog.open();
        }
    }

    select_asset_type(parent_object_identifier, reference_data) {
        let $div = $('<div>');
        let $h1 = $('<h1>').text(`Select type for ${reference_data.name}`).attr('title',reference_data.doc);
        let $h4 = $('<h4>').html(`The <i>${reference_data.name}</i> reference supports different types of content. Please select one from the list.`);
        let $select = $("<select>").attr('id', 'type_select');

        for (let i = 0; i < reference_data.types.length; i++) {
            let $option = $('<option>').attr('value', reference_data.types[i]).text(reference_data.types[i]);
            $select.append($option);
        }

        let $div2 = $('<div>')
                .append($("<span>").text('Select type: '))
                .append($("<span>").text(' '))
                .append($select);
        let $back_button = $('<button>').addClass('btn').append($('<i>').addClass('fa fa-arrow-left')).append($('<span>').text(' Back'));
        let $button = $('<button>').addClass('btn').append($('<span>').text('Next ')).append($('<i>').addClass('fa fa-arrow-right'));
        let $div3 = $('<div>').append($back_button).append($('<span>').css('width', '300px').css('float', 'left').html('&nbsp;')).append($button);
        $button.click(function (e) {
                let selected_type = [$('#type_select').val()];
                esdl_browser.add(parent_object_identifier, reference_data, selected_type);
            });
        $back_button.click(function (e) {
                esdl_browser.open_browser_identifier(parent_object_identifier);
            });


        $div.append($h1);
        $div.append($h4);
        $div.append($div2);
        $div.append($('<div>').css('height', '40px'))
        $div.append($div3);

        if (dialog === undefined) {
            console.log("ERROR: dialog not defined")
            // create dialog
            return;
        }
        dialog.setContent($div.get(0));
        dialog.setSize([800,500]);
        let width = map.getSize()
        dialog.setLocation([10, (width.x/2)-(800/2)]);
        $('.leaflet-control-dialog-contents').scrollTop(0);
        dialog.open();
    }

    select_ref(object, reference, types) {
        // 1 ask backend for possible references ( in types all possible subtypes are listed)
        // 2 show a select-box list
        // 3 add reference value to reference
        // 4 back to view of current id/fragment

        // (data.object, data.references[i], data.references[i].types)

        socket.emit('esdl_browse_list_references', {'parent': ESDLBrowser.identifier(object), 'name': reference.name});

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
            $('.leaflet-control-dialog-contents').scrollTop(0);
            dialog.open();

        });

        //esdl_browse_select_cross_reference
        socket.on('esdl_browse_select_cross_reference', function(data) {
            console.log(data);

            let jqueryNode = ESDLBrowser.generateXRefSelection(data);

            if (dialog === undefined) {
                console.log("ERROR: dialog not defined")
                // create dialog
                return;
            }
            dialog.setContent(jqueryNode.get(0));
            dialog.setSize([800,500]);
            let width = map.getSize()
            dialog.setLocation([10, (width.x/2)-(800/2)]);
            $('.leaflet-control-dialog-contents').scrollTop(0);
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