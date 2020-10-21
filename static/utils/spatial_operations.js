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
        $div.append($('<p>').text('This is very experimental functionality to experiment with some spatial algorithms'))

        let $content_div = $('<div>').addClass('sidebar-div');
        let $p_preprocess = $('<p>')
            .append($('<h2>').text('Area triangulation'))
            .append($('<p>')
                .text('To prepare the sub area triangulation')
                .append($('<br>'))
                .append($('<button>')
                    .text('Preprocess subareas')
                    .click(function() {
                        socket.emit('spatop_preprocess_areas', function(res) {
                            console.log(res);
                        });
                    })));
        let $p_centroid = $('<p>')
            .text('To generate joints at the center of the sub area polygon')
            .append($('<br>'))
            .append($('<button>')
                .text('Joint Centroid')
                .click(function() {
                    socket.emit('spatop_joint_middle_subarea', function(res) {
                        console.log(res);
                    });
                }));
        let $p_delaunay_subarea = $('<p>')
            .text('To perform the triangulation with the joints at the center of the sub area polygon')
            .append($('<br>'))
            .append($('<button>')
                .text('Subarea Joint Delaunay triangulation')
                .click(function() {
                    socket.emit('spatop_joint_delaunay_subarea', function(res) {
                        console.log(res);
                    });
                }));

        let $p_delaunay_joints = $('<p>')
            .append($('<h2>').text('Joints triangulation'))
            .append($('<p>')
                .text('To perform the triangulation with all joints drawn on the map'+
                    ' (you have to draw an Area too)')
                .append($('<br>'))
                .append($('<button>')
                    .text('Joint Delaunay triangulation')
                    .click(function() {
                        socket.emit('spatop_joint_delaunay', function(res) {
                            console.log(res);
                        });
                    })));

        let $p_connect_unconnected_assets = $('<p>').attr('id', 'p_conn_unconn_assets');

        $content_div
            .append($('<p>').append($p_preprocess))
            .append($('<p>').append($p_centroid))
            .append($('<p>').append($p_delaunay_subarea))
            .append($('<p>').append($p_delaunay_joints))
            .append($('<p>').append($p_connect_unconnected_assets));

        socket.emit('spatop_get_asset_types', function(res) {
            let $p = $('#p_conn_unconn_assets');
            console.log(res);

            if (res.length > 0) {
                $p.append($('<h2>').text('Connect unconnected assets'))
                    .append($('<p>').text('It takes the first port of the unconnected asset and tries to find a ' +
                        'port with opposite type to connect to. If that fails the asset is not connected.'))
                    .append($('<p>').text('Connect all unconnected:')
                        .append($('<select>').attr('id', 'select_connect_asset')))
                    .append($('<p>').text('to the nearest:')
                        .append($('<select>').attr('id', 'select_connect_to_asset')))
                    .append($('<button>')
                        .text('Go')
                        .click(function() {
                            let sca_choice = $('#select_connect_asset').val();
                            let scta_choice = $('#select_connect_to_asset').val();
                            socket.emit('spatop_connect_unconnected_assets', {
                                    connect_asset_type: sca_choice,
                                    connect_to_asset_type: scta_choice
                                }, function(res) {
                                    console.log(res);
                                }
                            );
                        }));

                let $sca = $('#select_connect_asset');
                let $scta = $('#select_connect_to_asset');
                for (let i=0; i<res.length; i++) {
                    $sca.append($('<option>').val(res[i]).text(res[i]));
                    $scta.append($('<option>').val(res[i]).text(res[i]));
                }
            } else {
                $p.append($('<p>').text('No assets in energysystem'));
            }
        });

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