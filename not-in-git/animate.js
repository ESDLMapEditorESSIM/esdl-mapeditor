
L.TimeDimension.Layer.GeoJson.GeometryCollection = L.TimeDimension.Layer.GeoJson.extend({

    // Do not modify features. Just return the feature if it intersects
    // the time interval
    _getFeatureBetweenDates: function(feature, minTime, maxTime) {
        var featureStringTimes = this._getFeatureTimes(feature);
        if (featureStringTimes.length == 0) {
            return feature;
        }
        var featureTimes = [];
        for (var i = 0, l = featureStringTimes.length; i < l; i++) {
            var time = featureStringTimes[i]
            if (typeof time == 'string' || time instanceof String) {
                time = Date.parse(time.trim());
            }
            featureTimes.push(time);
        }

        if (featureTimes[0] > maxTime || featureTimes[l - 1] < minTime) {
            return null;
        }
        return feature;
    },

});

L.timeDimension.layer.geoJson.geometryCollection = function(layer, options) {
    return new L.TimeDimension.Layer.GeoJson.GeometryCollection(layer, options);
};


function getCommonBaseLayers(map){
    var osmLayer = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
    });
    var bathymetryLayer = L.tileLayer.wms("http://ows.emodnet-bathymetry.eu/wms", {
        layers: 'emodnet:mean_atlas_land',
        format: 'image/png',
        transparent: true,
        attribution: "EMODnet Bathymetry",
        opacity: 0.8
    });
    var coastlinesLayer = L.tileLayer.wms("http://ows.emodnet-bathymetry.eu/wms", {
        layers: 'coastlines',
        format: 'image/png',
        transparent: true,
        attribution: "EMODnet Bathymetry",
        opacity: 0.8
    });
    var bathymetryGroupLayer = L.layerGroup([bathymetryLayer, coastlinesLayer]);
    bathymetryGroupLayer.addTo(map);
    return {
        "EMODnet Bathymetry": bathymetryGroupLayer,
        "OSM": osmLayer
    };
}

var map = L.map('map', {
    zoom: 8,
    fullscreenControl: true,
    timeDimensionControl: true,
    timeDimensionControlOptions: {
        loopButton: true,
    },
    timeDimension: true,
    center: [39.6145, 1.99363]
});
var baseLayers = getCommonBaseLayers(map); // see baselayers.js
L.control.layers(baseLayers, {}).addTo(map);

var geoJsonFeatures = {
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "properties": {
      "time": 1430391600000,
      "id": 1,
      "stroke": "#0000ff",
      "strokewidth": 10
    },
    "geometry": {
      "type": "GeometryCollection",
      "geometries": [{
        "type": "MultiPoint",
        "coordinates": [
          [1.8003, 38.9580],
          [1.7968, 38.9498],
          [1.7648, 38.9737],
          [1.7681, 38.9814]
        ]
      }, {
        "type": "MultiLineString",
        "coordinates": [
          [
            [1.78519, 38.96943],
            [1.78095, 38.96082]
          ],
          [
            [1.79229, 38.96415],
            [1.78854, 38.95544]
          ]
        ]
      }]
    }
  }, {
    "type": "Feature",
    "properties": {
      "time": 1430391600000,
      "id": 2,
      "stroke": "#ff0000",
      "strokewidth": 20
    },
    "geometry": {
      "type": "GeometryCollection",
      "geometries": [{
        "type": "MultiLineString",
        "coordinates": [
          [
            [1.78205, 38.97162],
            [1.77715, 38.96374]
          ],
          [
            [1.77247, 38.97880],
            [1.76811, 38.97036]
          ]
        ]
      }]
    }
  }, {
    "type": "Feature",
    "properties": {
      "time": 1430395200000,
      "id": 3,
      "stroke": "#555555",
      "strokewidth": 4
    },
    "geometry": {
      "type": "GeometryCollection",
      "geometries": [{
        "type": "MultiPoint",
        "coordinates": [
          [1.6003, 38.9580],
          [1.5968, 38.9498],
          [1.5648, 38.9737],
          [1.5681, 38.9814]
        ]
      }, {
        "type": "MultiLineString",
        "coordinates": [
          [
            [1.58519, 38.96943],
            [1.58095, 38.96082]
          ],
          [
            [1.59229, 38.96415],
            [1.58854, 38.95544]
          ],
          [
            [1.58205, 38.97162],
            [1.57715, 38.96374]
          ],
          [
            [1.57247, 38.97880],
            [1.56811, 38.97036]
          ]
        ]
      }]
    }
  }]
};

var geoJsonLayer = L.geoJson(geoJsonFeatures, {
  style: function(feature) {
    return {
      "color": feature.properties.stroke,
      "weight": feature.properties.strokewidth,
      "opacity": 0.4
    };
  }
});

map.fitBounds(geoJsonLayer.getBounds());

var geoJsonTimeLayer = L.timeDimension.layer.geoJson.geometryCollection(geoJsonLayer, {
  updateTimeDimension: true,
  updateTimeDimensionMode: 'replace',
  duration: 'PT30M',
});
geoJsonTimeLayer.addTo(map);