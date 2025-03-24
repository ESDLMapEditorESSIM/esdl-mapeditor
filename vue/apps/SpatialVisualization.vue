<!--
  - This work is based on original code developed and copyrighted by TNO 2025.
  - Subsequent contributions are licensed to you by the developers of such code and are
  - made available to the Project under one or several contributor license agreements.
  -
  - This work is licensed to you under the Apache License, Version 2.0.
  - You may obtain a copy of the license at
  -
  -     http://www.apache.org/licenses/LICENSE-2.0
  -
  - Contributors:
  -     TNO         - Initial implementation
  - Manager:
  -     TNO
  -->

<template>
  <a-space
    id="spatial-visualization"
    direction="vertical"
    style="width: 100%; padding: 8px; height: 100%;"
  >
    <!-- Header -->
    <a-row>
      <h1>
        <i class="fa fa-layer-group" />
        Spatial Visualization
      </h1>
    </a-row>
    <!----------------------------------->
    <!------------- Content ------------->
    <!----------------------------------->
    <a-col style="height: 100%;">
      <!-- Data sources -->
      <a-col>
        <a-row style="padding-bottom: 8px; align-items: center; justify-content: space-between;">
          <a-col :span="12">
            <h2>Data Sources</h2>
          </a-col>
          <a-col>
            <a-button
              type="primary"
              ghost
              small
              @click="openAddDataModal()"
            >
              <component 
                :is="FileAddOutlined"
                style="vertical-align: 0.1rem"
              />
              Add Source
            </a-button>
            <!-- Add Data modal -->
            <a-modal
              v-model:open="addDataModalOpen"
              title="Add data source"
              width="65%"
            >
              <div v-if="isLoading" class="loading">
                <a-spin :indicator="loadingIcon" />
              </div>
              <br>
              <a-tabs v-model:activeKey="activeTabKey" type="card">
                <!-- NOTE: Only support ESDL at the moment, can be extended to support GeoJSON, or other data sources. -->
                <a-tab-pane key="add-data-tab-esdl" tab="ESDL" style="overflow-y: scroll; max-height: 600px;">
                  <a-row
                    v-for="(ds, idx) in datasources"
                    :key="idx"
                    style="padding: 16px;"
                  >
                    <h4>{{ ds.name }}</h4>
                    <a-list
                      :data-source="Object.keys(ds.sources)"
                      size="small"
                      style="width: 100%;"
                      bordered
                    >
                      <template #renderItem="{ item }">
                        <a-list-item>
                          <template #actions>
                            <a-button
                              :disabled="ds.loadedSources[item] !== undefined || isLoading"
                              @click="() => {
                                ds.loading = true;
                                ds.addAsGeoJsonSource(item).then(() => {
                                  ds.loading = false;
                                });
                              }"
                            >
                              Add
                            </a-button>
                          </template>
                          {{ item }}
                        </a-list-item>
                      </template>
                    </a-list>
                  </a-row>
                </a-tab-pane>
              </a-tabs>
              <template #footer>
                <a-button key="back" :disabled="isLoading" @click="closeAddDataModal">Cancel</a-button>
                <a-button key="submit" type="primary" :disabled="isLoading" @click="closeAddDataModal">OK</a-button>
              </template>
            </a-modal>
          </a-col>
        </a-row>
        <!-- Loaded sources -->
        <a-card
          v-for="(ds, idx) in datasources"
          v-show="Object.keys(ds.loadedSources).length > 0"
          :key="idx"
          :title="ds.name"
          size="small"
          style="width: 100%; margin-bottom: 8px;"
          :body-style="{'padding': '0px'}"
        >
          <template #extra>
            <a-button
              type="link"
              :loading="ds.loading"
              :disabled="ds.loading"
              @click="() => ds.onSourceUpdate()"
            >
              Update
            </a-button>
          </template>
          <a-list
            :data-source="Object.keys(ds.loadedSources)"
            size="small"
            style="width: 100%;"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <template #actions>
                  <a-button
                    type="link"
                    :loading="ds.loading"
                    :disabled="ds.loading"
                    @click="() => ds.onAddLayerToMap(item)"
                  >
                    Add to map
                  </a-button>
                </template>
                {{ item }}
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
      <a-divider />
      <!----------------------------------->
      <!------------- Layers -------------->
      <!----------------------------------->
      <a-col>
        <h2>Layers</h2>
        <a-collapse
          v-if="visualizedLayers.length"
          v-model:activeKey="activeVizLayerKeys"
        >
          <a-collapse-panel
            v-for="(vizLayer, idx) in visualizedLayers"
            :key="idx"
            :header="vizLayer.name"
          >
            <a-row class="layer-style-option-row" style="padding-bottom: 8px;">
              Source
              <a-col :span="15">
                {{ vizLayer.sourceRef.name }}
              </a-col>
            </a-row>
            <a-row class="layer-style-option-row" style="padding-bottom: 8px;">
              Style field
              <a-select
                :value="vizLayer.styledField"
                style="width: 250px" 
                :options="vizLayer.fieldOptions"
                @change="(field) => vizLayer.onSelectStyledField(field)"
                @mouseleave="removeTooltipPopup"
              />
            </a-row>
            <a-space 
              v-if="vizLayer.styledField !== undefined"
              direction="vertical"
              style="width: 100%;"
            >
              <a-row class="layer-style-option-row">
                Style type
                <a-select
                  :value="vizLayer.styledType"
                  style="width: 250px" 
                  :options="VisualizedLayer.StyleTypes[vizLayer.styledFieldType]"
                  :status="vizLayer.styledType === undefined ? 'error' : null"
                  :placeholder="vizLayer.styledType === undefined ? 'Unsupported type for styling' : ''"
                  @change="(type) => vizLayer.onSelectStyleType(type)"
                  @mouseleave="removeTooltipPopup"
                />
              </a-row>
              <a-row v-if="vizLayer.colorPickerColor !== undefined" class="layer-style-option-row">
                Color
                <a-select
                  :value="vizLayer.colorPickerColor"
                  style="width: 250px"
                  @change="(color) => vizLayer.onSelectColor(color)"
                >
                  <a-select-option
                    v-for="option in VisualizedLayer.colorPickerPalette"
                    :key="option.value"
                    :value="option.value"
                  >
                    <a-col
                      :key="option.label"
                      :span="24"
                      :style="{ backgroundColor: option.label, height: '100%' 
                      }"
                    />
                  </a-select-option>
                </a-select>
              </a-row>
              <a-row v-if="vizLayer.colorPalette !== undefined" class="layer-style-option-row">
                Color palette
                <a-select
                  :value="vizLayer.colorPalette"
                  style="width: 250px"
                  @change="(palette) => vizLayer.onSelectPalette(palette)"
                >
                  <a-select-option
                    v-for="option in vizLayer.displayedPalettes"
                    :key="option.value"
                    :value="option.value"
                  >
                    <a-row>
                      <a-col
                        v-for="color in option.sample"
                        :key="color"
                        :span="2"
                        :style="{ backgroundColor: color.startsWith('#') ? color : `#${color}`, height: '35px' }"
                      />
                    </a-row>
                  </a-select-option>
                </a-select>
              </a-row>
              <a-row class="layer-style-option-row">
                Size
                <a-col :span="16">
                  <a-slider
                    :value="vizLayer.markerSizeValue"
                    :min="1"
                    :max="10"
                    :step="1"
                    @change="(size) => vizLayer.onSizeChange(size)"
                  />
                </a-col>
              </a-row>
              <a-row class="layer-style-option-row">
                Opacity
                <a-col :span="16">
                  <a-slider
                    :value="vizLayer.opacity"
                    :min="0"
                    :max="1"
                    :step="0.01"
                    @change="(opacity) => vizLayer.onOpacityChange(opacity)"
                  />
                </a-col>
              </a-row>
              <a-row
                v-if="!vizLayer.features[0].geometry.type.includes('LineString')"
                class="layer-style-option-row"
              >
                Show outline
                <a-col :span="2">
                  <a-switch
                    :checked="vizLayer.showStroke"
                    size="small"
                    @change="(checkedStatus) => vizLayer.onToggleShowStroke(checkedStatus)"
                  />
                </a-col>
              </a-row>
              <a-row class="layer-style-option-row">
                Show label
                <a-col :span="2">
                  <a-switch
                    :checked="vizLayer.showLabel"
                    size="small"
                    @change="(checkedStatus) => vizLayer.onToggleShowLabels(checkedStatus)"
                  />
                </a-col>
              </a-row>
            </a-space>
            <template #extra>
              <a-row>
                <a-button
                  type="text"
                  size="small"
                  @click="(event) => vizLayer.toggleLayer(event)"
                >
                  <component 
                    :is="vizLayer.visible ? EyeOutlined : EyeInvisibleOutlined"
                    style="vertical-align: 0.1rem"
                  />
                </a-button>
                <a-button
                  type="text"
                  size="small"
                  @click="(event) => vizLayer.removeLayer(event)"
                >
                  <component 
                    :is="DeleteOutlined"
                    style="vertical-align: 0.1rem"
                  />
                </a-button>
              </a-row>
            </template>
          </a-collapse-panel>
        </a-collapse>
      </a-col>
    </a-col>
  </a-space>
