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

// Profiles
// requires:
// map and socketio as global variables


class Profiles {
    constructor() {
        this.initSocketIO();
        this.profiles_list = null;
        this.files = {};
        this.blob = {};
        this.chunkSize = 100*1024; // 100kb chunks

        socket.emit('get_profiles_list', function(profiles_list) {
            // console.log(profiles_plugin);
            profiles_plugin.profiles_list = profiles_list;
        });
    }

    initSocketIO() {
        console.log("Registering socket io bindings for Profiles")
        var self = this;

        socket.on('update_profiles_list', function(profiles_list) {
            // console.log(profiles_list);
            profiles_plugin.profiles_list = profiles_list;
        });

        socket.on('csv_next_chunk', function(data) {
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
            socket.emit('profile_csv_upload', {'message_type': 'next_chunk', 'uuid': uuid, 'name':  file.name, 'size': file.size, 'content': slice, 'pos': pos});
            self.updateProgress(uuid, percentage);
        });
        socket.on('csv_upload_done', function(data) {
            $('#csv-message').text('CSV uploading finished, now writing data to database');
        });
        socket.on('csv_processing_done', function(data) {
            let uuid = data.uuid;
            self.files[uuid] = null;
            self.blob[uuid] = null;
            self.updateProgress(uuid, 0);

            if (!data.success) {
                console.log(data.error);
                $('#csv-message').text('');
                alert("Uploading failed: \n" + data.error);
            } else {
                $('#csv-message').text('Profiles have been stored in the database and are available for use');
            }
        });
    }

    get_profiles_settings(div) {
        socket.emit('get_profiles_list', function(profiles_list) {
            // console.log(profiles_list);
            profiles_plugin.profiles_list = profiles_list;
            div.append($('<h1>').text('Profiles plugin settings'));

            let $select = $('<select>').attr('id', 'profile_select');
            $select.append($('<option>').val('first_select_profile').text('Please select a profile'));
            let group_list = profiles_list['groups'];
            let profile_info = Object.entries(profiles_list['profiles']);
            for (let gr=0; gr<group_list.length; gr++) {
                let $optgroup = $('<optgroup>').attr('label', group_list[gr].name);
                for (let pr=0; pr<profile_info.length; pr++) {
                    if (group_list[gr].setting_type == profile_info[pr][1].setting_type) {
                        if (profile_info[pr][1].setting_type == 'project' &&
                            profile_info[pr][1].project_name != group_list[gr].project_name) continue;

                        let $option = $('<option>').val(profile_info[pr][0]).text(profile_info[pr][1].profile_uiname);
                        $optgroup.append($option);
                    }
                }
                $select.append($optgroup);
            }
            $select.change(function() {profiles_plugin.select_profile();});
            div.append($select);

            let $remove_button = $('<button>').text('Remove').click(function() {profiles_plugin.click_remove();})
            div.append($remove_button);

            div.append($('<p>'));

            let $table = $('<table>').addClass('pure-table pure-table-striped');
            let $thead = $('<thead>').append($('<tr>').append($('<th>').text('Parameter')).append($('<th>')
                    .text('Value')));
            let $tbody = $('<tbody>');
            $table.append($thead);
            $table.append($tbody);

            $tbody.append($('<tr>')
                .append($('<td>').append('Profile name'))
                .append($('<td>').append($('<input>').attr('id', 'input_prof_uiname').attr('value', '').attr('size',40)))
            );
            $tbody.append($('<tr>')
                .append($('<td>').append('Database'))
                .append($('<td>').append($('<input>').attr('id', 'input_prof_db').attr('value', '')))
            );
            $tbody.append($('<tr>')
                .append($('<td>').append('Measurement'))
                .append($('<td>').append($('<input>').attr('id', 'input_prof_meas').attr('value', '')))
            );
            $tbody.append($('<tr>')
                .append($('<td>').append('Field'))
                .append($('<td>').append($('<input>').attr('id', 'input_prof_field').attr('value', '')))
            );
            $tbody.append($('<tr>')
                .append($('<td>').append('Multiplier'))
                .append($('<td>').append($('<input>').attr('id', 'input_prof_mult').attr('value', '')))
            );
            $tbody.append($('<tr>')
                .append($('<td>').append('Profile Type'))
                .append($('<td>').append($('<input>').attr('id', 'input_prof_type').attr('value', '')))
            );
            $tbody.append($('<tr>')
                .append($('<td>').append('Start datetime'))
                .append($('<td>').append($('<input>').attr('id', 'input_prof_startdt').attr('value', '')))
            );
            $tbody.append($('<tr>')
                .append($('<td>').append('End datetime'))
                .append($('<td>').append($('<input>').attr('id', 'input_prof_enddt').attr('value', '')))
            );
            $tbody.append($('<tr>')
                .append($('<td>').append('Embed URL'))
                .append($('<td>').append($('<input>').attr('id', 'input_prof_embedurl').attr('value', '')))
            );

            let $select_group = $('<select>').attr('id', 'add_to_group_select');
            for (let gr=0; gr<group_list.length; gr++) {
                let $option = $('<option>').val(group_list[gr].project_name).text(group_list[gr].name);
                $select_group.append($option);
            }
            $tbody.append($('<tr>')
                .append($('<td>').append('Group'))
                .append($('<td>').append($select_group))
            );

            div.append($table);

            let $add_button = $('<button>').text('Add profile').click(function() {profiles_plugin.click_add();})
            let $save_button = $('<button>').text('Save profile').click(function() {profiles_plugin.click_save();})
            let $test_button = $('<button>').text('Test').click(function() {profiles_plugin.click_test();})
            let $clear_button = $('<button>').text('Clear').click(function() {profiles_plugin.click_clear();})
            div.append($('<p>').append($add_button).append($save_button).append($test_button).append($clear_button));

            div.append($('<div>').attr('id', 'profile_graph'));
        });
    }

