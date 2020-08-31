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


function wkt_rd2wgs(wkt) {
    RD_proj = '+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.9999079 +x_0=155000 +y_0=463000 +ellps=bessel +units=m +towgs84=565.2369,50.0087,465.658,-0.406857330322398,0.350732676542563,-1.8703473836068,4.0812 +no_defs';
    WGS_proj = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs';

    var regex = /[\d|.|e|E|\+|\-]+ [\d|.|e|E|\+|\-]+/g;
    var rd_coordinates = wkt.match(regex);

    for (i=0; i<rd_coordinates.length; i++) {
        coord = rd_coordinates[i].match(/[\d|.|e|E|\+|\-]+/g);  // array of strings
        coord = coord.map(Number);                              // array of numbers (RD)
        wgs_coord = proj4(RD_proj, WGS_proj, coord);            // array of numbers (WGS)
        wkt = wkt.replace(rd_coordinates[i], wgs_coord[0]+' '+wgs_coord[1]);
    }
    return wkt;
}