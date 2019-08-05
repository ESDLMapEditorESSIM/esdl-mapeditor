// Heat network extension


//function init() {}

function duplicate(event, id) {
    // console.log('Duplicating layer id = ', id)
    let area_bld_id = $( "#area_bld_select" ).val();
    socket.emit('duplicate', {asset_id: id, area_bld_id: area_bld_id});
}


function update(event) {
    if (event.type === 'add_contextmenu') {
        let layer = event.layer;
        let id = layer.id;
        // console.log('Extension HeatNetwork add_contextmenu for id=' + id)
        layer.options.contextmenuItems.push(
                { text: 'Duplicate', icon: resource_uri + 'icons/Duplicate.png', callback: function(e) { duplicate(e, id); } });
    }

}


$(document).ready(function() {
    extensions.push(update)
});