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
//  Operations on (leaflet) shapes
// ------------------------------------------------------------------------------------------------------------
function calculate_length(layer) {
    var previousPoint;
    var polyline_length = 0;

    // http://leafletjs.com/reference.html#polyline-getlatlngs
    layer.getLatLngs().forEach(function (latLng) {
         // http://leafletjs.com/reference.html#latlng-distanceto
        if (previousPoint) polyline_length += previousPoint.distanceTo(latLng);
        previousPoint = latLng;
    });

    return +(polyline_length.toFixed(1));
}

function calculate_area(layer) {
    return L.GeometryUtil.geodesicArea(layer.getLatLngs()[0]);
}

// Calculates the centeriod of a polygon
function calculate_array_polygon_center(pts) {
    var first = pts[0], last = pts[pts.length-1];
    if (first[0] != last[0] || first[1] != last[1]) pts.push(first);
    var twicearea=0,
        x=0, y=0,
        nPts = pts.length,
        p1, p2, f;
    for ( var i=0, j=nPts-1 ; i<nPts ; j=i++ ) {
        p1 = pts[i]; p2 = pts[j];
        f = (p1[1] - first[1]) * (p2[0] - first[0]) - (p2[1] - first[1]) * (p1[0] - first[0]);
        twicearea += f;
        x += (p1[0] + p2[0] - 2 * first[0]) * f;
        y += (p1[1] + p2[1] - 2 * first[1]) * f;
    }
    f = twicearea * 3;
    return [x/f + first[0], y/f + first[1]];
}

// calculates the centeriod of a polygon
function calculate_leaflet_polygon_center(pts) {
    var first = pts[0], last = pts[pts.length-1];
    if (first.lat != last.lat || first.lng != last.lng) pts.push(first);
    var twicearea=0,
    x=0, y=0,
    nPts = pts.length,
    p1, p2, f;
    for ( var i=0, j=nPts-1 ; i<nPts ; j=i++ ) {
        p1 = pts[i]; p2 = pts[j];
        f = (p1.lng - first.lng) * (p2.lat - first.lat) - (p2.lng - first.lng) * (p1.lat - first.lat);
        twicearea += f;
        x += (p1.lat + p2.lat - 2 * first.lat) * f;
        y += (p1.lng + p2.lng - 2 * first.lng) * f;
    }
    f = twicearea * 3;
    return [x/f + first.lat, y/f + first.lng];
}