    click_remove() {
        let selected_option = $('#profile_select').val();
        $('#profile_select option[value=\''+selected_option+'\']').remove();
        // console.log('Remove profile: '+selected_option);
        socket.emit('remove_profile', selected_option);
        profiles_plugin.click_clear();
    }
    click_add() {
        // console.log('Add profile');
        let profile_info = {
            profile_uiname: $('#input_prof_uiname').val(),
            database: $('#input_prof_db').val(),
            measurement: $('#input_prof_meas').val(),
            field: $('#input_prof_field').val(),
            multiplier: $('#input_prof_mult').val(),
            profile_type: $('#input_prof_type').val(),
            start_datetime: $('#input_prof_startdt').val(),
            end_datetime: $('#input_prof_enddt').val(),
            embedUrl: $('#input_prof_embedurl').val(),
            group: $('#add_to_group_select').val()
        };
        socket.emit('add_profile', profile_info);
    }
    click_save() {
        let selected_option = $('#profile_select').val();
        if (selected_option !== 'first_select_profile') {
            let profile_info = {
                id: selected_option,
                profile_uiname: $('#input_prof_uiname').val(),
                database: $('#input_prof_db').val(),
                measurement: $('#input_prof_meas').val(),
                field: $('#input_prof_field').val(),
                multiplier: $('#input_prof_mult').val(),
                profile_type: $('#input_prof_type').val(),
                start_datetime: $('#input_prof_startdt').val(),
                end_datetime: $('#input_prof_enddt').val(),
                embedUrl: $('#input_prof_embedurl').val(),
                group: $('#add_to_group_select').val()
            };
            socket.emit('save_profile', profile_info);
        }
    }
    click_test() {
        let selected_option = $('#profile_select').val();
        if (selected_option !== 'first_select_profile') {
            let profile_info = {
                id: selected_option,
                profile_uiname: $('#input_prof_uiname').val(),
                database: $('#input_prof_db').val(),
                measurement: $('#input_prof_meas').val(),
                field: $('#input_prof_field').val(),
                multiplier: $('#input_prof_mult').val(),
                filters: [],
                profile_type: $('#input_prof_type').val(),
                start_datetime: $('#input_prof_startdt').val(),
                end_datetime: $('#input_prof_enddt').val(),
                embedUrl: $('#input_prof_embedurl').val(),
                group: $('#add_to_group_select').val()
            };
            socket.emit('test_profile', profile_info, function(embed_url) {
                if (embed_url) {
                    $('#input_prof_embedurl').attr('value', embed_url);
                    $('#profile_graph').html('<iframe width="100%" height="200px" src="'+embed_url+'"></iframme>');
                } else {
                    $('#profile_graph').html('');
                }
            });
        }
    }
    click_clear() {
        // console.log('Clear profile');
        $('#profile_select').val('first_select_profile');

        $('#input_prof_uiname').attr('value', '');
        $('#input_prof_db').attr('value', '');
        $('#input_prof_meas').attr('value', '');
        $('#input_prof_field').attr('value', '');
        $('#input_prof_mult').attr('value', '');
        $('#input_prof_type').attr('value', '');
        $('#input_prof_startdt').attr('value', '');
        $('#input_prof_enddt').attr('value', '');
        $('#input_prof_embedurl').attr('value', '');

        $('#profile_graph').html('');
    }
    select_profile() {
        let selected_option = $('#profile_select').val();
        let profile_info = profiles_plugin.profiles_list['profiles'][selected_option];

        // console.log(profile_info);

        $('#input_prof_uiname').attr('value', profile_info.profile_uiname);
        $('#input_prof_db').attr('value', profile_info.database);
        $('#input_prof_meas').attr('value', profile_info.measurement);
        $('#input_prof_field').attr('value', profile_info.field);
        $('#input_prof_mult').attr('value', profile_info.multiplier);
        $('#input_prof_type').attr('value', profile_info.profileType);
        $('#input_prof_startdt').attr('value', profile_info.start_datetime);
        $('#input_prof_enddt').attr('value', profile_info.end_datetime);
        $('#input_prof_embedurl').attr('value', profile_info.embedUrl);

        let $select = $('#add_to_group_select');
        let setting_type = profile_info.setting_type;
        let selected_group = null;
        if (setting_type == 'project') {
            selected_group = profile_info.project_name;
        } else {
            for (let i=0; i<profiles_plugin.profiles_list['groups'].length; i++) {
                if (profiles_plugin.profiles_list['groups'][i].setting_type == setting_type) {
                    selected_group = profiles_plugin.profiles_list['groups'][i].project_name;
                }
            }
        }
        $select.val(selected_group);

        if (profile_info.embedUrl) {
            $('#profile_graph').html('<iframe width="100%" height="200px" src="'+profile_info.embedUrl+'"></iframme>');
        } else {
            $('#profile_graph').html('');
        }
    }

