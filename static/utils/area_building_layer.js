// --------------------------------------------------------------------------------------------------------
//   Visualize areas and buildings
// --------------------------------------------------------------------------------------------------------
var geojson_area_layer = false;
var geojson_area_geojson;
var geojson_building_layer = false;
var geojson_building_geojson;
var building_color_method = 'building type';

var areaLegend;             // the leaflet control
var buildingLegend;         // the leaflet control

var areaLegendChoice;       // will be initialized with the first KPI
var buildingLegendChoice;

var get_area_color;         // function to get color of an area
var get_building_color = get_buildingYear_colors;     // function to get color of a building

// ------------------------------------------------------------------------------------------------------------
//  Dictionary with info about what KPIs are set in the area and what set of values or what ranges
// ------------------------------------------------------------------------------------------------------------
var area_KPIs = {};
var building_KPIs = {};

function isNumeric(val) { return !isNaN(val); }

function preprocess_layer_data(layer_type, layer_data, kpi_list) {
    if (layer_type === "area") {
        get_area_color = null;
        areaLegendChoice = null;
    }
    if (layer_type === "building") {
        get_building_color = null;
        buildingLegendChoice = null;
    }
    for (l_index in layer_data) {
        let layer = layer_data[l_index];
        let KPIs = layer.properties.KPIs;
        for (kpi in KPIs) {
            KPI_value = KPIs[kpi];
            if (KPI_value != "") {
                if (!(kpi in kpi_list)) {
                    if (layer_type === "area" && !areaLegendChoice) { areaLegendChoice = kpi; }
                    if (layer_type === "building" && !buildingLegendChoice) { buildingLegendChoice = kpi; }
                    if (isNumeric(KPI_value)) {
                        if (layer_type === "area" && !get_area_color) { get_area_color = get_area_range_colors; }
                        if (layer_type === "building" && !get_building_color) { get_building_color = get_building_range_colors; }
                        value = parseFloat(KPI_value);
                        kpi_list[kpi] = { "min": value, "max": value };
                    } else {
                        if (layer_type === "area" && !get_area_color) { get_area_color = get_area_array_colors; }
                        if (layer_type === "building" && !get_building_color) { get_building_color = get_building_array_colors; }
                        kpi_list[kpi] = [KPI_value];
                    }
                } else {
                    if (isNumeric(KPI_value)) {
                        value = parseFloat(KPI_value);
                        if (value < kpi_list[kpi]["min"]) { kpi_list[kpi]["min"] = value; }
                        if (value > kpi_list[kpi]["max"]) { kpi_list[kpi]["max"] = value; }
                    } else {
                        // if (!(KPI_value in (kpi_list[kpi]))) {       // why is this not working?
                        // console.log(kpi_list+" "+kpi);

                        if (!(kpi_list[kpi].includes(KPI_value))) {
                            (kpi_list[kpi]).push(KPI_value);
                        }
                    }
                }
            }
        }
    };
    if (layer_type === "area") {
        if (!get_area_color) { get_area_color = get_area_default_color; }
    }
    if (layer_type === "building") {
        if (!get_building_color ) { get_building_color = get_building_default_color; }
    }
    // console.log(kpi_list);
}

function calc_order_of_magnitude(n) {
    var order = Math.floor(Math.log(Math.abs(n)) / Math.LN10
                       + 0.000000001); // because float math sucks like that
    return Math.pow(10,order);
}

// TODO: what if min == max???
function create_ranges(min, max) {
    var ranges = [];
    if (min == 0 && max == 0) {
        ranges = [0, 1];
//    } else if (min == max) {
//    } else if (min >= 0) {
    } else {
        var delta = Math.abs(max - min);
        var order_of_magnitude = calc_order_of_magnitude(delta);
        var start = 0;
        var numsteps = 1;
        var stepsize = 0;
        if (order_of_magnitude != 0) {
            start = Math.floor(min / order_of_magnitude) * order_of_magnitude;
            numsteps = Math.ceil(delta / order_of_magnitude);

            if (numsteps < 3) {
                numsteps *= 4;
                stepsize = order_of_magnitude / 4;
            } else if (numsteps < 4) {
                numsteps *= 2;
                stepsize = order_of_magnitude / 2;
            } else if (numsteps > 8) {
                numsteps /= 2;
                stepsize = order_of_magnitude * 2;
            } else {
                stepsize = order_of_magnitude;
            }
        }

        for (i=0; i<numsteps; i++) {
            ranges[i] = start + i * stepsize;
        }
//    } else {
//        alert('support for negative values in calculating legends should still be implemented');
    }
    return ranges;
}

