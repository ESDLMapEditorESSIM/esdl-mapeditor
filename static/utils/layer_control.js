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

var layer_control = null;

// https://stackoverflow.com/questions/24471708/prevent-jstree-node-select

function getESDLFileContextMenu(node, tree)
{
    var items = {
        'delete' : {
            'label' : 'Remove EnergySystem',
            'icon': 'fa fa-trash-o',
            'action' : function () {
                let id = node.id;
                // console.log('removing '+id);
                remove_esdl_layer(id);
                // $('#esdl_layer_control_tree').jstree("delete_node", '#'+node.id);
                // tree.jstree("delete_node", '#'+node.id);
                tree.delete_node(node.id);
            }
        },
        'rename' : {
            'label' : 'Rename EnergySystem',
            'icon': 'far fa-edit',
            'action': function () {
                tree.edit(node);
                // console.log(node.text);
            }
        }
    }

    return items;
}

function add_layer_control() {
    if (layer_control) {
        map.removeControl(layer_control);
    }

    layer_control = L.control({position: 'topright'});
    layer_control.onAdd = function (map) {
        var div = L.DomUtil.create('div', 'info legend');

        $base_layer_control_tree = $('<div>').attr('id', 'blct');
        $(div).append($base_layer_control_tree);

        $base_layer_control_tree
            .on('ready.jstree', function() {
                let tree = $('#blct').jstree(true);
                // console.log(baseTree.children[0].label);
                tree.select_node([baseTree.children[0].label]);
            })
            .on('select_node.jstree', function(e, data) {
                let node = data.node;
                base_layer_group = $("#blct").jstree("get_node", 'group_es_layers');
                // console.log(base_layer_group);
                if (base_layer_group)
                    for (let bl=0; bl<base_layer_group.children.length; bl++) {
                        base_layer = base_layer_group.children[bl];
                        // console.log(base_layer);
                        bl_node = $("#blct").jstree("get_node", base_layer);
                        if ($("#blct").jstree(true).is_selected(bl_node)) {
                            if (!map.hasLayer(baseTree.children[bl_node.data.baseTreeIndex].layer)) {
                                map.addLayer(baseTree.children[bl_node.data.baseTreeIndex].layer);
                            }
                        } else {
                            if (map.hasLayer(baseTree.children[bl_node.data.baseTreeIndex].layer)) {
                                map.removeLayer(baseTree.children[bl_node.data.baseTreeIndex].layer);
                            }
                        }
                    }
            })
            // These two events do only work if tie_selection is set to false
            // .on('check_node.jstree', function(e, data) {
            //     let node = data.node;
            //     if (!map.hasLayer(baseTree.children[node.data.baseTreeIndex].layer))
            //         map.addLayer(baseTree.children[node.data.baseTreeIndex].layer);
            // })
            // .on('uncheck_node.jstree', function(e, data) {
            //     let node = data.node;
            //     if (map.hasLayer(baseTree.children[node.data.baseTreeIndex].layer))
            //         map.removeLayer(baseTree.children[node.data.baseTreeIndex].layer);
            // })
            .jstree({
                "core" : {
                    "data": get_base_layers_control_tree_data(),
                    // so that create works for contextmenu plugin
                    "check_callback" : true,
                    "multiple": false
                },
                "plugins": ["checkbox", "types", "contextmenu"], // , "state"], // , "ui", "crrm", "dnd"],
                "checkbox": {
                    "three_state": false,
                    "whole_node": false
                },
                "contextmenu": {
                    "items": {}
                    // "select_node": false
                },
                "types" : {
                    "group" : {
                        "a_attr": {
                            "class": "no_checkbox"
                        }
                    },
                    "base-layer" : {
                        "icon" : "fas fa-layer-group layer-node"
                    }
                }
            });

        $esdl_layer_control_tree = $('<div>').attr('id', 'esdl_lct');
        $(div).append($esdl_layer_control_tree);

        $esdl_layer_control_tree
            .on('select_node.jstree', function(e, data) {
                // console.log('select_node event');
                // console.log(data);
                let node = data.node;
                // Execute select_active_layer here instead of in the conditionalselect event handler, such that
                // making an ESDL layer invisible doesn't set it to the active layer without moving the blue bar
                select_active_layer(node.id);
            })
            .on('ready.jstree', function() {
                let tree = $('#esdl_lct').jstree(true);
                tree.select_node(active_layer_id);
            })
            .on('load_node.jstree', function(e, data) {
                let tree = $('#esdl_lct').jstree(true);
                let root_node = data.node;
                for (ch=0; ch<root_node.children_d.length; ch++) {
                    child = tree.get_node(root_node.children_d[ch]);
                    if (child.type === 'layer') {
                        layer_data = child.data;
                        if (map.hasLayer(esdl_list[layer_data.es_id].layers[layer_data.layer_name]))
                            tree.check_node(child);
                    }
                }
            })
            .on('check_node.jstree', function(e, data) {
                let tree = $('#esdl_lct').jstree(true);
                let node = data.node;
                if (node.type === 'esdl-file') {    // check an entire ESDL file, show the ESDL layers that were visible
                    for (let c=0; c<node.children.length; c++) {
                        child = tree.get_node(node.children[c]);
                        if (tree.is_checked(child)) {
                            show_esdl_layer_on_map(child.data.es_id, child.data.layer_name);
                        }
                    }
                }
                if (node.type === 'layer') {    // check an individual ESDL layer
                    if (tree.is_checked(node.parent)) {
                        show_esdl_layer_on_map(node.data.es_id, node.data.layer_name);
                    }
                }
            })
            .on('uncheck_node.jstree', function(e, data) {
                let tree = $('#esdl_lct').jstree(true);
                let node = data.node;
                if (node.type === 'esdl-file') {    // uncheck an entire ESDL file, hide the ESDL layers that are visible
                    for (let c=0; c<node.children.length; c++) {
                        child = tree.get_node(node.children[c]);
                        if (tree.is_checked(child)) {
                            hide_esdl_layer_from_map(child.data.es_id, child.data.layer_name);
                        }
                    }
                }
                if (node.type === 'layer') {    // uncheck an individual ESDL layer
                    hide_esdl_layer_from_map(node.data.es_id, node.data.layer_name);
                }
            })
            // .on("dblclick.jstree", function (e) {
            //     var instance = $.jstree.reference(this),
            //     node = instance.get_node(e.target);
            //     console.log('Double click event');
            // })
            .on('click', '.jstree-anchor', function (e, data) {
                // console.log($('#esdl_lct').jstree(true).is_checked(e.target));
                // console.log($(e.target.parentNode).hasClass('jstree-checked'))
                // if ($(e.target.parentNode).hasClass('jstree-checked'))

                // only has this behaviour on the sublayer level...   else check-uncheck again
                // TODO: find better way of solving this
                if ($(e.target.parentNode.parentNode).attr('aria-level') == 3) {
                    // this enables that esdl sublayers can be checked and unchecked while not being selected
                    if ($('#esdl_lct').jstree(true).is_checked(e.target))
                        $('#esdl_lct').jstree(true).uncheck_node(e.target);
                    else
                        $('#esdl_lct').jstree(true).check_node(e.target);
                }
            })
            .on('set_text.jstree', function(e, data) {
                let tree = $("#esdl_lct").jstree(true);
                node = data.obj;
                new_title = data.text;
                // console.log('Set EnergySystem name');
                rename_esdl_energy_system(node.id, node.text);
            })
            .jstree({
                "core" : {
                    "data": get_esdl_layer_control_tree_data(),
                    // so that create works for contextmenu plugin
                    "check_callback" : true,
                    "dblclick_toggle" : false
                },
                "plugins": ["checkbox", "contextmenu", "types", "conditionalselect"], // , "state"], // , "ui", "crrm", "dnd"],
                "contextmenu": {
                    "items": function ($node) {
                        var tree = $("#esdl_lct").jstree(true);
                        if ($node.type === 'esdl-file')
                            return getESDLFileContextMenu($node, tree);
                        else
                            return {};
                    },
                    "select_node": false
                },
                "checkbox": {
                    "three_state": false,
                    "whole_node": false,
                    "tie_selection": false      // uncouple selecting and checking
                },
                "conditionalselect" : function (node, e) {
                    console.log(node.state);
                    if (node.type === 'esdl-file') {
                        // console.log('Selected an ESDL file with id: '+node.id);
                        // This code is also triggered when an ESDL layer is hidden, so it activates an ESDL layer too
                        // select_active_layer(node.id);
                        // The next line checks the checkbox when clicking the title, but prevent the checkbox
                        // from being clicked itself --> results in check-uncheck
                        // $('#esdl_lct').jstree(true).check_node(e.target);
                        return true;
                    } else
                        return false;
                },
                "types" : {
                    "group" : {
                        "a_attr": {
                            "class": "no_checkbox"
                        }
                    },
                    "esdl-file": {
                        "icon" : "fas fa-bezier-curve layer-node"
                    },
                    "layer" : {
                        "icon" : "fas fa-layer-group layer-node"
                    }
                }
            });

        $('.vakata-context').css('z-index', 20000);

        // div.firstChild.onmousedown = div.firstChild.ondblclick = L.DomEvent.stopPropagation;
        div.onmousedown = div.ondblclick = div.oncontextmenu = L.DomEvent.stopPropagation;
        return div;
    };

    layer_control.addTo(map);
}

