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

L.TimeDimension.Layer.WindowedGeoJson = L.TimeDimension.Layer.GeoJson.extend({

    initialize: function(layer, options) {
        L.TimeDimension.Layer.GeoJson.prototype.initialize.call(this, layer, options);
        this.startDate = new Date('2015-01-01T00:00:00+0100');
        this.simDuration = 1;
        this.endDate = new Date(this.startDate);
        this.endDate.setDate(this.endDate.getDate() + 1);
        this.getTimeWindowFromServer();
        this._loaded = true;
        map.timeDimension.setCurrentTime(0);
    },

    _update: function() {
        currentTime = new Date(this._timeDimension.getCurrentTime());
        if(currentTime < this.startDate || currentTime >= this.endDate) {
            this._loaded = false;
            this.startDate = currentTime;
            this.endDate = new Date(this.startDate);
            this.endDate.setDate(this.endDate.getDate() + 1);
            this.getTimeWindowFromServer();
        }
        //return L.TimeDimension.Layer.GeoJson.prototype._update.call(this);
        if (!this._map)
            return;
        if (!this._loaded) {
            return;
        }

        var time = this._timeDimension.getCurrentTime();

        var maxTime = this._timeDimension.getCurrentTime(),
            minTime = 0;
        if (this._duration) {
            var date = new Date(maxTime);
            L.TimeDimension.Util.subtractTimeDuration(date, this._duration, true);
            minTime = date.getTime();
        }

        // new coordinates:
        var layer = L.geoJson(null, this._baseLayer.options);
        var layers = this._baseLayer.getLayers();
        for (var i = 0, l = layers.length; i < l; i++) {
            var feature = this._getFeatureBetweenDates(layers[i].feature, minTime, maxTime);
            if (feature) {
                layer.addData(feature);
                if (this._addlastPoint && feature.geometry.type == "LineString") {
                    if (feature.geometry.coordinates.length > 0) {
                        var properties = feature.properties;
                        properties.last = true;
                        layer.addData({
                            type: 'Feature',
                            properties: properties,
                            geometry: {
                                type: 'Point',
                                coordinates: feature.geometry.coordinates[feature.geometry.coordinates.length - 1]
                            }
                        });
                    }
                }
            }
        }

        if (this._currentLayer) {
            this._map.removeLayer(this._currentLayer);
        }
        if (layer.getLayers().length) {
            layer.addTo(this._map);
            this._currentLayer = layer;
        }
    },



//    _update: function() {
//        currentTime = new Date(this._timeDimension.getCurrentTime());
//        this._loaded = false;
//        this.getSimulationData(currentTime);
//        return L.TimeDimension.Layer.GeoJson.prototype._update.call(this);
//    },

    eachLine: function(feature, layer) {
        if (feature.properties.pos) {
            direction = '   >   ';
        } else {
            direction = '   <   ';
        }
        layer.setText(null);
        let text_size = Math.max(20, 4*feature.properties.strokeWidth);
        layer.setText(direction, {repeat: true, offset: text_size/3, attributes: {fill: feature.properties.stroke, 'font-size': text_size}});

        load_str = Math.round((feature.properties.load + Number.EPSILON) * 100) / 100
        layer.bindPopup('<h2>'+feature.properties.id+'</h2><p>Load: '+load_str+' MWh');
        layer.bindTooltip('<h2>'+feature.properties.id+'</h2><p>Load: '+load_str+' MWh');

        layer.bindContextMenu({
            contextmenu: true,
            contextmenuWidth: 140,
            contextmenuItems: [{
                icon: '/icons/Graph.png',
                text: 'Show load duraction curve',
                callback: function(e) {
                    let target = e.relatedTarget;
                    let id = target.feature.properties.id;
                    console.log(id);
                    socket.emit('request_ielgas_ldc', {'id':id});
                }
            },{
                icon: '/icons/Graph.png',
                text: 'Monitor asset',
                callback: function(e) {
                    let target = e.relatedTarget;
                    let id = target.feature.properties.id;
                    console.log(id);
                    socket.emit('ielgas_monitor_asset', {'id':id});
                }
            }],
            contextmenuInheritItems: false
        });
    },

//    getSimulationData: function(date) {
//        socket.emit('get_simulation_data', date.toISOString(), (geojson_data) => {
//            // console.log(geojson_data);
//            var data = JSON.parse(geojson_data);
//
//            var geoJSONLayer = L.geoJSON(data, {
//                style: function(feature) {
//                    return {color: feature.properties.stroke, weight: feature.properties.strokeWidth};
//                },
//                onEachFeature: this.styleLine
//            });
//
//            // Set the underlying GeoJson layer to the newly created layer.
//            this._baseLayer = geoJSONLayer;
//            this._loaded = true;
//        });
//    },

    getTimeWindowFromServer: function() {
        // Obtain new date range.
        socket.emit('get_windowed_simulation_data', this.startDate.toISOString(), this.endDate.toISOString(), (geojson_test) =>
        {
            if(data == "{}")
            {
                console.log("No data was available for the current time window.");
            }
            console.log(data);
            var data = JSON.parse(geojson_test);

            var geoJSONLayer = L.geoJSON(data, {
                style: function(feature) {
                    return {color: feature.properties.stroke, weight: feature.properties.strokeWidth};
                },
                onEachFeature: this.eachLine
            });

            // Set the underlying GeoJson layer to the newly created layer.
            this._baseLayer = geoJSONLayer;
            this._loaded = true;
            this._update();
        });
    }
});


L.timeDimension.layer.windowedGeoJson = function(layer, options) {
    return new L.TimeDimension.Layer.WindowedGeoJson(layer, options);
};

class TimeDimension {

    constructor() {
//        this.sim_start_datetime = '2015-01-01T00:00:00+0100';
//        this.sim_end_datetime = '2016-01-01T00:00:00+0100';
//
//        this.current_time_window_start = new Date(this.sim_start_datetime);
//        this.current_time_window_end = new Date(this.current_time_window_start);
//        this.current_time_window_end.setDate(this.current_time_window_start.getDate() + 1);
    }

    initialize() {
        show_loader();
        socket.emit('timedimension_initialize', function(result) {
            if (result) {
                hide_loader();
                time_dimension.addGeoJSONLayer();
            }
        });
    }

    addGeoJSONLayer() {

        var geoJSONLayer = L.geoJSON();

        var geoJSONTDLayer = L.timeDimension.layer.windowedGeoJson(geoJSONLayer, {
            updateTimeDimension: false, // true
            duration: 'PT59M',
            updateTimeDimensionMode: 'replace',
            updateCurrentTime: true
        });

        geoJSONTDLayer.addTo(get_layers(active_layer_id, 'sim_layer'));
    }

    static create(event) {
        if (event.type === 'client_connected') {
            time_dimension = new TimeDimension();
            return time_dimension;
        }
    }
}

var time_dimension;

$(document).ready(function() {
    extensions.push(function(event) { TimeDimension.create(event) });
});