// ------------------------------------------------------------------------------------------------------------
//  Building colors based on their usage type
// ------------------------------------------------------------------------------------------------------------
var building_type_colors = {
    'UNDEFINED': '#808080',
    'RESIDENTIAL': '#a6cee3',
    'GATHERING': '#1f78b4',
    'PRISON': '#b2df8a',
    'HEALTHCARE': '#33a02c',
    'INDUSTRY': '#fb9a99',
    'OFFICE': '#e31a1c',
    'EDUCATION': '#fdbf6f',
    'SPORTS': '#ff7f00',
    'SHOPPING': '#cab2d6',
    'HOTEL': '#6a3d9a',
    'GREENHOUSE': '#ffff99',
    'UTILITY': '#b15928',
    'OTHER': '#000000'
}

var building_year_categories = [0, 1800, 1900, 1920, 1940, 1970, 1990, 2010];
var building_area_categories = [0, 50, 80, 100, 150, 200, 300, 600, 1000];

var num_building_year_categories = building_year_categories.length;
var num_building_area_categories = building_area_categories.length;

/*
    Generated with http://colorbrewer2.org/#type=sequential&scheme=PuBu&n=3
*/
var grades = {
    "1": ['#ece7f2'],
    "2": ['#ece7f2','#2b8cbe'],
    "3": ['#ece7f2','#a6bddb','#2b8cbe'],
    "4": ['#f1eef6','#bdc9e1','#74a9cf','#0570b0'],
    "5": ['#f1eef6','#bdc9e1','#74a9cf','#2b8cbe','#045a8d'],
    "6": ['#f1eef6','#d0d1e6','#a6bddb','#74a9cf','#2b8cbe','#045a8d'],
    "7": ['#f1eef6','#d0d1e6','#a6bddb','#74a9cf','#3690c0','#0570b0','#034e7b'],
    "8": ['#fff7fb','#ece7f2','#d0d1e6','#a6bddb','#74a9cf','#3690c0','#0570b0','#034e7b'],
    "9": ['#fff7fb','#ece7f2','#d0d1e6','#a6bddb','#74a9cf','#3690c0','#0570b0','#045a8d','#023858']
}

function get_range_color_index(value, range, range_length) {
    let i;
    for (i=0; i<range_length; i++) {
        if (value < range[i]) return i-1;
    }
    return i-1;
}

var color_grades;
function get_buildingType_colors(value) {
    return building_type_colors[value];
}

function get_buildingYear_colors(value) {
    // does it make sense to optimize this? grades[num_building_year_categories] doesn't change between calls
    return color_grades[get_range_color_index(value, building_year_categories, num_building_year_categories)];
}

function get_floorArea_colors(value) {
    // does it make sense to optimize this? grades[num_building_area_categories] doesn't change between calls
    return color_grades[get_range_color_index(value, building_area_categories, num_building_area_categories)];
}

var area_legend_ranges;
var num_area_range_colors;
function get_area_range_colors(value) {
    return grades[num_area_range_colors.toString()][get_range_color_index(value, area_legend_ranges, num_area_range_colors)];
}

var area_legend_array;
var num_area_array_colors;
function get_area_array_colors(value) {
    return color_grades[area_legend_array.indexOf(value)];
}

function get_area_default_color(value) {
    return "blue";
}

var building_legend_ranges;
var num_building_range_colors;
function get_building_range_colors(value) {
    return grades[num_building_range_colors.toString()][get_range_color_index(value, building_legend_ranges, num_building_range_colors)];
}

var building_legend_array;
var num_building_array_colors;
function get_building_array_colors(value) {
    return color_grades[building_legend_array.indexOf(value)];
}

function get_building_default_color(value) {
    return "blue";
}


