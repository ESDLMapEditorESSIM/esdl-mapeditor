function get_edr_assets(url) {
    $.ajax({
        url: url,
        success: function(data){
            console.log(data);
        },
        dataType: "json"
    });
}

function get_esdl_edr_asset(url, id) {
    console.log(url);
    console.log(id);
    $.ajax({
        url: url + '/' + id,
        success: function(data){
            console.log(data);
        },
        dataType: "xml"
    });
}

function update_edr_asset_list() {

}

