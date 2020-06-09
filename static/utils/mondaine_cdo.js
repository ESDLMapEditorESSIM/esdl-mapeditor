// Mondaine CDO integration
// requires:
// dialog, map and socketio as global variables

class MondaineCDO {

     constructor() {
        this.initSocketIO();


     }

     getTreeBrowser() {
        let $div = $('<div>').attr('id', 'treebrowsercontainer');
        let $jstree = $('<div>').attr('id', 'treebrowser');
        let $data = $('<div>').attr('id', 'data');
        let $content_esdl = $('<div>').addClass('content esdl').css('display','none');
        let $content_folder = $('<div>').addClass('content folder').css('display','none');
        let $content_default = $('<div>').addClass('content default').css('text-align','center').text('Select a file from the tree.');

        $data.append($content_folder);
        $data.append($content_esdl);
        $data.append($content_default);
        $div.append($jstree);
        $div.append($data);

        return $div;
     }

     initTree(saveDialog) {
        // saveDialog: true: do save dialog
        // saveDialog: false -> load dialog
        var self = this;
        var save = saveDialog;
        $('#treebrowser')
            .jstree({
                'core' : {
                    'multiple': false,
                    'data' : function (node, callback) {
                            console.log("Getting data ", node)
                            socket.emit('cdo_browse', {'operation': 'get_node', 'id': node.id}, function(data) {
                                console.log(data)
                                callback.call(this, data.json);
                            });
                    },
                    'check_callback' : function(operation, node, parent, i, m) {
                        // m.pos => i=append, a=addAfter, b=addBefore
                        if(m && m.dnd && m.pos !== 'i') { return false; }
                        if(operation === "move_node" || operation === "copy_node") {
                            if(this.get_node(node).parent === this.get_node(parent).id) { return false; }
                        }
                        if (parent.original === undefined || !parent.original.writable) { return false;}
                        return true;
                    },
                    'themes' : {
                        'responsive' : false,
                        'variant' : 'small',
                        'stripes' : false
                    }
                },
                'sort' : function(a, b) {
                    return this.get_type(a) === this.get_type(b) ? (this.get_text(a) > this.get_text(b) ? 1 : -1) : (this.get_type(a) >= this.get_type(b) ? 1 : -1);
                },
                'contextmenu' : {
                    'items' : function(node) {
                        var tmp = $.jstree.defaults.contextmenu.items();
                        console.log(tmp);
                        console.log(node);
                        delete tmp.create.action;
                        tmp.create.label = "New";
                        tmp.create.submenu = {
                            "create_folder" : {
                                "separator_after"	: true,
                                "label"				: "Folder",
                                "action"			: function (data) {
                                    var inst = $.jstree.reference(data.reference),
                                        obj = inst.get_node(data.reference);
                                    inst.create_node(obj, { type : "folder" }, "last", function (new_node) {
                                        setTimeout(function () { inst.edit(new_node); },0);
                                    });
                                }
                            } /*,
                            "create_file" : {
                                "label"				: "File",
                                "action"			: function (data) {
                                    var inst = $.jstree.reference(data.reference),
                                        obj = inst.get_node(data.reference);
                                    inst.create_node(obj, { type : "file" }, "last", function (new_node) {
                                        setTimeout(function () { inst.edit(new_node); },0);
                                    });
                                }
                            }*/
                        };
                        if(this.get_type(node) !== "folder" || !node.original.writable) {
                            // don't add New menu if it is a file that is selected
                            delete tmp.create;
                        }
                        return tmp;
                    }
                },
                'types' : {
                    'default' : { 'icon' : 'file' },
                    'folder' : { 'icon' : 'folder' },
                    'file' : { 'valid_children' : [], 'icon' : 'file' }
                },
                'unique' : {
                    'duplicate' : function (name, counter) {
                        return name + ' ' + counter;
                    }
                },
                'plugins' : ['state','dnd','sort','types','contextmenu','unique']
            })
            .on('delete_node.jstree', function (e, data) {
                if (confirm('Are you sure you want to delete ' + data.node.id + ' and all files and folders below it?')) {
                  socket.emit('cdo_browse', {'operation': 'delete_node', 'id': data.node.id}, function(response) {
                        if (response.status == 403) { // PermissionDenied
                            alert(response.json.error);
                        }
                        data.instance.refresh();
                    });
                }
            })
            .on('create_node.jstree', function (e, data) {
                socket.emit('cdo_browse', {'operation': 'create_node', 'type' : data.node.type, 'id' : data.node.parent, 'text' : data.node.text}, function(response) {
                    if (response.status == 403) { // PermissionDenied
                        alert(response.json.error);
                        data.instance.refresh();
                    } else {
                        data.node.original.writable = true;
                        data.instance.set_id(data.node, response.json.id);
                    }
                });
            })
            .on('rename_node.jstree', function (e, data) {
                socket.emit('cdo_browse', {'operation': 'rename_node', 'id' : data.node.id, 'text' : data.text}, function(response) {
                    if (response.status == 403) { // PermissionDenied
                        alert(response.json.error);
                        data.instance.refresh();
                    } else {
                        data.instance.set_id(data.node, response.json.id);
                    }
                });
            })
            .on('move_node.jstree', function (e, data) {
                socket.emit('cdo_browse', {'operation': 'move_node', 'id' : data.node.id, 'parent' : data.parent}, function(response) {
                    if (response.status == 403) { // PermissionDenied
                        alert(response.json.error);
                        data.instance.refresh();
                    } else {
                        data.instance.load_node(data.parent);
                    }
                });
            })
            .on('copy_node.jstree', function (e, data) {
                socket.emit('cdo_browse', {'operation': 'copy_node', 'id': data.original.id, 'parent' : data.parent}, function(response) {
                    if (response.status > 400) { // PermissionDenied
                        alert(response.json.error);
                        data.instance.refresh();
                    } else {
                        data.instance.load_node(data.parent);
                    }
                });
            })
            .on('changed.jstree', function (e, data) {
                if(data && data.selected && data.selected.length) {
                    if (save) {
                        self.tree_changed_save(data);
                    } else {
                        self.tree_changed_load(data);
                    }
                }
                else {
                    $('#data .content').hide();
                    $('#data .default').html('Select a file from the tree.').show();
                }
            });
     }