</template>

<script setup>
import { ref, onMounted, computed, h } from "vue";
import { 
  DeleteOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  FileAddOutlined,
  LoadingOutlined
} from "@ant-design/icons-vue";
import { getAssetFields, generateColorscale } from "../utils/spatialVisualization";

const loadingIcon = h(LoadingOutlined, {
  style: { fontSize: '5rem' }, spin: true
});

// to prevent stuck popup on UI
const removeTooltipPopup = () => { window.jquery(".ui-tooltip-content").parents('div').remove();};

// TODOs: Future works:
// support data filtering
// show data table
// support asset references field
// support custom field
// speed up query time (getAssetFields)
// allow reordering of vizualized layers
// export data sources
// rename Marker with symbol
// sync layer show/hide with map layer control event
// improve color scale options and calculation
// support label or icon visualization style?
// add layer legend?
// support date field visualization?

const datasources = ref([]);

const activeVizLayerKeys = ref([]);

// Add Data modal states
const addDataModalOpen = ref(false);
const activeTabKey = ref("add-data-tab-esdl");

// esdl_list defined in multi_esdl.js contains an object of opened ESDLs in map editor.
// It is used here to keep the user states from this component (e.g. datasources and vizualized layers) in sync. globally.
let esdlListRef = esdl_list;