    settings_window_contents() {
        let $div = $('<div>').attr('id', 'profiles_settings_window_div');
        profiles_plugin.get_profiles_settings($div);
        return $div;
    }

    create_drag_drop() {
        self = this;

        let $droparea = $('<div>').attr('id', 'csv-upload-area');
        let $form = $('<form>').addClass('upload-form');
        let $p1 = $('<p>').text('To upload csv files with profile information use drag & drop from your file explorer or click the button below.');
        let $input = $('<input type="file" multiple>').attr('id', 'fileElem');
        let $label = $('<label for="fileElem">').addClass('button').text('Select file(s)');
        let $progress = $('<progress>').attr('id', 'progress-bar').attr('max', 100).attr('value', 0);
        let $message = $('<p>').attr('id', 'csv-message');
        $droparea.append($form);
        $input.change(function(e) {
            handleFiles(this.files);
        });
        $form.append($p1);
        $form.append($input);
        $form.append($label);
        $droparea.append($progress);
        $droparea.append($message);

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
            $('#csv-message').text('Uploading CSV files')
            let selected_group = $('#profile_group_select').val();

            handleFiles(files, selected_group);
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

        function handleFiles(files, selected_group) {
            files = [...files];
            files.forEach(function (file) {
                let extension = file.name.split('.').pop();
                if (extension=="csv") {
                    let uuid = uuidv4();
                    self.files[uuid] = file;
                    initializeProgress(uuid);
                    uploadFile(file, uuid, selected_group);
                } else {
                    alert("Not a csv file: " + file.name);
                }
            });
        }

        function uploadFile(file, uuid, selected_group) {
            console.log("Uploading ", file);

            let reader = new FileReader();
            reader.onload = function() {
                // reading finished
                self.blob[uuid] = reader.result;
                socket.emit('profile_csv_upload', {'message_type': 'start', 'uuid': uuid, 'name':  file.name, 'size': file.size,
                                        'content': '', 'filetype': file.type, 'group': selected_group });
            };
            reader.onerror = function() {
                console.log(reader.error);
                $('#csv-message').text('Uploading failes: '+ reader.error)
                alert("Uploading failed: \n" + reader.error);
            };
            reader.readAsArrayBuffer(file);
        }
        return $droparea;
    }

    create_group_select(div) {
        socket.emit('get_profile_group_list', function(profile_group_list) {
            // console.log(profile_group_list);
            let $select = $('<select>').attr('id', 'profile_group_select');
            for (let gr=0; gr<profile_group_list.length; gr++) {
                let $option = $('<option>').val(profile_group_list[gr].name).text(profile_group_list[gr].name);
                // console.log(profile_group_list[gr]);
                $select.append($option);
            }
            div.append($select);
        });
    }

