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

// ESDL Drive: a file storage for ESDL files
// requires:
// dialog, map and socketio as global variables

class ESDLDrive {

     constructor() {
        this.initSocketIO();
        this.uploadForm = this.create_drag_drop();
        this.files = {};
        this.blob = {};
        this.chunkSize = 100*1024; // 100kb chunks
        this.driveName = "ESDL Drive";
        this.noCache = false; // default use cache
     }

     getTreeBrowser() {
        let $div = $('<div>').attr('id', 'treebrowsercontainer');
        let $jstree = $('<div>').attr('id', 'treebrowser');
        let $splitter = $('<div>').attr('id', 'splitter');
        let $data = $('<div>').attr('id', 'data');
        let $content_esdl = $('<div>').addClass('content esdl').css('display','none');
        let $content_folder = $('<div>').addClass('content folder').css('display','none');
        let $content_history = $('<div>').addClass('content history').css('display','none');
        let $content_default = $('<div>').addClass('content default').css('text-align','center').text('Select a file from the tree.');
        let $content_loader = $('<div>').addClass('content loader').css('text-align','center').text('Loading...');

        $data.append($content_folder);
        $data.append($content_esdl);
        $data.append($content_history);
        $data.append($content_default);
        $data.append($content_loader);
        $div.append($jstree);
        $div.append($splitter);
        $div.append($data);

        var jDoc = $div;
        $splitter.mousedown(function (e) {
            e.preventDefault();
            jDoc.mousemove(function (e) {
                e.preventDefault();
                var x = e.pageX - $jstree.offset().left;
                var windowWidth = $(window).width();
                var min = windowWidth/10;
                if (x > min && x < windowWidth && e.pageX < (windowWidth - min)) {
                    $jstree.width(x);
                    //jQuery("div#doc-content .markdown-body").each(function() {
                    //	var delta = jQuery("#docAppPanel")[0].getBoundingClientRect().right - this.getBoundingClientRect().right - 30;
                    //	var jThis = jQuery(this);
                    //	jThis.css("max-width", jThis.width()+delta+"px");
                    //});
                }
            });
        });
        jDoc.mouseup(function (e) {
            jDoc.unbind('mousemove');
        });

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
                            window.socket.emit('cdo_browse', {'operation': 'get_node', 'id': node.id, 'depth': 3}, function(data) {
                                console.log(data)
                                if (data.error !== undefined) {
                                    alert(data.error)
                                } else {
                                    callback.call(this, data.json);
                                }
                            });
                    },
                    'check_callback' : function(operation, node, parent, i, m) {
                        // m.pos => i=append, a=addAfter, b=addBefore
                        if(m && m.dnd && m.pos !== 'i') { return false; }
                        if(operation === "move_node" || operation === "copy_node") {
                            if(this.get_node(node).parent === this.get_node(parent).id) { return false; }
                        }
                        if (parent.original === undefined ||
                            !parent.original.writable ||
                            !(parent.original.type === 'folder')) {
                            return false;
                        }
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
                        tmp.rename.icon = "fa fa-edit";
                        tmp.remove.icon = "fa fa-trash-o";
                        tmp.ccp.submenu.cut.icon = "fa fa-cut";
                        tmp.ccp.submenu.copy.icon = "fa fa-copy";
                        tmp.ccp.submenu.paste.icon = "fa fa-paste";
                        delete tmp.create.action;
                        tmp.create.label = "New";
                        tmp.create.icon = "fa fa+plus";
                        tmp.create.submenu = {
                            "create_folder" : {
                                "separator_after"	: true,
                                "label"				: "Folder",
                                "icon"              : "fa fa-folder",
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
                        if (this.get_type(node) === 'folder') {
                            tmp.refresh = {
                                "label": "Refresh",
                                "icon": "fa fa-refresh",
                                "separator_before": true,
                                "action": function (data) {
                                    var inst = $.jstree.reference(data.reference),
                                        obj = inst.get_node(data.reference);
                                    //console.log(obj);
                                    // refresh parent, as that will refresh the children
                                    $('#treebrowser').jstree(true).refresh_node(obj.parent);
                                }
                            };
                        }
                        if(this.get_type(node) !== "folder" || !node.original.writable) {
                            // don't add New menu if it is a file that is selected
                            delete tmp.create;
                        }
                        if (this.get_type(node) === 'folder' && !node.original.writable) {
                            tmp.ccp._disabled = true;
						}
						if (this.get_type(node) !== 'folder' && !node.original.writable) {
                            tmp.rename._disabled = true;
                            tmp.remove._disabled = true;
                            tmp.ccp.submenu.cut._disabled = true;
						}
                        if (this.get_type(node) === 'folder' && !node.original.deletable) {
                            // don't show rename and remove on folders that are not deletable
                            tmp.rename._disabled = true;
                            tmp.remove._disabled = true;
                            tmp.ccp.submenu.cut._disabled = true;
                            tmp.ccp.submenu.copy._disabled = true;
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
                        data.instance.set_id(data.node, response.json.id);
                        for(let key in response.json) {
                            // update node to match properties from backend, e.g. writable
						    data.node.original[key] = response.json[key];
						}
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

     // renders the details view as a table
     render_table(d) {
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
                if (attr==='lastChanged') {
                    value = new Date(d[attr]).toLocaleString();
                }
                let $td = $('<td>');
                if (attr === 'revisionVersion' || attr === 'lastCommit') {
                    let $revLink = $('<a>', {text: camelCaseToWords(attr), title: 'Show history of this EnergySystem', href: '#'});
                    $revLink.click(function(e) {
                        socket.emit('cdo_browse', {'operation': 'get_revisions', 'id': d['path'] }, function(response) {
                            console.log('Response:', response);
                            if (response.status < 400 ) {
                                self.showHistory(response.json);
                            } else {
                                if (response.error !== undefined) {
                                    alert(response.error);
                                } else {
                                    console.log("Something went wrong getting history");
                                }
                            }
                        });
                    });
                    $td.append($revLink);
                } else {
                    $td.html(camelCaseToWords(attr));
                }
                let $tr = $('<tr>');
                $tr.append($td);
                $tr.append($('<td>').html(String(value)));
                $t.append($tr);
            }
            return $t;
     }

     tree_changed_load(data) {
        $('#data .content').hide();
        $('#data .loader').show();
        let self = this;
        // get content from CDO and show in browser, for load dialog
        socket.emit('cdo_browse', {'operation': 'get_content', 'id':  data.selected.join(':')}, function(response) {
            console.log('cdo_browse response', response);
            if (response.status !== undefined && response.status >= 400) {
                alert(response.error);
                return;
            }
			var d = response.json;
			$('#data .content').hide();
			$('#data .history').hide();
			if(d && typeof d.type !== 'undefined') {
                console.log('Get Content', d);
                switch(d.type) {
                    case 'esdl':
                        let $p = $('<h4>').html('Energy System: <i>' + d.fileName + '</i>');
                        let $t = self.render_table(d);
                        $('#data .esdl').empty();
                        $('#data .esdl').append($p);
                        $('#data .esdl').append($t);
                        if (d['path'] !== undefined) {
                            let $openbtn = $('<input type="button" value="Open" id="openbutton" title="Open this file and remove the currently opened files in the MapEditor">');
                            $openbtn.click(function () {
                                    // use cache?
                                    socket.emit('cdo_open', {'path':  d.path, 'nocache': self.noCache, 'import': false});
                                    show_loader();
                                    dialog.close();
                                });

                            let $importbtn = $('<input type="button" value="Import" id="importbutton" title="Add this energy system to the open files in the MapEditor">');
                            $importbtn.css('margin-left', '30px');
                            $importbtn.click(function () {
                                    socket.emit('cdo_open', {'path':  d.path, 'nocache': self.noCache, 'import': true});
                                    show_loader();
                                    dialog.close();
                                });

                            $('#data .esdl').append($openbtn);

                            $('#data .esdl').append($importbtn);
                        }

                        $('#data .esdl').show();
                        break;
                    case 'edd':
                        let $p_edd = $('<h4>').html('Energy Data Description: <i>' + d.fileName + '</i>');
                        let $t_edd = self.render_table(d);
                        $('#data .esdl').empty();
                        $('#data .esdl').append($p_edd);
                        $('#data .esdl').append($t_edd);
                        let $hint = $('<span>').text('Currently, Energy Data Descriptions cannot be opened in the MapEditor');
                        $('#data .esdl').append($hint);
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
        let $h4 = $('<h4>').text('Save Energy System');
        let $intro = $('<p>').text('Select a folder to store the file, add a commit message and enter a file name');
        let $p = $('<p>').html('Save folder: <i>' + path + '</i>');
         //<label class="button" for="fileElem">Select some files</label>
        let $message_div = $('<div>').addClass('blockdiv');
        let $message_label = $('<label>').addClass('button').attr({'for': 'message'}).text("Commit message:");
        let $message = $('<textarea placeholder="Added new Energy system" rows="4">').attr('id', 'message').addClass('commitmessage').css({'width':'400px'});
        $message_div.append($message_label).append($message);

        let $filename_div = $('<div>').addClass('blockdiv');
        let $filename_label = $('<label>').addClass('button').attr({'for': 'filename'}).text("Specify file name:");
        let $filename = $('<input placeholder="My Energy System.esdl" type="text">').attr('id', 'filename').css({'width':'400px'});
        $filename_div.append($filename_label).append($filename);
        $filename.val(filename);

        let $overwritecheckbox_div = $('<div>').addClass('blockdiv');
        let $overwritecheckbox_label = $('<label for="forceOverwrite">').text("Overwrite contents:");
        let $overwritecheckbox = $('<input type="checkbox" id="forceOverwrite" title="Forcibly overwrite the current file, without identifying the differences.">');
        $overwritecheckbox_div.append($overwritecheckbox_label).append($overwritecheckbox);


        let $save = $('<input type="button" class="btn btn-outline-primary blockdiv" value="Save">');
        $save.click(function (e) {
            filename = $('#filename').val();
            if (!filename) { // empty string
                filename = "My Energy System.esdl";
            }
            if (!filename.endsWith('.esdl')) { // add .esdl extension
                filename = filename + ".esdl";
            }
            let commitMessage = $('#message').val();
            let forceOverwrite = $('#forceOverwrite').prop('checked');
            console.log(path + "/" + filename, commitMessage, forceOverwrite);
            socket.emit('cdo_save', {'path':  path + "/" + filename, 'commitMessage': commitMessage, 'forceOverwrite': forceOverwrite}, function(response) {
                if (!response.success) {
                    alert("Saving failed: " + response.error);
                }
            });
            //show_loader();
            dialog.close();
        });
        $div.append($h4);
        $div.append($intro);
        $div.append($p);
        $div.append($message_div);
        $div.append($filename_div);
        $div.append($overwritecheckbox_div);
        $div.append($save);
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
        let $input = $('<input type="file" multiple>').attr('id', 'fileElem');
        let $label = $('<label for="fileElem">').addClass('button').text('Select file(s)');
        let $progress = $('<progress>').attr('id', 'progress-bar').attr('max', 100).attr('value', 0).css('vertical-align','middle');
        let $progress_text = $('<span style="margin-left: 1em; margin-top: -4px">').attr('id', 'progress-text').text('');
        $droparea.append($form);
        $input.change(function(e) {
            handleFiles(this.files);
        });
        $form.append($p1);
        $form.append($p2);
        $form.append($input);
        $form.append($label);
        $droparea.append($progress);
        $droparea.append($progress_text);


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
        }

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
          let text = 'Loading ' + self.files[uuid].name;
          $progress_text.html(text);
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
          let text = ""
          if (self.files[fileUuid] === null) {
            text = 'Done';
          } else {
            text = 'Uploading ' + self.files[fileUuid].name + ' ' + percent.toFixed(1) + '%';
          }
          $progress_text.html(text)
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
        dialog.setTitle('Load file from ' + this.driveName);
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
        dialog.setTitle('Save file to ' + this.driveName);
        $('.leaflet-control-dialog-contents').scrollTop(0);
        dialog.open();
     }

     showHistory(history) {
        //content history
        let $history = $('#data .history');
        $history.empty();
        let $div = $('<div>').css({'display':'inline'});
        let $p = $('<h4>').text('History of ' + history.name).css({'margin-top': '0px'});
        let $back_button = $('<button>').css({'float': 'left', 'margin-right': '10px', 'margin-top': '2px'})
            .addClass('btn-outline-primary dialogbutton btn').append($('<i>').addClass('fa fa-arrow-left')).append($('<span>').text(' Back'));
        $div.append($back_button)
        $div.append($p)
        $back_button.click(function() {
            $history.hide();
            $('#data .esdl').show();
        });
        $history.append($div);
        let $t = $('<table>').addClass('pure-table pure-table-striped').css({'width': '100%'}); //, 'table-layout': 'auto', 'border-collapse': 'collapse'});
        let $thead = $('<thead>').append(
            $('<tr>').append(
                $('<th>').text("Time").css({'min-width': '140px'}),
                $('<th>').text('Message').css({'width': '100%'}),
                $('<th>').text('User'),
                $('<th>').text('Branch'),
                $('<th>').text('Action')
            )
        );
        $t.append($thead);
        let commits = history.commits;
        for (let i in commits) {
            let commit = commits[i];
            //console.log(commits[i]);
            let $tr = $('<tr>');
            $tr.append($('<td>').html(new Date(commit.time).toLocaleString()).css({'text-align': 'right'}));
            $tr.append($('<td>').html(commit.message));
            $tr.append($('<td>').html(commit.user));
            $tr.append($('<td>').html(commit.branch));
            let $a = $('<a>', {href: '#', text: 'Open', title: 'Open this version in the MapEditor'});
            $a.click(function(e) {
                console.log(e);
                socket.emit('cdo_open', {'path':  history.path, 'revision': commit.time});
                show_loader();
                dialog.close();
            });
            $tr.append($('<td>').append($a));
            $t.append($tr);
            $history.append($t);
        }
        $('#data .esdl').hide();
        $history.show();

     }


     initSocketIO() {
        console.log("Registering socket io bindings for ESDL Drive CDO repo")
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
            if (esdlDrive === undefined) {
                esdlDrive = new ESDLDrive();
            }
            return esdlDrive;
        }
    }

}

var esdlDrive; // global esdlDrive variable
$(document).ready(function() {
    extensions.push(function(event) { ESDLDrive.create(event) });
});