// pie_chart_color_list is defined in area_building_layer.js
const defaultColors = pie_chart_color_list;

onMounted(async () => {
  console.debug("Initializing Spatial Visualization component.");
  initDatasources();
});

const openAddDataModal = () => {
  addDataModalOpen.value = true;
};

const closeAddDataModal = () => {
  addDataModalOpen.value = false;
};

/**
 * Populate the datasources array from the existing sources (the ones kept in esdlListRef)
 * or instantiate a new EsdlLayerSource.
 */
const initDatasources = () => {
  const esIDs = Object.keys(esdlListRef);
  esIDs.forEach((esId) => {
    const existingEsdlDs = esdlListRef[esId]["viz_datasources"];
    if (existingEsdlDs && existingEsdlDs.length === 1) {
      datasources.value.push(existingEsdlDs[0]);
    } else {
      const esdlTitle = esdlListRef[esId].title;
      const esdlSource = new EsdlLayerSource(esId, esdlTitle, 'ESDL');
      // To store EsdlLayerSource instance globally for later retrieval (e.g. when the component is reopened)
      esdlListRef[esId]["viz_datasources"] = [esdlSource];
      datasources.value.push(esdlSource);
    }
  });
};

const visualizedLayers = computed(() => {
  return datasources.value
    .filter(ds => ds.vizLayers !== undefined)
    .map(ds => ds.vizLayers)
    .flat();
});