    upload_profiles_window_contents() {
        let $div = $('<div>').attr('id', 'upload_profiles_window_div');
        $div.append($('<h1>').text('Upload profiles'));
        $div.append($('<p>').text('First select in which group (or project) you want to upload the profiles. '+
            'This determines who else can see and use these profiles'));
        let $group_select = $('<div>');
        $div.append($('<p>').append($group_select));
        profiles_plugin.create_group_select($group_select);

        $div.append($('<p>').text('CSV files with profile data must adhere to a certain format:'))
        $div.append($('<ul>')
            .append($('<li>').text('there is one row with the column headers'))
            .append($('<li>').text('the first column must contain the datetime field (format \'DD-MM-YYYY HH:MM\')'))
            .append($('<li>').text('dates/times must be in UTC (without daylight saving)'))
            .append($('<li>').text('different profiles can be added using more than one column'))
            .append($('<li>').text('profiles are uploaded to the standard database, using the csv filename and the'+
                ' column name as identifiers (they must be unique, else data will be overwritten)'))
            .append($('<li>').text('use a \'.\' as a decimal seperator'))
            .append($('<li>').text('a full year profile contains 8760 profile elements (or 8784 for a leap year)'))
        );

        $div.append(profiles_plugin.create_drag_drop());
        return $div;
    }

    create_profiles_management(div) {
        socket.emit('get_profiles_list', function(profiles_list) {
            // console.log(profiles_list);
            profiles_plugin.profiles_list = profiles_list;

            let $select = $('<select>').attr('id', 'mult_profile_select').attr('multiple', 'multiple').attr('size', '15');
            let group_list = profiles_list['groups'];
            let profile_info = Object.entries(profiles_list['profiles']);
            for (let gr=0; gr<group_list.length; gr++) {
                let $optgroup = $('<optgroup>').attr('label', group_list[gr].name);
                for (let pr=0; pr<profile_info.length; pr++) {
                    if (group_list[gr].setting_type == profile_info[pr][1].setting_type) {
                        if (profile_info[pr][1].setting_type == 'project' &&
                            profile_info[pr][1].project_name != group_list[gr].project_name) continue;

                        let $option = $('<option>').val(profile_info[pr][0]).text(profile_info[pr][1].profile_uiname);
                        $optgroup.append($option);
                    }
                }
                $select.append($optgroup);
            }
//        $select.change(function() {profiles_plugin.select_profile();});
            div.append($select);

            let $delete_button = $('<button>').text('Delete profiles').click(function() {profiles_plugin.click_delete_profiles();});
            div.append($('<p>').append($delete_button));
        });
    }

    click_delete_profiles() {
        let selected_option = $('#mult_profile_select').val();
        $('#mult_profile_select option:selected').remove();
        // console.log('Remove profile: '+selected_option);
        socket.emit('remove_profile', selected_option);
    }

    profiles_management_window_contents() {
        let $div = $('<div>').attr('id', 'profiles_management_window_div');
        $div.append($('<h1>').text('Profiles management'));
        profiles_plugin.create_profiles_management($div);
        return $div;
    }

    create_databases_settings(div) {
        socket.emit('get_profiles_list', function(settings) {
            console.log(JSON.stringify(settings, undefined, 4));
            let $par = $('<pre>').text(JSON.stringify(settings, undefined, 4))
            div.append($par);
        });
    }


    db_settings_window_contents() {
        let $div = $('<div>').attr('id', 'db_settings_window_div');
        $div.append($('<h1>').text('Profile database settings'));
        profiles_plugin.create_databases_settings($div);
        return $div;
    }

    static create(event) {
        if (event.type === 'client_connected') {
            profiles_plugin = new Profiles();
            console.log("profiles_plugin initiated!!")
            return profiles_plugin;
        }
        if (event.type === 'settings_menu_items') {
            let menu_items = {
                'value': 'profiles_plugin_settings',
                'text': 'Profiles plugin',
                'settings_func': profiles_plugin.settings_window_contents,
                'sub_menu_items': [
                    {
                        'value': 'upload_profiles',
                        'text': 'Upload profiles',
                        'settings_func': profiles_plugin.upload_profiles_window_contents,
                        'sub_menu_items': []
                    },
                    {
                        'value': 'delete_profiles',
                        'text': 'Delete profiles',
                        'settings_func': profiles_plugin.profiles_management_window_contents,
                        'sub_menu_items': []
                    },
                    {
                        'value': 'profile_db_settings',
                        'text': 'Profile database settings',
                        'settings_func': profiles_plugin.db_settings_window_contents,
                        'sub_menu_items': []
                    },
                ]
            };

            return menu_items;
        }
    }
}

var profiles_plugin;

$(document).ready(function() {
    extensions.push(function(event) { return Profiles.create(event) });
});