stdKPIs = {
    "buildingYear": {
        "get_colors": get_buildingYear_colors,
        "color_grades": grades[num_building_year_categories],
        "create_legendClassesDiv": create_buildingYear_legendClassesDiv
    },
    "floorArea": {
        "get_colors": get_floorArea_colors,
        "color_grades": grades[num_building_area_categories],
        "create_legendClassesDiv": create_floorArea_legendClassesDiv
    },
    "buildingType": {
        "get_colors": get_buildingType_colors,
        "color_grades": building_type_colors,
        "create_legendClassesDiv": create_buildingType_legendClassesDiv
    }
}


// ------------------------------------------------------------------------------------------------------------
//  Functions to create the proper legends
// ------------------------------------------------------------------------------------------------------------
var buildingLegendClassesDiv;
var areaLegendClassesDiv;

function create_floorArea_legendClassesDiv() {
    let result = '';
    for (var i = 0; i < building_area_categories.length; i++) {
        result +=
            '<i style="background:' + get_floorArea_colors(building_area_categories[i] + 1) + '"></i> ' +
            building_area_categories[i] + (building_area_categories[i + 1] ? ' <b>&ndash;</b> ' + building_area_categories[i + 1] + '<br>' : '+');
    }
    return result;
}

function create_buildingYear_legendClassesDiv() {
    let result = '';
    for (var i = 0; i < building_year_categories.length; i++) {
        result +=
            '<i style="background:' + get_buildingYear_colors(building_year_categories[i] + 1) + '"></i> ' +
            building_year_categories[i] + ((i != building_year_categories.length-1)  ? ' <b>&ndash;</b> ' + building_year_categories[i + 1] + '<br>' : '+');
    }
    return result;
}

function create_buildingType_legendClassesDiv() {
    let result = '';
    for (key in building_type_colors) {
        color = building_type_colors[key];
        result += '<i style="background:' + color + '"></i> ' + key + '<br>';
    }
    return result;
}

function create_range_area_legendClassesDiv(kpi) {
    let result = '';
    for (var i = 0; i < area_legend_ranges.length; i++) {
        result +=
            '<i style="background:' + get_area_range_colors(area_legend_ranges[i]) + '"></i> ' +
            area_legend_ranges[i] + ((i != area_legend_ranges.length-1) ? ' <b>&ndash;</b> ' + area_legend_ranges[i + 1] + '<br>' : '+');
    }
    return result;
}

function create_array_area_legendClassesDiv(kpi) {
    let result = '';
    for (i=0; i<kpi.length; i++) {
        color = grades[kpi.length][i];
        result += '<i style="background:' + color + '"></i> ' + kpi[i] + '<br>';
    }
    return result;
}

function create_range_building_legendClassesDiv(kpi) {
    let result = '';
    for (var i = 0; i < building_legend_ranges.length; i++) {
        result +=
            '<i style="background:' + get_building_range_colors(building_legend_ranges[i]) + '"></i> ' +
            building_legend_ranges[i] + ((i != building_legend_ranges.length-1) ? ' <b>&ndash;</b> ' + building_legend_ranges[i + 1] + '<br>' : '+');
    }
    return result;
}

function create_array_building_legendClassesDiv(kpi) {
    let result = '';
    for (i=0; i<kpi.length; i++) {
        color = grades[kpi.length][i];
        result += '<i style="background:' + color + '"></i> ' + kpi[i] + '<br>';
    }
    return result;
}


// ------------------------------------------------------------------------------------------------------------
//
// ------------------------------------------------------------------------------------------------------------
var building_colors = {
    "building type": {
        parameter_name: "feature.properties.buildingType",
        colors: building_type_colors
    }
}

// ------------------------------------------------------------------------------------------------------------
//  Handling mouse over, mouse out events
// ------------------------------------------------------------------------------------------------------------
function highlightAreaOrBuilding(e) {
    let layer = e.target;

    layer.setStyle({
        weight: 3,
        color: 'white',
        dashArray: '',
        fillOpacity: 0.5
    });

    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        layer.bringToFront();
    }

    layer.openPopup();
}

function resetHighlightArea(e) {
    let layer = e.target;
    geojson_area_layer.resetStyle(layer);
    layer.closePopup();
}

function resetHighlightBuilding(e) {
    let layer = e.target;
    geojson_building_layer.resetStyle(layer);
    layer.closePopup();
}

