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

// ------------------------------------------------------------------------------------------------------------
//  Shapefile functions - Not working at the moment
// ------------------------------------------------------------------------------------------------------------
function load_shapefile() {
    var files = document.getElementById('shapefile').files;
    if (files.length == 0) {
        console.log('filelength is zero');
        return; //do nothing if no file given yet
    }

    var file = files[0];

    if (file.name.slice(-3) != 'zip') {             // Only accept .zip. All others, return.
        document.getElementById('warning').innerHTML = 'Select .zip file';
        return;
    } else {
        document.getElementById('warning').innerHTML = ''; //clear warning message.
        handleZipFile(file);
    }
};

//More info: https://developer.mozilla.org/en-US/docs/Web/API/FileReader
function handleZipFile(file){
    console.log('handle zip file');
    var reader = new FileReader();
    reader.onload = function() {
        if (reader.readyState != 2 || reader.error){
            console.log("error");
            return;
        } else {
            console.log("no error");
            convert_shapefile_to_layer(reader.result);
        }
    }
    reader.readAsArrayBuffer(file);
}

function convert_shapefile_to_layer(buffer) {
    shp(buffer).then(function(geojson) {	            //More info: https://github.com/calvinmetcalf/shapefile-js
        console.log('shapefile addto map');
        var layer = L.shapefile(geojson).addTo(map);       //More info: https://github.com/calvinmetcalf/leaflet.shapefile
        console.log(layer);
    });
}

function show_add_shapefile() {
    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>Add shapefile</h1>';
    sidebar_ctr.innerHTML += '<p><label for="input">Select a zipped shapefile:</label><input type="file" id="shapefile"></p>';
    sidebar_ctr.innerHTML += '<button onclick="sidebar.hide();load_shapefile();">Load shapefile</button></p>';
    sidebar_ctr.innerHTML += '<span id="warning"></span>';

    sidebar.show();
}
