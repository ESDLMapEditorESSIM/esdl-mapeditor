// ------------------------------------------------------------------------------------------------------------
//  WMS Layer functionality
// ------------------------------------------------------------------------------------------------------------
function add_layer() {
    layer_descr = document.getElementById('layer_descr').value;
    layer_url = document.getElementById('layer_url').value;
    layer_name = document.getElementById('layer_name').value;
    legend_url = document.getElementById('legend_url').value;
    select_layer_group = document.getElementById('add_to_group');
    group_id = select_layer_group[select_layer_group.selectedIndex].value;
    layer_id = uuidv4();

    socket.emit('command', {cmd: 'add_layer', id: layer_id, descr: layer_descr, url: layer_url, name: layer_name, group_id: group_id, legend_url: legend_url, visible: true});
    wms_layer_list['layers'][layer_id] = { description: layer_descr, url: layer_url, legend_url: legend_url, layer_name: layer_name, group_id: group_id };

    wms_layer_list['layers'][layer_id].layer_ref = L.tileLayer.wms(layer_url, {
        layers: layer_name,
        format:'image/png',
        transparent: true
    });
    wms_layer_list['layers'][layer_id].layer_ref.addTo(map);
    wms_layer_list['layers'][layer_id].layer_ref.bringToFront();
    wms_layer_list['layers'][layer_id].visible = true;

    var parent = $('#layer_tree li#li_wms_layer_list_'+group_id+' ul');
    var new_node = { "id":'li_'+layer_id, "text":layer_descr }; // , "state":{"checked":true} };
    $('#layer_tree').jstree("create_node", parent, new_node, "last", false, false);
    $('#layer_tree').jstree("check_node", '#li_'+layer_id);
}

function remove_layer(id) {
    socket.emit('command', {cmd: 'remove_layer', id: id});
    // console.log('remove layer: '+id);
    map.removeLayer(wms_layer_list['layers'][id].layer_ref);
    delete wms_layer_list['layers'][id];
}

function show_wms_layer(id) {
    // console.log('add layer to map: '+id);
    wms_layer_list['layers'][id].layer_ref.addTo(map);
    wms_layer_list['layers'][id].layer_ref.bringToFront();
    wms_layer_list['layers'][id].visible = true;
    if (wms_layer_list['layers'][id].legend_url !== "") {
        show_wms_legend(wms_layer_list['layers'][id].legend_url);
    }
}

function hide_wms_layer(id) {
    // console.log('remove layer from map: '+id);
    map.removeLayer(wms_layer_list['layers'][id].layer_ref);
    wms_layer_list['layers'][id].visible = false;
    if (wms_layer_list['layers'][id].legend_url !== "") {
        remove_wms_legend();
    }
}

function wmsLayerContextMenu(node)
{
    var items = {
        'delete' : {
            'label' : 'Delete layer',
            'action' : function () {
                let id = node.id.substring(3);
                console.log('removing '+id);
                remove_layer(id);
                $('#layer_tree').jstree("delete_node", '#'+node.id);
            }
        }
    }
    return items;
}

var tree_data = [];
function show_layers() {
    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>WMS Layers</h1>';
    tree = '<p><div id="layer_tree"></div></p>';
    sidebar_ctr.innerHTML = sidebar_ctr.innerHTML + tree;

    tree_data = [];
    for (var idx in wms_layer_list['groups']) {
        let group = wms_layer_list['groups'][idx];
        let group_id = group.id;
        let group_name = group.name;
        let tree_children = []
        for (var key in wms_layer_list['layers']) {
            let layer = wms_layer_list['layers'][key];
            let layer_group = layer.group_id;
            if (layer_group == group_id) {
                let value = wms_layer_list['layers'][key];
                tree_children.push({"id":"li_"+key, "text":value.description, "parent":"li_wms_layer_list_"+group_id});
            }
        }
        let tree_obj = {"id":"li_wms_layer_list_"+group_id, "text":group_name, "children":tree_children};
        tree_data.push(tree_obj);
    }

    sidebar_ctr.innerHTML += '<h2>Add layers:</h2>';
    table = '<table>';
    table += '<tr><td width=180>Description</td><td><input type="text" width="60" id="layer_descr"></td></tr>';
    table += '<tr><td width=180>URL</td><td><input type="text" width="60" id="layer_url"></td></tr>';
    table += '<tr><td width=180>Layer name</td><td><input type="text" width="60" id="layer_name"></td></tr>';
    table += '<tr><td width=180>Legend URL</td><td><input type="text" width="60" id="legend_url"></td></tr>';
    table += '<tr><td width=180>Add to group</td><td><select id="add_to_group">';
    for (var idx in wms_layer_list['groups']) {
        let group = wms_layer_list['groups'][idx];
        table += '<option value="'+group.id+'">'+group.name+'</value>';
    }
    table += '</select></td></tr>';

    table += '<tr><td><button onclick="add_layer();">Add layer</button></td><td>&nbsp;</td>';
    table += '</table>';
    sidebar_ctr.innerHTML = sidebar_ctr.innerHTML + table;

    // https://github.com/vakata/jstree/issues/593
    // Set the z-index of the contextmenu of jstree
//    $('.vakata-context').css('z-index', 20000);

    // TODO: Is this the right way (using event 'shown') to attach after building the DOM??
    sidebar.on('shown', function() {
        $(function () {
            $('#layer_tree')
                .on('select_node.jstree', function(e, data) {
                    console.log(data);
                    let id = data.node.id.substring(3);
                    if (!(id.startsWith("wms_layer_list"))) {
                        console.log('adding '+id);
                        show_wms_layer(id);
                    }
                })
                .on('deselect_node.jstree', function(e, data) {
                    let id = data.node.id.substring(3);
                    if (!(id.startsWith("wms_layer_list"))) {
                        console.log('removing '+id);
                        hide_wms_layer(id);
                    }
                })
                .jstree({
                    "core" : {
                        "data": tree_data,
                        // so that create works for contextmenu plugin
                        "check_callback" : true
                    },
                    "plugins": ["checkbox", "state", "contextmenu"], // , "ui", "crrm", "dnd"],
                    "contextmenu": {
                        "items": wmsLayerContextMenu
                    }
                });
            $('.vakata-context').css('z-index', 20000);
        });
    });

    sidebar.show();
//    $('.vakata-context').css('z-index', 20000);
}

function create_wms_layer_legend(url) {
    var legend_div = L.DomUtil.create('div', 'info legend');
    var legend_title_div = L.DomUtil.create('div', 'legend_title', legend_div);
    legend_title_div.innerHTML += 'Legend';

    LegendPicture_div = L.DomUtil.create('div', 'info legend', legend_div);
    LegendPicture_div.innerHTML = '<img src="'+url+'">'
    return legend_div;
}

var wms_legend = null;
function show_wms_legend(url) {
    if (wms_legend) {
        map.removeControl(wms_legend);
    }
    wms_legend = L.control({position: 'bottomright'});
    wms_legend.onAdd = function (map) {
        return create_wms_layer_legend(url);
    };
    wms_legend.addTo(map);
}

function remove_wms_legend() {
    if (wms_legend) {
        map.removeControl(wms_legend);
    }
}