//
function request_bag_info(e, area_id) {
    area_polygon = e.relatedTarget;
    latlngs = area_polygon.getLatLngs();
    socket.emit('get_bag_contours', {id: area_polygon.id, polygon: latlngs});
}

// ------------------------------------------------------------------------------------------------------------
//  Add geojson data contained in area_data to the area map layer
// ------------------------------------------------------------------------------------------------------------
function set_area_handlers(area) {
    let area_id = area.id
    area.bindContextMenu({
        contextmenu: true,
        contextmenuWidth: 140,
        contextmenuItems: [],
        contextmenuInheritItems: false
    });

    area.options.contextmenuItems.push({
        icon: '{{dir_settings.resource_prefix}}icons/BuildingContents.png',
        text: 'request BAG building',
        callback: function(e) { request_bag_info(e, area_id); }
    });
    area.options.contextmenuItems.push('-');

    area.on('dragend', function(e) {
        var area = e.target;
        // var pos = area.getLatLng();
        // socket.emit('update-coord', {id: area.id, lat: pos.lat, lng: pos.lng, asspot: 'building'});
    });

    // area.on('remove', function(e) {
    //     $(".ui-tooltip-content").parents('div').remove();
    // });

    area.on('click', function(e) {
        var area = e.target;
        if (deleting_objects == false && editing_objects == false) {        // do not execute when removing/editing objects
            var area = e.target;
            var id = area.id;

            socket.emit('command', {cmd: 'get_area_info', id: id});
        }
    });
}

function add_area_layer(area_data) {
    geojson_area_layer = L.geoJson(area_data, {
        style: style_area,
        onEachFeature: function(feature, layer) {
            if (Object.keys(feature.properties.KPIs).length != 0) {
                feature.properties.get_area_color = get_area_range_colors;
            }
            if (feature.properties && feature.properties.id) {
                layer.id = feature.properties.id;
// if we uncomment the following lines, the area context menu doesn't work
//                let text = "ID: " + feature.properties.id;
//                if (feature.properties.name) {
//                    text = feature.properties.name + " (" + text + ")";
//                }
//
//                for (let key in feature.properties.KPIs) {
//                    text += "<br>" + key + ": " + feature.properties.KPIs[key];
//                }
//
//                layer.bindPopup(text, {closeButton: false, offset: L.point(0, -20)});
                layer.on('mouseover', highlightAreaOrBuilding);
                layer.on('mouseout', resetHighlightArea);
                set_area_handlers(layer);
            }
        }
    }).addTo(get_layers(active_layer_id, 'area_layer'));
}
// ------------------------------------------------------------------------------------------------------------
//  Add geojson data contained in building_data to the building map layer
// ------------------------------------------------------------------------------------------------------------

function add_building_layer(building_data) {
    geojson_building_layer = L.geoJson(building_data, {
        style: style_building,
        onEachFeature: function(feature, layer) {
            if (feature.properties) {
                let text = "";
                for (let key in feature.properties.KPIs) {
                    text += key + ": " + feature.properties.KPIs[key] + "<br>";
                }

                layer.bindPopup(text, {closeButton: false, offset: L.point(0, -20)});
                layer.on('mouseover', highlightAreaOrBuilding);
                layer.on('mouseout', resetHighlightBuilding);
            }
        }
    }).addTo(get_layers(active_layer_id, 'bld_layer'));
}


// ------------------------------------------------------------------------------------------------------------
//  Function that deals with selecting another parameter in the Legend
// ------------------------------------------------------------------------------------------------------------
function create_building_legendClassesDiv(legendChoice) {
    let kpi = building_KPIs[legendChoice];
    if (legendChoice in stdKPIs) {
        color_grades = stdKPIs[legendChoice]["color_grades"];
        get_building_color = stdKPIs[legendChoice]["get_colors"];
        return stdKPIs[legendChoice]["create_legendClassesDiv"]();
    } else {
        return create_building_array_or_range_legendClassesDiv(kpi);
    }
}

