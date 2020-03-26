var layer_control = null;

// https://stackoverflow.com/questions/24471708/prevent-jstree-node-select

function getESDLFileContextMenu(node, tree)
{
    var items = {
        'delete' : {
            'label' : 'Remove EnergySystem',
            'icon': 'fa fa-trash-o',
            'action' : function () {
                let id = node.id.substring(3);
                console.log('removing '+id);
                remove_layer(id);
//                $('#esdl_layer_control_tree').jstree("delete_node", '#'+node.id);
                tree.jstree("delete_node", '#'+node.id);
            }
        }
    }

    return items;
}

//function create_layer_control_tree_data() {
//    let tree_data = [];
//
//    populate_base_layers(tree_data);
//  //  populate_es_layers(tree_data);
//
//    return tree_data;
//}

function add_layer_control() {
    if (layer_control) {
        map.removeControl(layer_control);
    }
    console.log('Adding layer_control')

    layer_control = L.control({position: 'topright'});
    layer_control.onAdd = function (map) {
        var div = L.DomUtil.create('div', 'info legend');

        $base_layer_control_tree = $('<div>').attr('id', 'blct');
        $(div).append($base_layer_control_tree);

        // let layer_control_tree_data = create_layer_control_tree_data();

        $base_layer_control_tree
            .jstree({
                "core" : {
                    "data": get_base_layers_control_tree_data(),
                    // so that create works for contextmenu plugin
                    "check_callback" : true,
                    "multiple": false
                },
                "plugins": ["checkbox", "state", "types"], // , "ui", "crrm", "dnd"],
                "checkbox": {
                    "three_state": false,
                    "whole_node": false
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
            })
            .jstree(true).load_node('#');   // to get the checkbox into the selected state (initially)

        $esdl_layer_control_tree = $('<div>').attr('id', 'esdl_lct');
        $(div).append($esdl_layer_control_tree);

        $esdl_layer_control_tree
//            .on('select_node.jstree', function(e, data) {
//                console.log('select_node event');
//                console.log(data);
//            })
//            .on('check_node.jstree', function(e, data) {
//                console.log('check_node event');
//                console.log(data);
//            })
//            .on('uncheck_node.jstree', function(e, data) {
//                console.log('uncheck_node event');
//                console.log(data);
//            })
//            .on("dblclick.jstree", function (e) {
//                var instance = $.jstree.reference(this),
//                node = instance.get_node(e.target);
//                console.log('Double click event');
//            })
            .on('click', '.jstree-anchor', function (e, data) {
//                console.log('click event on .jstree-anchor');
//                console.log($('#esdl_lct').jstree(true).is_checked(e.target));
//                console.log($(e.target.parentNode).hasClass('jstree-checked'))
//                if ($(e.target.parentNode).hasClass('jstree-checked'))

                // only has this behaviour on the sublayer level...   else check-uncheck again
                if ($(e.target.parentNode.parentNode).attr('aria-level') == 3) {
                    // this enables that esdl sublayers can be checked and unchecked while not being selected
                    if ($('#esdl_lct').jstree(true).is_checked(e.target))
                        $('#esdl_lct').jstree(true).uncheck_node(e.target);
                    else
                        $('#esdl_lct').jstree(true).check_node(e.target);
                }
            })
//            .on('deselect_node.jstree', function(e, data) {
//                console.log('deselect_node event');
//                console.log(data);
//            })
            .jstree({
                "core" : {
                    "data": get_esdl_layer_control_tree_data(),
                    // so that create works for contextmenu plugin
                    "check_callback" : true,
                    "dblclick_toggle" : false
                },
                "plugins": ["checkbox", "contextmenu", "types", "conditionalselect", "state"], // , "ui", "crrm", "dnd"],
                "contextmenu": {
                    "items": function ($node) {
                        var tree = $("#esdl_lct").jstree(true);
						if($node.type === 'esdl-file')
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
//                    console.log(node);
                    if(node.type === 'esdl-file') {
                        console.log('Selected an ESDL file!!!');
                        // The next line checks the checkbox when clicking the title, but prevent the checkbox
                        // from being clocked itself --> results in check-uncheck
//                        $('#esdl_lct').jstree(true).check_node(e.target);
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

        div.firstChild.onmousedown = div.firstChild.ondblclick = L.DomEvent.stopPropagation;
        return div;
    };

    layer_control.addTo(map);
}

function get_base_layers_control_tree_data() {
    let children = [];

    for (let i=0; i<baseTree['children'].length; i++) {
        let state = {};
        if (i==0)
            state = { checked: true };

        let child = {
            id : baseTree['children'][i].label,
            text: baseTree['children'][i].label,
            icon: "",
            type: "base-layer",
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
            { text: 'Area', type: "layer" }, //, layer: es.layers['area_layer'] },
            { text: 'Assets', type: "layer" }, //, layer: es.layers['esdl_layer'] },
            { text: 'Connections', type: "layer" }, //, layer: es.layers['connection_layer'] },
            { text: 'Buildings', type: "layer" }, //, layer: es.layers['bld_layer'] },
            { text: 'Potentials', type: "layer" }, //, layer: es.layers['pot_layer'] },
            { text: 'Simulation results', type: "layer" }, //, layer: es.layers['sim_layer'] }
        ];

        let esdl_layer = {
            id: key,
            text: item.title,
            type: "esdl-file",
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