const isLoading = computed(() => {
  return datasources.value.find(ds => ds.loading === true) ? true : false; 
});

class DataSource {
  constructor(
    id, name, type
  ) {
    this.id = id;
    this.name = name;
    this.type = type;
  }
}

class EsdlLayerSource extends DataSource {
  constructor(id, name, type) {
    super(id, name, type);
    this.sources = {};
    this.loadedSources = {};
    this.vizLayers = [];
    this.loading = false;

    this._getEsdlAssetLayers();
    this._addFeatureGroupLayerToMap();
  }

  /**
   * Enrich the asset features of the given assetType with attribute (field) values returned 
   * from the backend and add them as a GeoJSON FeatureCollection to loadedSources.
   * 
   * @param {string} assetType ESDL asset type 
   */
  async addAsGeoJsonSource (assetType) {
    const layerFeatures = this.sources[assetType];
    const geoJsonFeaturePromises = layerFeatures.map(async (f) => {
      const g = f.toGeoJSON();

      const assetId = f.id;
      const fields = await getAssetFields(this.id, assetId);
      g['_fields'] = fields;
      
      const properties = {};
      fields.forEach((f) => {
        properties[f.name] = f.value;
      });
      g.properties = properties;

      return g;
    });

    const geoJsonFeatureCollection = await Promise.all(geoJsonFeaturePromises);

    this.loadedSources = {
      ...(this.loadedSources || {}),
      [assetType]: geoJsonFeatureCollection 
    };
  }

  /**
   * Initialize a new VisualizedLayer of the given assetType and add it to the vizLayers collection.
   * 
   * @param {string} assetType ESDL asset type 
   */
  onAddLayerToMap (assetType) {
    const layerName = this._createUniqueVizLayerName(assetType);
    const features = this.loadedSources[assetType];
    // When instantiated, new layer will be added to the map.
    const vizLayer = new VisualizedLayer(this, layerName, features);
    this.vizLayers.push(vizLayer);
  }

  /**
   * Update the loadedSources and the corresponding visualized layers.
   * 
   * Useful to call after the source ESDL is edited by the user (e.g. attribute value update),
   * and to show the changes in visualized layers.
   */
  onSourceUpdate () {
    this.loading = true;
    this._getEsdlAssetLayers().then(async () => {
      const addSourcePromises = Object.keys(this.loadedSources).map(async (assetType) => {
        return this.addAsGeoJsonSource(assetType);
      });
      // Wait for all addAsGeoJsonSource calls to complete
      await Promise.all(addSourcePromises);

      Object.keys(this.loadedSources).forEach((assetType) => {
        this.vizLayers.forEach((vizLayer) => {
          if (vizLayer.name.includes(assetType)) {
            // Update and redraw the layer with the latest features.
            const updatedFeatures = this.loadedSources[assetType];
            vizLayer.redrawLayerOnFeaturesUpdate(updatedFeatures);
          }
        });
      });

      this.loading = false;
    });
  }

  // ---------------------------- //
  // ----- Internal methods ----- //
  // ---------------------------- //

  async _getEsdlAssetLayers() {
    const esdlLayer = window.get_layers(this.id, 'esdl_layer');
    const layerList = esdlLayer.getLayers();
    
    const layers = {};
    layerList.forEach((l) => {  
      if (Object.keys(layers).includes(l.type)) {
        layers[l.type].push(l);
      } else {
        layers[l.type] = [l];
      }
    });
    this.sources = layers;
  }

  /**
   * Add a visualization feature group layer to the map if it does not exist.
   * NOTE: The "viz_layer" is initialized in multi_esdl.js
   */
  _addFeatureGroupLayerToMap () {
    if (!Object.keys(esdlListRef[this.id].layers).includes("viz_layer")) {
      esdlListRef[this.id].layers["viz_layer"] = L.featureGroup().addTo(map);
    }
  }