function selectBuildingKPI(selectObject) {
    let legendChoice = selectObject.value;
    buildingLegendClassesDiv.innerHTML = create_building_legendClassesDiv(legendChoice);

    geojson_building_layer.eachLayer(function (layer) {
        layer.setStyle({
            fillColor: get_building_color(layer.feature.properties.KPIs[legendChoice]),
            color: get_building_color(layer.feature.properties.KPIs[legendChoice])
        });
    });
}

function create_building_array_or_range_legendClassesDiv(kpi) {
    if (Array.isArray(kpi)) {
        if (kpi.length > 9) {
            alert("More than 9 labels ("+kpi.length+") in KPI "+buildingLegendChoice);
            rb = new Rainbow();
            rb.setNumberRange(0, kpi.length-1);
            color_grades = [];
            for (i=0; i<kpi.length; i++) {
                color_grades.push('#' + rb.colourAt(i));
            }
        } else {
            color_grades = grades[kpi.length]
        }
        building_legend_array = building_KPIs[buildingLegendChoice];
        num_building_array_colors = kpi.length;
        get_building_color = get_building_array_colors;
        return create_array_building_legendClassesDiv(kpi);
    } else {
        // kpi is number with min and max
        var min = kpi["min"];
        var max = kpi["max"];
        building_legend_ranges = create_ranges(min, max);
        num_building_range_colors = building_legend_ranges.length;
        get_building_color = get_building_range_colors;
        return create_range_building_legendClassesDiv(kpi);
    }
}

function selectAreaKPI(selectObject) {
    areaLegendChoice = selectObject.value;
    kpi = area_KPIs[areaLegendChoice];

    areaLegendClassesDiv.innerHTML = create_area_array_or_range_legendClassesDiv(kpi);

    geojson_area_layer.eachLayer(function (layer) {
        layer.setStyle({
            fillColor: get_area_color(layer.feature.properties.KPIs[areaLegendChoice]),
            color: get_area_color(layer.feature.properties.KPIs[areaLegendChoice])
        });
    });
}



// ------------------------------------------------------------------------------------------------------------
//  Generate the complete Legend DIV
// ------------------------------------------------------------------------------------------------------------
function createBuildingLegendDiv() {
    var legendDiv = L.DomUtil.create('div', 'info legend');
    var legendTitleDiv = L.DomUtil.create('div', 'legend_title', legendDiv);
    legendTitleDiv.innerHTML += 'Building Legend';

    var selectorDiv = L.DomUtil.create('div', 'legend_select', legendDiv);
    var selectText = '<select style="z-index:1000;" onchange="selectBuildingKPI(this);">';
    for (bkpi in building_KPIs) {
//        if (bkpi == 'buildingYear') {
//            selectText += '<option value="'+bkpi+'" selected>'+bkpi+'</option>';
//        } else {
            selectText += '<option value="'+bkpi+'">'+bkpi+'</option>';
//        }
    }
    selectText += '</select>';
    selectorDiv.innerHTML = selectText;

    buildingLegendClassesDiv = L.DomUtil.create('div', 'info legend', legendDiv);

    first_kpi_name = Object.keys(building_KPIs)[0];
    buildingLegendClassesDiv.innerHTML = create_building_legendClassesDiv(first_kpi_name);
    return legendDiv;
};

//function createBuildingLegendDiv() {
//    var legendDiv = L.DomUtil.create('div', 'info legend');
//    var legendTitleDiv = L.DomUtil.create('div', 'legend_title', legendDiv);
//    legendTitleDiv.innerHTML += 'Building Legend';
//
//    var selectorDiv = L.DomUtil.create('div', 'legend_select', legendDiv);
//    var selectText = '<select style="z-index:1000;" onchange="selectBuildingKPI(this);">';
//    for (bkpi in building_KPIs) {
//        selectText += '<option value="'+bkpi+'">'+bkpi+'</option>';
//    }
//    selectText += '</select>';
//    selectorDiv.innerHTML = selectText;
//
//    buildingLegendClassesDiv = L.DomUtil.create('div', 'info legend', legendDiv);
//
//    first_kpi_name = Object.keys(building_KPIs)[0];
//    buildingLegendClassesDiv.innerHTML = create_area_array_or_range_legendClassesDiv(building_KPIs[first_kpi_name]);
//    return legendDiv;
//};



