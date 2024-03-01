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
pie_chart_color_list = ['#a6cee3','#1f78b4','#b2df8a','#33a02c','#fb9a99','#e31a1c','#fdbf6f','#ff7f00','#cab2d6',
    '#6a3d9a','#ffff99','#b15928','#000000','#808080'];

function isNumeric(val) { return !isNaN(val); }


/**
 * Flattens a list of areas such that KPIs can be properly processed
 * @param layer_data list of layers. Items in this list can be objects with grouped layers
 * @returns {*[]} flattened list of areas
 */
function flatten_area_list(layer_data) {
    let flat_layer_data = [];

    for (const l_index in layer_data) {
        let layer = layer_data[l_index];
        if (layer.hasOwnProperty('type') && layer['type']==='group') {
            // current layer is a group of layers
            flat_layer_data.push(...layer['area_list']);
        } else {
            // current layer is a single layer
            flat_layer_data.push(layer);
        }
    }

    return flat_layer_data;
}


/**
 * Preprocess layer data of an area or building. Creates KPI's and sets colors.
 * @param {*} layer_type Either area or building.
 * @param {*} layer_data 
 * @param {*} kpi_list An object to which the KPI's from the layer will be added.
 */
function preprocess_layer_data(layer_type, layer_data, kpi_list) {
    if (layer_type === "area") {
        get_area_color = null;
        areaLegendChoice = null;
    }
    if (layer_type === "building") {
        get_building_color = null;
        buildingLegendChoice = null;
    }
    let flattened_layer_data = flatten_area_list(layer_data);
    for (const l_index in flattened_layer_data) {
        let layer = flattened_layer_data[l_index];
        let KPIs = layer.properties.KPIs;
        let dist_KPIs = layer.properties.dist_KPIs;
        for (const kpi in KPIs) {
            const kpi_obj = KPIs[kpi];
            let KPI_value;
            if (kpi_obj.hasOwnProperty('value')) {
                KPI_value = KPIs[kpi]['value'];
            } else {
                // Legacy support for older ESDLs.
                KPI_value = kpi_obj;
            }
            if (KPI_value !== "") {
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

        // Handle Distributed KPIs here for now.
        for (const kpi in dist_KPIs) {
            const KPI_value = dist_KPIs[kpi]["value"];

            if (KPI_value != null) {
                if (!(kpi in kpi_list)) {
                    if (layer_type === "area" && !areaLegendChoice) { areaLegendChoice = kpi; }
                    if (layer_type === "building" && !buildingLegendChoice) { buildingLegendChoice = kpi; }
                    if (layer_type === "area" && !get_area_color) { get_area_color = get_area_range_colors; }
                    if (layer_type === "building" && !get_building_color) { get_building_color = get_building_range_colors; }
                    //value = parseFloat(KPI_value);
                    kpi_list[kpi] = {"type": "distributionKPI", "names": []};
                    for (let i=0; i<KPI_value.length; i++) {
                        let val = KPI_value[i];
                        kpi_list[kpi]["names"].push(val["name"]);
                    }

                    //kpi_list[kpi] = { "min": value, "max": value };
                } else {
                    // if kpi information is already in kpi_list, check if new area contains other values
                    // such that legend is extended with the new categories
                    for (let i=0; i<KPI_value.length; i++) {
                        if (!(kpi_list[kpi]["names"].includes(KPI_value[i]["name"]))) {
                            kpi_list[kpi]["names"].push(KPI_value[i]["name"]);
                        }
                    }
                }
            }
        }
    }
    if (layer_type === "area") {
        if (!get_area_color) { get_area_color = get_area_default_color; }
    }
    if (layer_type === "building") {
        if (!get_building_color ) { get_building_color = get_building_default_color; }
    }
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


var stdKPIs = {
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

function create_distribution_legendClassesDiv(kpi) {
    let result = '';
    for (var i = 0; i < kpi["names"].length; i++) {
        result +=
            '<i style="background:' + pie_chart_color_list[i] + '"></i> ' +
            kpi["names"][i] + ' <br />';
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
function saveStyle(layer) {
    layer.oldStyle = {
        weight: layer.options.weight,
        color: layer.options.color,
        dashArray: layer.options.dashArray,
        fillOpacity: layer.options.fillOpacity
    }
}

function restoreStyle(layer) {
    if (layer.oldStyle) {
        layer.setStyle({
            weight: layer.oldStyle.weight,
            color: layer.oldStyle.color,
            dashArray: layer.oldStyle.dashArray,
            fillOpacity: layer.oldStyle.fillOpacity
        });
        layer.oldStyle = null;
    }
}

function highlightAreaOrBuilding(e) {
    let layer = e.target;

    saveStyle(layer);
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
    restoreStyle(layer);
//    geojson_area_layer.resetStyle(layer);         // Interferes with the contextmenu
    layer.closePopup();
}

function resetHighlightBuilding(e) {
    let layer = e.target;
    // geojson_building_layer.resetStyle(layer);    // Interferes with the contextmenu
    restoreStyle(layer);
    layer.closePopup();
}

function delete_area(e, area_id) {
    // Currently the area id can have (x of y) appended to it (in case of a multipolygon)
    let a_id = area_id.replace(/ \(\d+ of \d+\)/, '');
    socket.emit('command', {cmd: 'remove_area', id: a_id});
}

function request_bag_info(area) {
    let latlngs = area.getLatLngs();
    show_loader();
    socket.emit('get_bag_contours', {id: area.id, polygon: latlngs});
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
       icon: resource_uri + '/icons/Delete.png',
       text: 'delete area',
       callback: function(e) { delete_area(e, area_id); }
   });

    if (services_enabled['bag_service']) {
        area.options.contextmenuItems.push({
            icon: resource_uri + '/icons/BuildingContents.png',
            text: 'request BAG building',
            callback: function(e) { request_bag_info(area); }
        });
        area.options.contextmenuItems.push('-');
    }

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

    // let extensions know they can update this layer.
    // e.g. add a context menu item
    for (let i=0; i<extensions.length; i++) {
        updatefun = extensions[i];
        updatefun({type: 'add_contextmenu', layer: area, layer_type: 'area'});
    }
}

function format_KPI_value(value) {
    if (typeof(value) == "number") {
        value_str = value.toString();
        index_of_decimal_seperator = value_str.indexOf('.');
        if (index_of_decimal_seperator >= 0) {
            if (index_of_decimal_seperator < value_str.length - 3) {
                value = Math.round((1000*value)+Number.EPSILON) / 1000;
                value_str = value.toString();
            }
            return value_str;
        } else
            return value_str;
    } else
        return value;
}

function format_KPI_unit(unit) {
    if (unit.indexOf('Mg') >= 0) {
        return unit.replace('Mg', 'ton');
    } else
        return unit;
}

function create_area_pie_chart(ar, size) {
    if (ar.properties.dist_KPIs && Object.keys(ar.properties.dist_KPIs).length != 0) {
        let keys = Object.keys(ar.properties.dist_KPIs);

        // create pieChartMwrkers for all DistributionKPIs
        for (let j=0; j<keys.length; j++) {
            let key = keys[j];

            // Pie chart options.
            var pieChartOptions = {
                radius: size / 4,
                fillOpacity: 1.0,
                opacity: 1.0,
                data: {},
                chartOptions: {},
                weight: 1,
            };

            for (let k=0; k<ar.properties.dist_KPIs[key].value.length; k++) {
                let dist_kpi = ar.properties.dist_KPIs[key].value[k];

                pieChartOptions.data[dist_kpi["name"]] = dist_kpi["value"];
                pieChartOptions.chartOptions[dist_kpi["name"]] = {
                    fillColor: pie_chart_color_list[k],
                    minValue: 0,
                    maxValue: 10,
                    maxHeight: 10,
                    displayText: function (value) {
                        return 1;
                    }
                }
            }
            ar.properties.dist_KPIs[key].pieChartMarker = new L.PieChartMarker(
                new L.LatLng(ar.properties.dist_KPIs[key].location[0], ar.properties.dist_KPIs[key].location[1]),
                pieChartOptions
            );
            ar.properties.dist_KPIs[key].pieChartMarkerVisible = false;
        }
    }
}

function calculate_area_size(layer) {
    // calculate the size of the area, see https://oliverroick.net/writing/2015/leaflet-deflate.html
    let bounds = layer.getBounds();
    let zoom = map.getZoom();
    let ne_px = map.project(bounds.getNorthEast(), zoom);
    let sw_px = map.project(bounds.getSouthWest(), zoom);
    let width = ne_px.x - sw_px.x;
    let height = sw_px.y - ne_px.y;
    let size = Math.min(width, height);
    return size
}

function resize_area_pi_charts() {
    let area_layers = get_layers(active_layer_id, 'area_layer');
    area_layers.eachLayer(function(featuregroup_instance) {
        if (featuregroup_instance instanceof L.FeatureGroup) {
            featuregroup_instance.eachLayer(function(layer) {
                // layer should now contain leaflet layers for each area
                if ("dist_KPIs" in layer.feature.properties) {
                    if (areaLegendChoice in layer.feature.properties.dist_KPIs) {
                        // if currently selected KPI is DistributionKPI, remove it from map
                        let kpi = layer.feature.properties.dist_KPIs[areaLegendChoice];
                        if (kpi.pieChartMarkerVisible) {   // don't add if it's already visible
                            kpi.pieChartMarker.removeFrom(get_layers(active_layer_id, 'kpi_layer'));
                            kpi.pieChartMarkerVisible = false;
                        }
                    }

                    let area_size = calculate_area_size(layer);
                    create_area_pie_chart(layer.feature, area_size);

                    if (areaLegendChoice in layer.feature.properties.dist_KPIs) {
                        let kpi = layer.feature.properties.dist_KPIs[areaLegendChoice];

                        if (!kpi.pieChartMarkerVisible) {   // don't add if it's already visible
                            kpi.pieChartMarker.addTo(get_layers(active_layer_id, 'kpi_layer'));
                            kpi.pieChartMarkerVisible = true;
                        }
                    }
                }
            });

        }
    });
}

function add_geojson_area_layer(area_data, group_name, map_esdl_layer) {
    let geo_json_layer = L.geoJson(area_data, {
        style: style_area,
        group_name: group_name,
        onEachFeature: function(feature, layer) {
            if (feature.properties.dist_KPIs && Object.keys(feature.properties.dist_KPIs).length != 0) {
                feature.properties.get_area_color = get_area_range_colors;

                let area_size = calculate_area_size(layer);
                create_area_pie_chart(feature, area_size);

                // Only show first DistributionKPI if it's also the first KPI in the legend list.
                let first_kpi_key = Object.keys(area_KPIs)[0];
                if ('type' in area_KPIs[first_kpi_key] && area_KPIs[first_kpi_key].type == "distributionKPI") {
                    feature.properties.dist_KPIs[first_kpi_key].pieChartMarker.addTo(get_layers(active_layer_id, 'kpi_layer'));
                    feature.properties.dist_KPIs[first_kpi_key].pieChartMarker.bringToFront();
                    feature.properties.dist_KPIs[first_kpi_key].pieChartMarkerVisible = true;
                }
            }
            if (feature.properties.KPIs && Object.keys(feature.properties.KPIs).length != 0) {
                feature.properties.get_area_color = get_area_range_colors;
            }
            if (feature.properties && feature.properties.id) {
                layer.id = feature.properties.id;

                let text = "ID: " + feature.properties.id;
                if (feature.properties.name) {
                    text = feature.properties.name + " (" + text + ")";
                }

                if (Object.keys(feature.properties.KPIs).length != 0) {
                    text = "<b>"+ text +"</b>";
                    text += "<br><br><table class=\"kpi_table\">";
                    text += "<thead><tr><th>KPI</th><th>Value</th><th>Unit</th></tr></thead><tbody>"
                    for (let key in feature.properties.KPIs) {
                        text += "<tr><td>" + key + "</td><td align=\"right\">" + format_KPI_value(feature.properties.KPIs[key]['value']) + "</td>";
                        if (!(feature.properties.KPIs[key]['unit'] === "")) {
                            text += "<td>" + format_KPI_unit(feature.properties.KPIs[key]['unit']) + "</td></tr>";
                        } else {
                            text += "<td>&nbsp;</td></tr>";
                        }
                    }
                    text += "</tbody></table>"
                }

                let popup = L.popup();
                popup.setContent(text);
                layer.bindPopup(popup);

                layer.on('mouseover', function (e) {
                    var popup = e.target.getPopup();
                    var this_map = e.sourceTarget._map;     // can be area map and building map
                    popup.setLatLng(e.latlng).openOn(this_map);

                    highlightAreaOrBuilding(e);
                });

                layer.on('mouseout', function(e) {
                    e.target.closePopup();

                    resetHighlightArea(e);
                });

                layer.on('mousemove', function (e) {
                    e.target.closePopup();
                    var this_map = e.sourceTarget._map;     // can be area map and building map
                    var popup = e.target.getPopup();
                    popup.setLatLng(e.latlng).openOn(this_map);
                });

                set_area_handlers(layer);
            }
        }
    }).addTo(map_esdl_layer);

    return geo_json_layer;
}


function add_area_layer(area_data) {
    let other_layers = [];
    for (const l_index in area_data) {
        let layer = area_data[l_index];
        if (layer.hasOwnProperty('type') && layer['type'] === 'group') {
            let geojson = add_geojson_area_layer(
                layer['area_list'],
                layer['name'],
                get_layers(active_layer_id, 'area_layer')
            );
        } else {
            other_layers.push(layer);
        }
    }

    geojson_area_layer = add_geojson_area_layer(
        other_layers,
        null,
        get_layers(active_layer_id, 'area_layer')
    );
}

// ------------------------------------------------------------------------------------------------------------
//  Add geojson data contained in building_data to the building map layer
// ------------------------------------------------------------------------------------------------------------
function set_building_contextmenu(layer, id) {
    layer.bindContextMenu({
        contextmenu: true,
        contextmenuWidth: 140,
        contextmenuItems: [],
        contextmenuInheritItems: false
    });

    layer.options.contextmenuItems.push({
        text: 'Building ESDL contents',
        icon: resource_uri + 'icons/BuildingContents.png',
        callback: function(e) { edit_building_contents(e, id); }
    });
    layer.options.contextmenuItems.push('-');
    layer.options.contextmenuItems.push({
        text: 'Delete',
        icon: resource_uri + 'icons/Delete.png',
        callback: function(e) { remove_building(layer); }
    });
    layer.options.contextmenuItems.push({
        text: 'Edit building properties',
        icon: resource_uri + 'icons/Edit.png',
        callback: function(e) { esdl_browser.open_browser_with_event(e, id); }
    });
}

/**
 * Add layer of type building to the map.
 * 
 * @param {*} building_data 
 */
function add_building_layer(building_data) {
    geojson_building_layer = L.geoJson(building_data, {
        style: style_building,
        onEachFeature: function(feature, layer) {
            if (feature.properties) {
                let text = "<table>";
                // Render the KPI's for a popup. These were set in the preprocess_layer_data function.
                for (let key in feature.properties.KPIs) {
                    const kpi = feature.properties.KPIs[key]
                    if (typeof kpi === "number") {
                        if (Math.floor(kpi) === kpi)
                            kpi_string = feature.properties.KPIs[key].toFixed(0);
                        else
                            kpi_string = feature.properties.KPIs[key].toFixed(2);
                    } else {
                        kpi_string = feature.properties.KPIs[key];
                    }
                    text += "<tr><td>" + key + "</td><td style=\"float:right\">" + kpi_string + "</td></tr>";
                }
                text += "</table>";

                // Bind the KPI popup on hover of a building.
                layer.bindPopup(text, {maxWidth: "auto", closeButton: false, autoPan: false, offset: L.point(0, -20)});
                layer.on('mouseover', highlightAreaOrBuilding);
                layer.on('mouseout', resetHighlightBuilding);
            }
            if (feature.properties && feature.properties.id) {
                window.PubSubManager.broadcast('ADD_FEATURE_TO_LAYER', { id: feature.properties.id, feature: feature, layer: layer });
                set_building_contextmenu(layer, feature.properties.id);
            }
        }
    }).addTo(get_layers(active_layer_id, 'bld_layer'));
}

// Ewoud's attempts to get context menus working with GeoJSON layers:
// https://jsfiddle.net/ykjh6w4r/ and http://jsfiddle.net/jdembdr/y97k2n2z/

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
    buildingLegendChoice = legendChoice;
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

function create_area_array_or_range_legendClassesDiv(kpi) {
    if (Array.isArray(kpi)) {
        if (kpi.length > 9) {
            alert("More than 9 labels ("+kpi.length+") in KPI "+areaLegendChoice);
            rb = new Rainbow();
            rb.setNumberRange(0, kpi.length-1);
            color_grades = [];
            for (i=0; i<kpi.length; i++) {
                color_grades.push('#' + rb.colourAt(i));
            }
        } else {
            color_grades = grades[kpi.length]
        }
        area_legend_array = area_KPIs[areaLegendChoice];
        num_area_array_colors = kpi.length;
        get_area_color = get_area_array_colors;
        return create_array_area_legendClassesDiv(kpi);
    } else {
        if(kpi["type"] === "distributionKPI") {
            return create_distribution_legendClassesDiv(kpi);
        } else {
            // kpi is number with min and max
            var min = kpi["min"];
            var max = kpi["max"];
            area_legend_ranges = create_ranges(min, max);
            num_area_range_colors = area_legend_ranges.length;
            get_area_color = get_area_range_colors;
        }
        return create_range_area_legendClassesDiv();
    }
}

function selectAreaKPI(selectObject) {
    areaLegendChoice = selectObject.value;
    kpi = area_KPIs[areaLegendChoice];

    areaLegendClassesDiv.innerHTML = create_area_array_or_range_legendClassesDiv(kpi);

    let area_layers = get_layers(active_layer_id, 'area_layer');
    area_layers.eachLayer(function(featuregroup_instance) {
        if (featuregroup_instance instanceof L.FeatureGroup) {
            featuregroup_instance.eachLayer(function (layer) {
                if (Object.keys(layer.feature.properties.KPIs).length > 0) {
                    if (areaLegendChoice in layer.feature.properties.KPIs) {
                        layer.setStyle({
                            fillColor: get_area_color(layer.feature.properties.KPIs[areaLegendChoice].value),
                            color: get_area_color(layer.feature.properties.KPIs[areaLegendChoice].value)
                        });
                    } else {
                        layer.setStyle({
                            fillColor: "blue",
                            weight: 1,
                            opacity: 1,
                            color: "blue",
                            dashArray: '',
                            fillOpacity: 0.3
                        });
                    }
                }

                if (Object.keys(layer.feature.properties.dist_KPIs).length > 0) {
                    if (areaLegendChoice in layer.feature.properties.dist_KPIs) {
                        // A DistributionKPI was selected
                        for (let key in layer.feature.properties.dist_KPIs) {
                            let kpi = layer.feature.properties.dist_KPIs[key];
                            if (areaLegendChoice == key) {
                                if (!kpi.pieChartMarkerVisible) {   // don't add if it's already visible
                                    kpi.pieChartMarker.addTo(get_layers(active_layer_id, 'kpi_layer'));
                                    kpi.pieChartMarkerVisible = true;
                                }
                            } else {
                                // remove all other distributionKPIs if applicable
                                if (kpi.pieChartMarkerVisible) {
                                    kpi.pieChartMarker.removeFrom(get_layers(active_layer_id, 'kpi_layer'));
                                    kpi.pieChartMarkerVisible = false;
                                }
                            }
                        }
                    } else {
                        // A non DistributionKPI was selected, hide pieCharts if the previous KPI was a DistributionKPI
                        for (let key in layer.feature.properties.dist_KPIs) {
                            let kpi = layer.feature.properties.dist_KPIs[key];
                            if (kpi.pieChartMarkerVisible) {
                                kpi.pieChartMarker.removeFrom(get_layers(active_layer_id, 'kpi_layer'));
                                kpi.pieChartMarkerVisible = false;
                            }
                        }
                    }
                }
            });
        }
    });
}

// ------------------------------------------------------------------------------------------------------------
//  Generate the complete Legend DIV
// ------------------------------------------------------------------------------------------------------------
function createBuildingLegendDiv() {
    var legendDiv = L.DomUtil.create('div', 'info legend');
    legendDiv.oncontextmenu = L.DomEvent.stopPropagation;
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
}

function createAreaLegendDiv() {
    var legendDiv = L.DomUtil.create('div', 'info legend');
    legendDiv.oncontextmenu = L.DomEvent.stopPropagation;
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
}

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

/**
 * Add all buildings to the map with the KPI legend.
 * 
 * @param {*} geojson_building_data 
 */
function add_building_geojson_layer_with_legend(geojson_building_data) {
    //console.log(geojson_building_data);
    building_KPIs = {};
    preprocess_layer_data("building", geojson_building_data, building_KPIs);

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

function add_potential_geojson_layer(geojson_pontential_data) {
    geojson_potential_layer = L.geoJson(geojson_pontential_data, {
        style: {
            fillColor: 'grey',
            weight: 2,
            opacity: 1,
            color: 'grey',
            dashArray: '',
            fillOpacity: 0.7
        },
        onEachFeature: function(feature, layer) {
            if (feature.properties) {
                if (feature.properties.name) {
                    let popup = L.popup();
                    popup.setContent(feature.properties.name);
                    layer.bindPopup(popup);

                    layer.on('mouseover', function (e) {
                        var popup = e.target.getPopup();
                        var this_map = e.sourceTarget._map;     // can be area map and building map
                        popup.setLatLng(e.latlng).openOn(this_map);
                    });

                    layer.on('mouseout', function(e) {
                        e.target.closePopup();
                    });

                    layer.on('mousemove', function (e) {
                        e.target.closePopup();
                        var this_map = e.sourceTarget._map;     // can be area map and building map
                        var popup = e.target.getPopup();
                        popup.setLatLng(e.latlng).openOn(this_map);
                    });
                    // bindPopup doesn't work with contextmenu
                    // layer.bindPopup(feature.properties.name, {maxWidth: "auto", closeButton: false, offset: L.point(0, -20)});
                }
            }
            // TODO: Implement contextmenu for potentials
            // if (feature.properties && feature.properties.id) {
            //     set_potential_contextmenu(layer, feature.properties.id);
            // }
        }
    }).addTo(get_layers(active_layer_id, 'pot_layer'));
}

function add_geojson_listener(socket, map) {
    socket.on('geojson', function(message) {
        let layer = message['layer'];
        hide_loader();

        if (layer == 'area_layer') {
            geojson_area_data = message['geojson'];     // store for redraw based on other KPI
            add_area_geojson_layer_with_legend(geojson_area_data);
        }

        // add_building_geojson_layer_with_legend is now called from the 'add_building_objects' socketIO handler
        // This code was commented out with the above command, but is required for the BAG service
        if (layer == 'bld_layer') {
            geojson_building_data = message['geojson']; // store for redraw based on other property
            add_building_geojson_layer_with_legend(geojson_building_data);
        }

        if (layer == 'pot_layer') {
            add_potential_geojson_layer(message['geojson']);
        }

        // recreate top right layer control box, as areas in ESDL can influence area layer control (for grouped areas)
        add_layer_control();
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
        let color = '#ffffff';
        if (areaLegendChoice in feature.properties.KPIs) {
            color = get_area_color(feature.properties.KPIs[areaLegendChoice].value);
        }
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
    let b_color = '#ffffff';
    if (buildingLegendChoice in feature.properties.KPIs) {
        b_color = get_building_color(feature.properties.KPIs[buildingLegendChoice]);
    }
    return {
        fillColor: b_color,
        weight: 2,
        opacity: 1,
        color: b_color,
        dashArray: '',
        fillOpacity: 0.7
    };
}