  _createUniqueVizLayerName = (name) => {
    let vizLayerName = name;
    if (this.vizLayers.find(l => l.name === name)) {
      const suffixNr = this.vizLayers.filter(l => l.name.includes(name)).length;
      vizLayerName = `${vizLayerName} ${suffixNr + 1}`;
    }
    return vizLayerName;
  };
}

class VisualizedLayer {
  static initMarkerSizeValue = 5;
  static initOpacity = 1.0;
  static initStrokeWeight = 2;
  static initColorPickerColor = undefined;
  static initColorPalette = undefined;
  static initDisplayedPalettes = [];

  // a constant factor to scale between marker radius and weight. 
  static radiusToWeight = 0.4;

  // Supported style types
  static StyleTypes = Object.freeze({
    boolean: [
      {value: "categoricalColor", label: "Categorical Color" }
    ],
    string: [
      {value: "singleColor", label: "Single Color" },
      {value: "categoricalColor", label: "Categorical Color" }
    ],
    number: [
      {value: "size", label: "Size" },
      {value: "gradientColor", label: "Gradient Color" },
      {value: "colorAndSize", label: "Color and Size" },
    ]
  });

  static colorPickerPalette = defaultColors.map(c => ({value: c, label: c}));

  static sampleNum = 12;
  static colorPalettes = {
    "Categorical": [
      { label: 'Default', value: 'Default', sample: defaultColors.slice(0, VisualizedLayer.sampleNum) },
      { label: 'Qualitative', value: 'Qualitative', sample: window.palette('mpn65', VisualizedLayer.sampleNum) },
    ],
    "Continuous": [
      { label: 'Diverging', value: 'Diverging', sample: window.palette('tol-dv', VisualizedLayer.sampleNum) },
      { label: 'Sequential', value: 'Sequential', sample: window.palette('tol-sq', VisualizedLayer.sampleNum) },
      { label: 'Rainbow', value: 'Rainbow', sample: window.palette('tol-rainbow', VisualizedLayer.sampleNum) },
    ]
  };

  static setFeatureStyle (geometryType, color='#1f78b4', opacity=1, radius=5, weight=2, stroke=false) {
    switch (geometryType) {
      case "Point":
      case "MultiPoint":
        return {
          fillColor: color,
          radius: radius,
          fillOpacity: opacity,
          stroke: stroke,
        };
      case "LineString":
      case "MultiLineString":
        return {
          color: color,
          weight: weight,
          opacity: opacity,
        };
      case "Polygon":
      case "MultiPolygon":
        return {
          fillColor: color,
          fillOpacity: opacity,
          stroke: stroke,
        };
      default:
        console.error(`Unsupported geometry type: ${geometryType}.`);
        return {};
    }
  }

  static customMapPane = 'vizLayerPane';

  constructor(
    sourceRef, name, features
  ) {
    this.sourceRef = sourceRef;
    this.name = name;
    this.features = features;

    this._initVizLayerPane();

    // Properties instantiated with default values
    this.id = `${sourceRef.id}-${name}`;
    this.layer = this.createGeoJsonLayer(this.features);
    this.visible = true;
    this.fieldOptions = this._listLayerFieldOptions();

    this.addLayerToMap(this.layer);

    // Layer styling options
    this.styledField = undefined;
    this.styledFieldType = undefined;
    this.styledType = undefined;
    this.markerSizeValue = VisualizedLayer.initMarkerSizeValue;
    this.opacity = VisualizedLayer.initOpacity;
    this.colorPickerColor = VisualizedLayer.initColorPickerColor;
    this.colorPalette = VisualizedLayer.initColorPalette;
    this.displayedPalettes = VisualizedLayer.initDisplayedPalettes;
    this.showStroke = false;
    this.showLabel = false;
  }

  createGeoJsonLayer (features) {
    const layer = L.geoJSON(features, {
      style: function (feature) {
        return VisualizedLayer.setFeatureStyle(feature.geometry.type);
      },
      pointToLayer: function (feature, latlng) {
        return L.circleMarker(latlng, VisualizedLayer.setFeatureStyle(feature.geometry.type));
      },
    });

    // Add the layer to the custom pane after initialization.
    layer.eachLayer((featureLayer) => {
      featureLayer.options.pane = VisualizedLayer.customMapPane;
    });

    return layer;
  }