     tree_changed_load(data) {
        // get content from CDO and show in browser, for load dialog
        socket.emit('cdo_browse', {'operation': 'get_content', 'id':  data.selected.join(':')}, function(response) {
			var d = response.json;
			if(d && typeof d.type !== 'undefined') {
                $('#data .content').hide();
                switch(d.type) {
                    case 'esdl':
                        let $t = $('<table>');
                        for (let attr in d) {
                            let $tr = $('<tr>');
                            $tr.append($('<td>').text(attr));
                            $tr.append($('<td>').text(d[attr]));
                            $t.append($tr);
                        }
                        $('#data .esdl').empty();
                        $('#data .esdl').append($t);
                        if (d['path'] !== undefined) {
                            let $a = $('<input type="button" value="Open">');
                            $a.click(function () {
                                    socket.emit('cdo_open', {'path':  d.path});
                                    show_loader();
                                    dialog.close();
                                });

                            $('#data .esdl').append($a);
                        }

                        $('#data .esdl').show();
                        break;
                    case 'text':
                    case 'txt':
                    case 'md':
                    case 'htaccess':
                    case 'log':
                    case 'sql':
                    case 'php':
                    case 'js':
                    case 'json':
                    case 'css':
                    case 'html':
                        $('#data .code').show();
                        $('#code').val(d.content);
                        break;
                    case 'png':
                    case 'jpg':
                    case 'jpeg':
                    case 'bmp':
                    case 'gif':
                        $('#data .image img').one('load', function () { $(this).css({'marginTop':'-' + $(this).height()/2 + 'px','marginLeft':'-' + $(this).width()/2 + 'px'}); }).attr('src',d.content);
                        $('#data .image').show();
                        break;
                    default:
                        $('#data .default').html(d.content).show();
                        break;
                }
            }
		});

     }

     tree_changed_save(data) {
        console.log(data);
        let path = data.node.id;
        let filename = '';
        if (data.node.type != 'folder') {
            filename = path.substring(path.lastIndexOf("/")+1)
            path = path.substring(0, path.lastIndexOf("/"));
        }
        $('#data .content').hide();
        let $div = $('<div>')
        let $intro = $('<p>').text('Select a folder to store the file and enter a file name')
        let $p = $('<p>').text('Save file to: ' + path)
        let $input = $('<input placeholder="My Energysystem.esdl" type="text">').attr('id', 'filename');
        $input.val(filename);
        let $save = $('<input type="button" value="Save">');
        $save.click(function (e) {
            filename = $('#filename').val();
            console.log(path + "/" + filename)
            socket.emit('cdo_save', {'path':  path + "/" + filename });
            //show_loader();
            dialog.close();
        });
        $div.append($intro)
        $div.append($p)
        $div.append($input)
        $div.append($save)
         $('#data .esdl').empty();
         $('#data .esdl').append($div);
         $('#data .esdl').show();
     }

     file_open_dialog() {
        if (dialog === undefined) {
            console.log("ERROR: dialog not defined")
            // create dialog
            return;
        }

        let dialogHTML = this.getTreeBrowser();

        //dialog.setSize([800,500]);
        //let width = map.getSize();
        //dialog.setLocation([10, (width.x/2)-(800/2)]);
        dialog.setContent(dialogHTML.get(0));
        this.initTree(false);

        dialog.setSize([esdl_browser.width, esdl_browser.height]);
        dialog.setLocation([esdl_browser.x, esdl_browser.y]);
        dialog.setTitle('Load file from Mondaine HUB');
        $('.leaflet-control-dialog-contents').scrollTop(0);
        dialog.open();
     }


     file_save_dialog() {
        if (dialog === undefined) {
            console.log("ERROR: dialog not defined")
            // create dialog
            return;
        }

        let dialogHTML = this.getTreeBrowser();

        //dialog.setSize([800,500]);
        //let width = map.getSize();
        //dialog.setLocation([10, (width.x/2)-(800/2)]);
        dialog.setContent(dialogHTML.get(0));
        this.initTree(true); // save dialog

        dialog.setSize([esdl_browser.width, esdl_browser.height]);
        dialog.setLocation([esdl_browser.x, esdl_browser.y]);
        dialog.setTitle('Save file to Mondaine HUB');
        $('.leaflet-control-dialog-contents').scrollTop(0);
        dialog.open();
     }


     initSocketIO() {
        console.log("Registering socket io bindings for Mondaine CDO repo")
        var self = this;
        socket.on('cdo_file_open', function(data) {
            //console.log("ESDL_Brower: browse_to SocketIO call");
            console.log(data);

            self.file_open_dialog();

        });
    }

    static create(event) {
        if (event.type === 'client_connected') {
            mondaineCDO = new MondaineCDO;
            return mondaineCDO;
        }
    }

}

var mondaineCDO; // global esdl_browser variable
$(document).ready(function() {
    extensions.push(function(event) { MondaineCDO.create(event) });
});