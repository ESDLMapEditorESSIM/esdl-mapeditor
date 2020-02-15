// ------------------------------------------------------------------------------------------------------------
//  WMS Layer functionality
// ------------------------------------------------------------------------------------------------------------
function add_layer() {
    layer_descr = document.getElementById('layer_descr').value;
    layer_url = document.getElementById('layer_url').value;
    layer_name = document.getElementById('layer_name').value;
    layer_id = uuidv4();

    socket.emit('command', {cmd: 'add_layer', id: layer_id, descr: layer_descr, url: layer_url, name: layer_name, visible: true});
    wms_layer_list[layer_id] = { description: layer_descr, url: layer_url, layer_name: layer_name }

    wms_layer_list[layer_id].layer_ref = L.tileLayer.wms(layer_url, {
        layers: layer_name,
        format:'image/png',
        transparent: true
    });
    wms_layer_list[layer_id].layer_ref.addTo(map);
    wms_layer_list[layer_id].layer_ref.bringToFront();
    wms_layer_list[id].visible = true;
}

function remove_layer(id) {
    socket.emit('command', {cmd: 'remove_layer', id: id});
    // console.log('remove layer: '+id);
    map.removeLayer(wms_layer_list[id].layer_ref);
    delete wms_layer_list[id];
}

function click_layer(id) {
    checkbox = document.getElementById('cb_'+id);
    if (checkbox.checked) {
        // console.log('add layer to map: '+id);
        wms_layer_list[id].layer_ref.addTo(map);
        wms_layer_list[id].layer_ref.bringToFront();
        wms_layer_list[id].visible = true;
        if (wms_layer_list[id].legend_url !== "") {
            show_wms_legend(wms_layer_list[id].legend_url);
        }
    } else {
        // console.log('remove layer from map: '+id);
        map.removeLayer(wms_layer_list[id].layer_ref);
        wms_layer_list[id].visible = false;
        if (wms_layer_list[id].legend_url !== "") {
            remove_wms_legend();
        }
    }
}

function show_layers() {
    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>WMS Layers</h1>';
    table = '<table>';
    for (var key in wms_layer_list) {
        let value = wms_layer_list[key];

        table += '<tr><td><input type="checkbox" id="cb_'+ key +'" name="' +value.description+ '" onclick="click_layer(\''+key+'\');"';
        if (value.visible) { table += ' checked'; }
        table +='>';
        table += '<label for="'+value.id+'" title="' +value.url+' - '+value.layer_name + '">'+value.description+'</label></td>';
        table += '<td><button onclick="remove_layer(\'' + key + '\');">Del</button></td></tr>';
    }
    table += '</table>';
    sidebar_ctr.innerHTML += table;

    sidebar_ctr.innerHTML += '<h2>Add layers:</h2>';
    table = '<table>';
    table += '<tr><td width=180>Description</td><td><input type="text" width="60" id="layer_descr"></td></tr>';
    table += '<tr><td width=180>URL</td><td><input type="text" width="60" id="layer_url"></td></tr>';
    table += '<tr><td width=180>Layer name</td><td><input type="text" width="60" id="layer_name"></td></tr>';
    table += '<tr><td><button onclick="add_layer();">Add layer</button></td><td>&nbsp;</td>';
    table += '</table>';
    sidebar_ctr.innerHTML = sidebar_ctr.innerHTML + table;

    sidebar.show();
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