  removeLayerFromMap (layer) {
    if (esdlListRef[this.sourceRef.id].layers["viz_layer"].hasLayer(layer)) {
      // Remove existing tooltips to avoid them lingering on the map.
      layer.eachLayer((featureLayer) => {
        featureLayer.closeTooltip();
        featureLayer.unbindTooltip(); 
      });
      esdlListRef[this.sourceRef.id].layers["viz_layer"].removeLayer(layer);
    }
  }

  addLayerToMap (layer) {
    esdlListRef[this.sourceRef.id].layers["viz_layer"].addLayer(layer);
  }
  
  redrawLayerOnFeaturesUpdate (updatedFeatures) {
    this.features = updatedFeatures;
    this.removeLayerFromMap(this.layer);
    this.layer = this.createGeoJsonLayer(this.features);
    this.addLayerToMap(this.layer);
    this.styleLayer(this.styledType);
  }

  toggleLayer (event) {
    event.stopPropagation();
    if (this.visible) {
      this.layer.remove();
      this.visible = false;
    } else {
      this.layer.addTo(map);
      this.visible = true;
    }
  }

  removeLayer (event) {
    event.stopPropagation();
    if (this.sourceRef) {
      this.sourceRef.vizLayers = this.sourceRef.vizLayers.filter(layer => layer.id !== this.id);
      this.removeLayerFromMap(this.layer);
    }
  }

  onSelectStyledField (selectedField) {
    this.styledField = selectedField;
    this.styledFieldType = this.fieldOptions.find(f => f.value === selectedField).type;

    let defaultStyleType = undefined;
    if (Object.keys(VisualizedLayer.StyleTypes).includes(this.styledFieldType)) {
      // Default to the first StyleType when the styledField is updated.
      defaultStyleType = VisualizedLayer.StyleTypes[this.styledFieldType][0].value;
    } else {
      console.warn(`No supported style type for ${this.styledField} [${this.styledFieldType}]`);
    }
    this._setStyleType(defaultStyleType);
  }

  onSelectStyleType (selectedStyleType) {
    this._setStyleType(selectedStyleType);
  }

  onSizeChange (size) {
    this.markerSizeValue = size;
    this.styleLayer(this.styledType);
  }

  onSelectColor (color) {
    this.colorPickerColor = color;
    this.styleLayer(this.styledType);
  }

  onSelectPalette (palette) {
    this.colorPalette = palette;
    this.styleLayer(this.styledType);
  }

  onOpacityChange (opacity) {
    this.opacity = opacity;
    this.styleLayer(this.styledType);
  }

  onToggleShowStroke (checkedStatus) {
    this.showStroke = checkedStatus;
    this.styleLayer(this.styledType);
  }

  onToggleShowLabels (checkedStatus) {
    this.showLabel = checkedStatus;
    this.styleLayer(this.styledType);
  }

  /**
   * Style layer according to the given styleType and current style options.
   * 
   * @param {string|undefined} styleType The style type to be applied.
   */
   styleLayer (styleType) {
    switch (styleType) {
      default:
      case "singleColor":
        this._styleMarkerWithSingleColor(this.colorPickerColor);
        this._styleMarkerSize(this.markerSizeValue);
        break;
      case "categoricalColor":
        this._styleMarkerColorOnCategorizedFieldValue(this.styledField, this.colorPalette);
        this._styleMarkerSize(this.markerSizeValue);
        break;
      case "size":
        this._styleMarkerWithSingleColor(this.colorPickerColor);
        this._styleMarkerSizeOnNumericalFieldValue(this.styledField);
        break;
      case "gradientColor":
        this._styleMarkerColorOnNumericalFieldValue(this.styledField, this.colorPalette);
        this._styleMarkerSize(this.markerSizeValue);
        break;
      case "colorAndSize":
        this._styleMarkerColorOnNumericalFieldValue(this.styledField, this.colorPalette);
        this._styleMarkerSizeOnNumericalFieldValue(this.styledField);
        break;
    }
    this._styleMarkerOpacity(this.opacity);
    this._showHideMarkerStroke(this.showStroke);
    this._showHideFeatureLabels(this.styledField, this.showLabel);
  }