function createAreaLegendDiv() {
    var legendDiv = L.DomUtil.create('div', 'info legend');
    var legendTitleDiv = L.DomUtil.create('div', 'legend_title', legendDiv);
    legendTitleDiv.innerHTML += 'Area Legend';

    var selectorDiv = L.DomUtil.create('div', 'legend_select', legendDiv);
    var selectText = '<select style="z-index:1000;" onchange="selectAreaKPI(this);">';
    for (akpi in area_KPIs) {
        selectText += '<option value="'+akpi+'">'+akpi+'</option>';
    }
    selectText += '</select>';
    selectorDiv.innerHTML = selectText;

    areaLegendClassesDiv = L.DomUtil.create('div', 'info legend', legendDiv);

    first_kpi_name = Object.keys(area_KPIs)[0];
    areaLegendClassesDiv.innerHTML = create_area_array_or_range_legendClassesDiv(area_KPIs[first_kpi_name]);
    return legendDiv;
};

function removeBuildingLegend() {
    if (buildingLegend) {
        map.removeControl(buildingLegend);
    }
}
function removeAreaLegend() {
    if (areaLegend) {
        map.removeControl(areaLegend);
    }
}

function add_area_geojson_layer_with_legend(geojson_area_data) {
    area_KPIs = {};
    preprocess_layer_data("area", geojson_area_data, area_KPIs);

    removeAreaLegend();
    if (!jQuery.isEmptyObject(area_KPIs)) {
        areaLegend = L.control({position: 'bottomright'});
        areaLegend.onAdd = function (map) {
            return createAreaLegendDiv();
        };
        areaLegend.addTo(map);
    }

    add_area_layer(geojson_area_data);
}

function add_building_geojson_layer_with_legend(geojson_building_data) {
    building_KPIs = {};
    preprocess_layer_data("building", geojson_building_data, building_KPIs);

//    buildingLegendChoice = "buildingYear";
//    color_grades = grades[num_building_year_categories];
//    get_building_color = get_buildingYear_colors;

    removeBuildingLegend();
    if (!jQuery.isEmptyObject(building_KPIs)) {
        buildingLegend = L.control({position: 'bottomright'});
        buildingLegend.onAdd = function (map) {
            return createBuildingLegendDiv();
        };
        buildingLegend.addTo(map);
    }

    add_building_layer(geojson_building_data);
}

function add_geojson_listener(socket, map) {
    socket.on('geojson', function(message) {
        let layer = message['layer'];
        hide_loader();

        if (layer == 'area_layer') {
            geojson_area_data = message['geojson'];     // store for redraw based on other KPI
            add_area_geojson_layer_with_legend(geojson_area_data);
        }

        if (layer == 'bld_layer') {
            geojson_building_data = message['geojson']; // store for redraw based on other property
            add_building_geojson_layer_with_legend(geojson_building_data);
        }
    });
}

// ------------------------------------------------------------------------------------------------------------
//   Initial styling of buildings and areas   --> must be changed too
// ------------------------------------------------------------------------------------------------------------
function get_area_color_old(d) {
    return d > 1000000 ? '#800026' :
           d > 500000  ? '#BD0026' :
           d > 200000  ? '#E31A1C' :
           d > 100000  ? '#FC4E2A' :
           d > 50000   ? '#FD8D3C' :
           d > 20000   ? '#FEB24C' :
           d > 10000   ? '#FED976' :
                      '#FFEDA0';
}

function style_area(feature) {
    if (Object.keys(feature.properties.KPIs).length != 0) {
        //if (feature.properties.get_area_color) {
        //    get_area_color = feature.properties.get_area_color;
        //}
        var color = get_area_color(feature.properties.KPIs[areaLegendChoice]);
        return {
            fillColor: color,
            weight: 2,
            opacity: 1,
            color: color,
            dashArray: '',
            fillOpacity: 0.7
        };
    } else {
        return {
            fillColor: "blue",
            weight: 1,
            opacity: 1,
            color: "blue",
            dashArray: '',
            fillOpacity: 0.3
        };
    }
}

function style_building(feature) {
    var b_color = get_building_color(feature.properties.KPIs[buildingLegendChoice]);
    return {
        fillColor: b_color,
        weight: 2,
        opacity: 1,
        color: b_color,
        dashArray: '',
        fillOpacity: 0.7
    };
}
