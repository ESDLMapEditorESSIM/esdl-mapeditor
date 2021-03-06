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
        this.startDate = new Date(options.startDate);
        this.window_size = 24;
        this.endDate = new Date(this.startDate);
        map.timeDimension.setCurrentTime(0);
        this.getTimeWindowFromServer();
        this._loaded = true;
    },

    _update: function() {
        currentTime = new Date(this._timeDimension.getCurrentTime());
        if(currentTime < this.startDate || currentTime > this.endDate) {
            this._loaded = false;
            this.startDate = currentTime;
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
                    socket.emit('request_ielgas_ldc', {'id':id});
                }
            },{
                icon: '/icons/Graph.png',
                text: 'Monitor asset',
                callback: function(e) {
                    let target = e.relatedTarget;
                    let id = target.feature.properties.id;
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

    determineWindowEndTime: function() {
        var times = map.timeDimension.getAvailableTimes();
        var idx = times.indexOf(this.startDate.getTime());

        this.endDate = new Date(times[Math.min(times.length - 1, idx + 24)]);
    },

    getTimeWindowFromServer: function() {
        this.determineWindowEndTime();
        // Obtain new date range.
        socket.emit('get_windowed_simulation_data', this.startDate.toISOString(), this.endDate.toISOString(), (geojson_result) =>
        {
            if(geojson_result == "{}")
            {
                console.log("No data was available for the current time window.");
                return;
            }
            // console.log(geojson_result);
            var data = JSON.parse(geojson_result);

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

    initialize_animation_toolbar_setting() {
        socket.emit('time_dimension_get_settings', function(res) {
            let ab_visible = res['ab_visible'];
            time_dimension.show_hide_animation_toolbar(ab_visible);
        });
    }

    initialize(database, simulation_id, networks=[]) {
        time_dimension.removeGeoJSONLayers();
        show_loader();
        socket.emit('timedimension_initialize', {database: database, simulation_id: simulation_id, networks: networks}, function(result) {
            if (result) {
                hide_loader();

                var time_list = result;
                var startDate = time_list[0];
                // Time dimension expects time list to be a single string with times separated by a comma.

                time_list = time_list.join();
                map.timeDimension.setAvailableTimes(time_list, 'replace');
                // console.log(time_list);

                time_dimension.addGeoJSONLayer(startDate);
            }
        });
    }

    addGeoJSONLayer(startDate) {
        var geoJSONLayer = L.geoJSON();
        var geoJSONTDLayer = L.timeDimension.layer.windowedGeoJson(geoJSONLayer, {
            updateTimeDimension: false, // true
            duration: 'PT59M',
            updateTimeDimensionMode: 'replace',
            updateCurrentTime: true,
            startDate: startDate
        });

        geoJSONTDLayer.addTo(get_layers(active_layer_id, 'sim_layer'));
    }

    removeGeoJSONLayers() {
        clear_layers(active_layer_id, 'sim_layer');
    }

    toggle_animation_toolbar_visibility() {
        if ($('#menu_option_animation_bar').hasClass("ui-icon-check ui-icon"))
            time_dimension.show_hide_animation_toolbar(false);
        else
            time_dimension.show_hide_animation_toolbar(true);
    }

    show_hide_animation_toolbar(visible) {
        if (visible) {
            // copied from vendor/socib/leaflet.timedimension.src.js
            map.timeDimensionControl = L.control.timeDimension(map.options.timeDimensionControlOptions || {});
            map.addControl(map.timeDimensionControl);

            // set checkmark at view menu option
            $('#menu_option_animation_bar').addClass("ui-icon-check ui-icon");
        } else {
            if (map.timeDimensionControl) map.removeControl(map.timeDimensionControl);

            // remove checkmark at view menu option
            $('#menu_option_animation_bar').removeClass("ui-icon-check ui-icon");
        }
    }

    UISettings() {
        let $div = $('<div>').addClass('ui_settings_div').append($('<h3>').text('Animation toolbar'));

        let $visible_on_startup = $('<input>').attr('type', 'checkbox').attr('id', 'ab_visible').attr('value', 'ab_visible').attr('name', 'ab_visible');
        let $abvis_label = $('<label>').attr('for', 'ab_visible').text('Animation toolbar visible on startup');
        $div.append($('<p>').append($visible_on_startup).append($abvis_label));

        $visible_on_startup.change(function() {
            let ab_visible = $('#ab_visible').is(':checked');
            time_dimension.show_hide_animation_toolbar(ab_visible);
            socket.emit('time_dimension_set_settings', {ab_visible: ab_visible});
        });

        socket.emit('time_dimension_get_settings', function(res) {
            let ab_visible = res['ab_visible'];
            $('#ab_visible').prop('checked', ab_visible);
        });

        return $div;
    }

    static create(event) {
        if (event.type === 'client_connected') {
            time_dimension = new TimeDimension();
            time_dimension.initialize_animation_toolbar_setting();
            return time_dimension;
        }
        if (event.type === 'ui_settings_div') {
            return time_dimension.UISettings();
        }
    }
}

var time_dimension;

$(document).ready(function() {
    extensions.push(function(event) { return TimeDimension.create(event) });
});