  // ---------------------------------------- //
  // ----- Internal methods for styling ----- //
  // ---------------------------------------- //

  _styleMarkerWithSingleColor (color) {
    this.layer.setStyle({
      fillColor: color,
      color: color
    });
  }

  _styleMarkerSize (size) {
    const isPolyline = this.features[0].geometry.type.includes('LineString');
    this.layer.setStyle({
      radius: size, 
      weight: isPolyline
        ? size * VisualizedLayer.radiusToWeight 
        : VisualizedLayer.initStrokeWeight
    });
  }

  _styleMarkerOpacity (opacity) {
    this.layer.setStyle({
      opacity: opacity, 
      fillOpacity: opacity 
    });
  }

  // Should only be applied to Point or Polygon feature
  _showHideMarkerStroke (showStroke) {
    const isPolyline = this.features[0].geometry.type.includes('LineString');
    if (!isPolyline) {
        this.layer.setStyle({
        stroke: showStroke,
        weight: VisualizedLayer.initStrokeWeight,
        color: '#2e4053'
      });
    }
  }

  /**
   * Show or hide the selected field value from features as tooltip labels.
   */
  _showHideFeatureLabels (selectedField, showLabel=false) {
    this.layer.eachLayer((featureLayer) => {
      // Clean up existing tooltip
      featureLayer.closeTooltip();
      featureLayer.unbindTooltip();

      if (showLabel && (featureLayer.feature && featureLayer.feature.properties)) {
        const fieldValue = featureLayer.feature.properties[selectedField];
        const popupContent = fieldValue !== null ? `${fieldValue}` : "No data";
        featureLayer.bindTooltip(popupContent, {
          permanent: true,
          direction: 'top',
          opacity: 0.8
        }).openTooltip();
      }
    });
  }

  _styleMarkerColorOnCategorizedFieldValue (styledField, palette) {
    const fieldUniqueValues = this._getFieldUniqueValues(styledField);
    if (fieldUniqueValues.length) {
      const colorscale = generateColorscale(palette, fieldUniqueValues.length);
      this.layer.setStyle((feature) => {
        const fieldValue = feature.properties[styledField];
        const idx = fieldUniqueValues.findIndex((val) => val === fieldValue);
        // To handle if the number of unique features is more than available colors (e.g. Default)
        const markerColor = colorscale[idx % colorscale.length];
        return {
          fillColor: markerColor,
          color: markerColor
        };
      });
    } else {
      const markerColor = generateColorscale(palette, 1);
      this._styleMarkerWithSingleColor(markerColor[0]);
    }
  }

  _styleMarkerColorOnNumericalFieldValue (styledField, palette) {
    const fieldUniqueValues = this._getFieldUniqueValues(styledField);

    // TODO: how should this be defined?
    const colorNum = 25;
    const colorscale = generateColorscale(palette, colorNum + 1);

    if (fieldUniqueValues.length > 1) {
      const min = Math.min(...fieldUniqueValues);
      const max = Math.max(...fieldUniqueValues);

      this.layer.setStyle((feature) => {
        const fieldValue = feature.properties[styledField];
        const normalizedValue = (Math.log1p(fieldValue) - Math.log1p(min)) / 
                                (Math.log1p(max) - Math.log1p(min));
        const colorIndex = parseInt(normalizedValue * colorNum);
        const markerColor = colorscale[colorIndex];
        return {
          fillColor: markerColor,
          color: markerColor
        };
      });
    } else {
      const markerColor = generateColorscale(palette, 1);
      this._styleMarkerWithSingleColor(markerColor[0]);
    }
  }

