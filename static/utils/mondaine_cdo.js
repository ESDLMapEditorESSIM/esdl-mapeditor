// Mondaine CDO integration
// requires:
// dialog, map and socketio as global variables

class MondaineCDO {

     constructor() {
        this.initSocketIO();
        this.uploadForm = this.create_drag_drop();
        this.files = {};
        this.blob = {};
        this.chunkSize = 100*1024; // 100kb chunks
     }

     getTreeBrowser() {
        let $div = $('<div>').attr('id', 'treebrowsercontainer');
        let $jstree = $('<div>').attr('id', 'treebrowser');
        let $data = $('<div>').attr('id', 'data');
        let $content_esdl = $('<div>').addClass('content esdl').css('display','none');
        let $content_folder = $('<div>').addClass('content folder').css('display','none');
        let $content_default = $('<div>').addClass('content default').css('text-align','center').text('Select a file from the tree.');
        let $content_loader = $('<div>').addClass('content loader').css('text-align','center').text('Loading...');

        $data.append($content_folder);
        $data.append($content_esdl);
        $data.append($content_default);
        $data.append($content_loader);
        $div.append($jstree);
        $div.append($data);

        return $div;
     }

     initTree(saveDialog) {
        // saveDialog: true: do save dialog
        // saveDialog: false -> load dialog
        this.files = {};
        this.blob = {};
        var self = this;
        var save = saveDialog;
        $('#treebrowser')
            .jstree({
                'core' : {
                    'multiple': false,
                    'data' : function (node, callback) {
                            //console.log("Getting data ", node)
                            socket.emit('cdo_browse', {'operation': 'get_node', 'id': node.id}, function(data) {
                                //console.log(data)
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
                        //console.log(tmp);
                        //console.log(node);
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
                            }
                            /*,
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
                        tmp.refresh = {
                                "label": "Refresh",
                                "separator_before": true,
                                "action": function (data) {
                                    var inst = $.jstree.reference(data.reference),
                                        obj = inst.get_node(data.reference);
                                    //console.log(obj);
                                    $('#treebrowser').jstree(true).refresh_node(obj.id);
                                }
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
                        data.instance.refresh_node(data.node.parent);
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
        $('#data .content').hide();
        $('#data .loader').show();
        let self = this;
        // get content from CDO and show in browser, for load dialog
        socket.emit('cdo_browse', {'operation': 'get_content', 'id':  data.selected.join(':')}, function(response) {
            console.log('cdo_browse response', response);
			var d = response.json;
			$('#data .content').hide();
			if(d && typeof d.type !== 'undefined') {
                switch(d.type) {
                    case 'esdl':
                        let $t = $('<table>').addClass('pure-table pure-table-striped');
                        let $thead = $('<thead>').append(
                            $('<tr>').append(
                                $('<th>').text("Property"),
                                $('<th>').text('Value')
                            )
                        );
                        $t.append($thead);

                        for (let attr in d) {
                            let value = d[attr];
                            if (attr==='Last saved') {
                                value = new Date(d[attr]).toLocaleString();
                            }
                            let $tr = $('<tr>');
                            $tr.append($('<td>').text(attr));
                            $tr.append($('<td>').text(value));
                            $t.append($tr);
                        }
                        $('#data .esdl').empty();
                        $('#data .esdl').append($t);
                        if (d['path'] !== undefined) {
                            let $a = $('<input type="button" value="Open" id="openbutton">');
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
                    case 'folder':
                        $('#data .folder').empty();
                        if (d.writable) {
                            $('#data .folder').append(self.uploadForm);
                            self.uploadForm.attr('path', d.path);
                            let folderName = d.path.substring(d.path.lastIndexOf('/')+1);
                            self.uploadForm.find('#foldername').text("Upload to folder: " + folderName);
                            $('#progress-bar').get(0).value = 0;
                        }

                        $('#data .folder').show();
                        break;
                    default:
                        console.log(d);
                        if (d.content) {
                            $('#data .default').html(d.content).show();
                        } else {
                            $('#data .default').text("").show();
                        }
                        break;
                }
            }
		});

     }

     tree_changed_save(data) {
        //console.log(data);
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

     create_drag_drop() {
        self=this;
     /*
     <div id="drop-area">
      <form class="my-form">
        <p>Upload multiple files with the file dialog or by dragging and dropping images onto the dashed region</p>
        <input type="file" id="fileElem" multiple accept="image/*" onchange="handleFiles(this.files)">
        <label class="button" for="fileElem">Select some files</label>
      </form>
      <progress id="progress-bar" max=100 value=0></progress>
      <div id="gallery" /></div>
    </div>
     */
        let $droparea = $('<div>').attr('id', 'drop-area');
        let $form = $('<form>').addClass('upload-form');
        let $p1 = $('<p>').text('To upload ESDL files in this folder use drag & drop from your file explorer or click the button below.');
        let $p2 = $('<p id="foldername">');
        let $input = $('<input type="button" multiple>').attr('id', 'fileElem');
        let $label = $('<label for="fileElem">').addClass('button').text('Select file(s)');
        let $progress = $('<progress>').attr('id', 'progress-bar').attr('max', 100).attr('value', 0);
        $droparea.append($form);
        $form.append($p1);
        $form.append($p2);
        $form.append($input);
        $form.append($label);
        $droparea.append($progress);


        // ************************ Drag and drop ***************** //
        // Prevent default drag behaviors
        // see https://codepen.io/joezimjs/pen/yPWQbd
        let dropArea = $droparea.get(0);
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
          dropArea.addEventListener(eventName, preventDefaults, false);
          document.body.addEventListener(eventName, preventDefaults, false);
        });

        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
          dropArea.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
          dropArea.addEventListener(eventName, unhighlight, false);
        });

        // Handle dropped files
        dropArea.addEventListener('drop', handleDrop, false);

        function preventDefaults(e) {
          e.preventDefault();
          e.stopPropagation();
        };

        function highlight(e) {
          dropArea.classList.add('highlight');
        }

        function unhighlight(e) {
          dropArea.classList.remove('active');
           dropArea.classList.remove('highlight');
        }

        function handleDrop(e) {
          var dt = e.dataTransfer;
          var files = dt.files;

          handleFiles(files);
        }

        self.uploadProgress = [];
        let progressBar = $progress.get(0);

        function initializeProgress(uuid) {
          progressBar.value = 0;
          self.uploadProgress[uuid] = 0;
        }

        function updateProgress(fileUuid, percent) {
          self.uploadProgress[fileUuid] = percent;
          let progress = Object.values(self.uploadProgress)
          let total = progress.reduce((tot, curr) => tot + curr, 0) / progress.length;
          console.log(progress);
          console.log(total)
          console.debug('update', fileUuid, percent, total);
          progressBar.value = total;
        }
        self.updateProgress = updateProgress;

        function handleFiles(files) {
          files = [...files];
          files.forEach(function (file) {
            let extension = file.name.split('.').pop();
            if (extension=="esdl") {
                let uuid = uuidv4();
                self.files[uuid] = file;
                initializeProgress(uuid);
                uploadFile(file, uuid);
            } else {
                alert("Not an esdl-file: " + file.name);
            }

          });
          //self.files.forEach(uploadFile);
          //files.forEach(previewFile);
        }

        function uploadFile(file, uuid) {
          console.log("Uploading ", file);

          let reader = new FileReader();
          reader.onload = function() {
            // reading finished
            self.blob[uuid] = reader.result;
            socket.emit('cdo_upload', {'message_type': 'start', 'uuid': uuid, 'name':  file.name, 'size': file.size,
                                        'content': '', 'filetype': file.type, 'path': $droparea.attr('path') });
          };
          reader.onerror = function() {
            console.log(reader.error);
            alert("Uploading failed: \n" + reader.error);
          };
          reader.readAsArrayBuffer(file);


          /*
          var url = '/upload'
          var xhr = new XMLHttpRequest()
          var formData = new FormData()
          xhr.open('POST', url, true)
          xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')

          // Update progress (can be used to show progress indicator)
          xhr.upload.addEventListener("progress", function(e) {
            updateProgress(i, (e.loaded * 100.0 / e.total) || 100)
          })

          xhr.addEventListener('readystatechange', function(e) {
            if (xhr.readyState == 4 && xhr.status == 200) {
              updateProgress(i, 100) // <- Add this
            }
            else if (xhr.readyState == 4 && xhr.status != 200) {
              // Error. Inform the user
              console.log("Error ", xhr);
            }
          })

          //formData.append('upload_preset', 'ujpu6gyk')
          formData.append('file', file)
          //xhr.send(formData)
          updateProgress(i, 100);
          */
        }


        return $droparea;
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
            self.file_open_dialog();
        });
        socket.on('cdo_next_chunk', function(data) {
              //{'name': name, 'pos': self.files[name]['pos']}')
              let uuid = data.uuid;
              let file = self.files[uuid];
              console.log('Next chunk for', data, file);
              let blob = self.blob[uuid];
              let pos = data.pos
              let length = Math.min(self.chunkSize, file.size - pos);
              let slice = blob.slice(pos, pos+length);
              let percentage = pos / file.size * 100;
              console.log("Sending chunk start", pos, "end", length);
              socket.emit('cdo_upload', {'message_type': 'next_chunk', 'uuid': uuid, 'name':  file.name, 'size': file.size, 'content': slice, 'pos': pos});
              self.updateProgress(uuid, percentage);

        });
        socket.on('cdo_upload_done', function(data) {
              let uuid = data.uuid;
              self.files[uuid] = null;
              self.blob[uuid] = null;
              self.updateProgress(uuid, 100);
              if (data.success) {
                console.log('Refreshing tree');
                $('#treebrowser').jstree(true).refresh_node(data.path);
              } else {
                console.log(data.error);
                alert("Uploading failed: \n" + data.error);
              }

        });
    }

    static create(event) {
        if (event.type === 'client_connected') {
            if (mondaineCDO === undefined) {
                mondaineCDO = new MondaineCDO();
            }
            return mondaineCDO;
        }
    }

}

var mondaineCDO; // global mondaineCDO variable
$(document).ready(function() {
    extensions.push(function(event) { MondaineCDO.create(event) });
});