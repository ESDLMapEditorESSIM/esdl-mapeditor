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


class SpatialOperations {
    constructor() {
        this.initSocketIO();
    }

    initSocketIO() {
        socket.on('data', function(data) {
            console.log('Jee');
        });
    }

    open_window() {
        sidebar.setContent(spatial_operations_plugin.create_sidebar_content().get(0));
        sidebar.show();
    }

    create_sidebar_content() {
        let $div = $('<div>').attr('id', 'spatial-operations-main-div');
        let $title = $('<h1>').text('Spatial Operations');
        $div.append($title);

        let $content_div = $('<div>').addClass('sidebar-div');
        let $p_preprocess = $('<p>')
            .append($('<p>').text('To prepare the sub area triangilation'))
            .append($('<button>')
                .text('Preprocess subareas')
                .click(function() {
                    socket.emit('spatop_preprocess_areas', function(res) {
                        console.log(res);
                    });
                }));
        let $p_centroid = $('<p>')
            .append($('<p>').text('To generate joints at the center of the sub area polygon'))
            .append($('<button>')
                .text('Joint Centroid')
                .click(function() {
                    socket.emit('spatop_joint_middle_subarea', function(res) {
                        console.log(res);
                    });
                }));
        let $p_delaunay_subarea = $('<p>')
            .append($('<p>').text('To perform the triangulation with the joints at the center of the sub area polygon'))
            .append($('<button>')
                .text('Subarea Joint Delaunay triangulation')
                .click(function() {
                    socket.emit('spatop_joint_delaunay_subarea', function(res) {
                        console.log(res);
                    });
                }));

         let $p_delaunay_joints = $('<p>')
            .append($('<p>').text('To perform the triangulation with all joints drawn on the map'+
                ' (you have to draw an Area too)'))
            .append($('<button>')
                .text('Joint Delaunay triangulation')
                .click(function() {
                    socket.emit('spatop_joint_delaunay', function(res) {
                        console.log(res);
                    });
                }));

        $content_div
            .append($('<p>').append($p_preprocess))
            .append($('<p>').append($p_centroid))
            .append($('<p>').append($p_delaunay_subarea))
            .append($('<p>').append($p_delaunay_joints));

        $div.append($content_div);

        return $div;
    }

    static create(event) {
        if (event.type === 'client_connected') {
            spatial_operations_plugin = new SpatialOperations();
            return spatial_operations_plugin;
        }
        if (event.type === 'add_contextmenu') {
            let layer = event.layer;
            let layer_type = event.layer_type;
            let id = layer.id;
            if (layer_type === 'area') {
                layer.options.contextmenuItems.push({
                    text: 'spatial operations',
                    icon: resource_uri + 'icons/AreaGeometry.png',
                    callback: function(e) {
                        spatial_operations_plugin.open_window(e, id);
                    }
                });
            }
        }
    }
}

var spatial_operations_plugin;   // global variable for the spatial operations plugin

$(document).ready(function() {
    extensions.push(function(event) { return SpatialOperations.create(event) });
});