// Following function does not work because jstree is not loaded yet when it is called
//function set_selected_layer(layer_id) {
//    let tree = $('#esdl_lct').jstree(true);
//    to_be_activated_node = tree.get_node(layer_id);
//    console.log('found layer: ');
//    console.log(to_be_activated_node);
//    console.log('selecting node with id: '+layer_id);
//    tree.select_node(layer_id);
//}


function get_base_layers_control_tree_data() {
    let children = [];

    for (let i=0; i<baseTree['children'].length; i++) {
        let state = {};
        if (i==0)
            state = {"checked": true};

        let child = {
            id : baseTree['children'][i].label,
            text: baseTree['children'][i].label,
            icon: "",
            type: "base-layer",
            data: {
                baseTreeIndex: i
            },
            state: state,
            children: [],
            li_attr: {},
            a_attr: {}
        }
        children.push(child);
    }

    let group = {
        id : "group_es_layers",
        text: "Base layers",
        icon: "",
        type: "group",
        state: {
            opened : true
        },
        children: children,
        li_attr: {},
        "a_attr": {
            "class": "no_checkbox"
        }
    }

    return [group];
}

function get_esdl_layer_control_tree_data() {
    let children = [];

    for (let key in esdl_list) {
        let item = esdl_list[key];

        let esdl_sublayers = [
            { text: 'Area', type: "layer", state: {"checked": true}, data: {es_id: key, layer_name: 'area_layer'}},
            { text: 'Assets', type: "layer", state: {"checked": true}, data: {es_id: key, layer_name: 'esdl_layer'}},
            { text: 'Connections', type: "layer", state: {"checked": true}, data: {es_id: key, layer_name: 'connection_layer'}},
            { text: 'Buildings', type: "layer", state: {"checked": true}, data: {es_id: key, layer_name: 'bld_layer'}},
            { text: 'Potentials', type: "layer", state: {"checked": true}, data: {es_id: key, layer_name: 'pot_layer'}},
            { text: 'KPIs', type: "layer", state: {"checked": true}, data: {es_id: key, layer_name: 'kpi_layer'}},
            { text: 'Simulation results', type: "layer", state: {"checked": true}, data: {es_id: key, layer_name: 'sim_layer'}},
            { text: 'Notes', type: "layer", state: {"checked": true}, data: {es_id: key, layer_name: 'notes_layer'}}
        ];

        console.log('adding layer with id: '+ key);

        let esdl_layer = {
            id: key,
            text: item.title,
            type: "esdl-file",
            state: {"checked": true},
            children: esdl_sublayers
        }

        children.push(esdl_layer);
    }

    let group = {
        id : "group_base_layers",
        text: "ESDL layers",
        icon: "",
        type: "group",
        state: {
            opened : true
        },
        children: children,
        li_attr: {},
        "a_attr": {
            "class": "no_checkbox"
        }
    }

    return [group];
}