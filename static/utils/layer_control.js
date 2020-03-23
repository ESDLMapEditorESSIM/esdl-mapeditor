var layer_control = null;

function ControlLayerContextMenu(node)
{
    var items = {}
    if (!node.data.readonly) {
        items = {
            'delete' : {
                'label' : 'Delete layer',
                'icon': 'fa fa-trash-o',
                'action' : function () {
                    let id = node.id.substring(3);
                    console.log('removing '+id);
                    remove_layer(id);
                    $('#layer_control_tree').jstree("delete_node", '#'+node.id);
                }
            }
        }
    }
    return items;
}

function create_layer_control_tree_data() {
    let tree_data = [];

    populate_base_layers(tree_data);
    populate_es_layers(tree_data);

    return tree_data;
}

function add_layer_control() {
    if (layer_control) {
        map.removeControl(layer_control);
    }
    console.log('Adding layer_control')

    layer_control = L.control({position: 'topright'});
    layer_control.onAdd = function (map) {
        var div = L.DomUtil.create('div', 'info legend');

        tree = '<p><div id="layer_control_tree"></div></p>';
        div.innerHTML = div.innerHTML + tree;

        let layer_control_tree_data = create_layer_control_tree_data();

        L.DomEvent.on(div, 'mouseover', function() {
            console.log('Yeah!');
            $(function () {

                $('#layer_control_tree')
                    .on('select_node.jstree', function(e, data) {
                        console.log(data);
                        let id = data.node.id.substring(3);
                    })
                    .on('deselect_node.jstree', function(e, data) {
                        let id = data.node.id.substring(3);
                    })
                    .jstree({
                        "core" : {
                            "data": layer_control_tree_data,
                            // so that create works for contextmenu plugin
                            "check_callback" : true
                        },
                        "plugins": ["checkbox", "state", "contextmenu", "types"], // , "ui", "crrm", "dnd"],
                        "contextmenu": {
                            "items": ControlLayerContextMenu,
                            "select_node": false
                        },
                        "checkbox": {
                            "three_state": false
                        },
                        "types" : {
                            "group" : {
                                "a_attr": {
                                    "class": "no_checkbox"
                                }
                            },
                            "esdl-file": {
                                "icon" : "fa fa-bezier-curve layer-node"
                            },
                            "layer" : {
                                "icon" : "fa fa-layer-group layer-node"
                            }
                        }
                    });
                $('.vakata-context').css('z-index', 20000);
            });
        });

        div.firstChild.onmousedown = div.firstChild.ondblclick = L.DomEvent.stopPropagation;
        return div;
    };

    layer_control.addTo(map);
}

function populate_base_layers(tree_data) {
    let children = [];

    for (let i=0; i<baseTree['children'].length; i++) {
        let child = {
            id : baseTree['children'][i].label,
            text: baseTree['children'][i].label,
            icon: "",
            type: "base-layer",
            state: {},
//            data: {
//                lyr: baseTree['children'][i].layer
//            },
            children: [],
            li_attr: {},
            a_attr: {}
        }
        children.push(child);
    }

    let group = {
        id : "group_es_layers",
        text: "ESDL layers",
        icon: "",
        type: "group",
        state: {
            opened : true
        },
        children: children,
        li_attr: {},
        a_attr: {}
    }

    tree_data.push(group);
}

function populate_es_layers(tree_data) {
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
        text: "Base layers",
        icon: "",
        type: "group",
        state: {
            opened : true
        },
        children: children,
        li_attr: {},
        a_attr: {}
    }

    tree_data.push(group);
}