  _styleMarkerSizeOnNumericalFieldValue (styledField) {
    const fieldUniqueValues = this._getFieldUniqueValues(styledField);
    if (fieldUniqueValues.length > 1) {
      const min = Math.min(...fieldUniqueValues);
      const max = Math.max(...fieldUniqueValues);

      const sizeMin = this.markerSizeValue;
      const sizeMax = sizeMin * 6;

      this.layer.setStyle((feature) => {
        const normalizedValue = (Math.log1p(feature.properties[styledField]) - Math.log1p(min)) / 
                                (Math.log1p(max) - Math.log1p(min));
        const size = normalizedValue * (sizeMax - sizeMin) + sizeMin;
        const isPolyline = feature.geometry.type.includes("LineString");
        return {
          radius: size, 
          weight: isPolyline
            ? size * VisualizedLayer.radiusToWeight
            : VisualizedLayer.initStrokeWeight
        };
      });
    } else {
      this._styleMarkerSize(this.markerSizeValue);
    }
  }

  /**
   * When the styledType is updated, reset the style options (size, opacity, etc.) to the default state,
   * and apply styledFieldType and styledType dependent color settings to style layer.
   * 
   * @param {string|undefined} styleType The style type to be applied.
   */
   _setStyleType (styleType) {
    this.styledType = styleType;

    this._resetStyleOptions();

    if (styleType === undefined || styleType === 'singleColor' || styleType === 'size') {
      this.colorPickerColor = '#1f78b4';
    } else {
      if (["string", "boolean"].includes(this.styledFieldType)) {
        this.displayedPalettes = VisualizedLayer.colorPalettes["Categorical"];
        this.colorPalette = this.displayedPalettes[0].value;
      } else if (this.styledFieldType === "number") {
        this.displayedPalettes = VisualizedLayer.colorPalettes["Continuous"];
        this.colorPalette = this.displayedPalettes[0].value;
      } else {
        console.warn(`No supported color palette for styledFieldType: ${this.styledFieldType}`);
      }
    }

    this.styleLayer(styleType);
  }

  _resetStyleOptions () {
    this.markerSizeValue = VisualizedLayer.initMarkerSizeValue;
    this.opacity = VisualizedLayer.initOpacity;
    this.colorPickerColor = VisualizedLayer.initColorPickerColor;
    this.colorPalette = VisualizedLayer.initColorPalette;
    this.displayedPalettes = VisualizedLayer.initDisplayedPalettes;
  }

  // --------------------------------- //
  // ----- Internal util methods ----- //
  // --------------------------------- //

  /**
   * Initialize a custom map pane to ensure GeoJSON features are added to the vizLayerPane
   * and are displayed on the top of the map.
   * 
   * Ref:
   * https://leafletjs.com/examples/map-panes/
   * https://leafletjs.com/reference.html#map-tooltippane
   */
  _initVizLayerPane () {
    if (map.getPane(VisualizedLayer.customMapPane) === undefined) {
      const vizLayerPane = map.createPane(VisualizedLayer.customMapPane);
      vizLayerPane.style.zIndex = 640; // Keep it below the tooltippane (650)
    }
  }

  _listLayerFieldOptions () {
    const options = this.features[0]._fields.map(f => ({
      label: `${f.name.toUpperCase()} [${f.type}]`,
      value: f.name,
      type: f.type,
    }));
    return options;
  }

  /**
   * Retrieves unique values for a specified field from the layer features' properties.
   * 
   * @param {string} fieldName The field name string.
   */
  _getFieldUniqueValues (fieldName) {
    const fieldVals = this.features
      .map(f => f.properties[fieldName])
      .filter(element => element !== null);
    return [...new Set(fieldVals)];
  }
}

</script>

<style scoped>

.layer-style-option-row {
  justify-content: space-between;
}

.loading {
  position: absolute;
  display: flex;
  flex-direction: column;
  justify-content: center;
  width: calc(100% - 52px);
  height: calc(100% - 60px);
  z-index: 100;
  background-color: transparent;
  border-radius: 5px;
}

</style>