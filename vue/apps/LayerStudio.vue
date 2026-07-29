<!-- TODO: move this to components -->
<template>
  <a-space
    id="layer-studio"
    direction="vertical"
    style="width: 100%; padding: 4px; padding-top: 20px; height: 100%"
  >
    <!-- HEADER -->
    <a-row type="flex" justify="space-between" align="middle">
      <a-col>
        <h3>Visual Editor</h3>
      </a-col>
      <a-col>
        <a-dropdown trigger="click">
          <a-button type="primary" size="small" @click.prevent
            >Add Layer</a-button
          >
          <template #overlay>
            <a-menu>
              <template v-if="datasources.length > 0">
                <a-menu-item-group
                  v-for="datasource in datasources"
                  :key="datasource.id"
                  :title="datasource.name"
                >
                  <a-menu-item
                    v-for="sourceKey in Object.keys(datasource.sources)"
                    :key="`${datasource.id}::${sourceKey}`"
                    @click="onSelectSource(datasource, sourceKey)"
                  >
                    {{ sourceKey }}
                  </a-menu-item>
                </a-menu-item-group>
              </template>
              <a-menu-item v-else key="no-sources" disabled>
                No sources available
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </a-col>
    </a-row>
    <!----------------------------------->
    <!------------- Layers -------------->
    <!----------------------------------->
    <a-col>
      <a-collapse
        v-if="visualizedLayers.length"
        v-model:activeKey="activeVizLayerKeys"
        :bordered="false"
      >
        <a-collapse-panel
          v-for="(vizLayer, idx) in visualizedLayers"
          :key="idx"
          :header="vizLayer.name"
        >
          <a-row class="layer-style-option-row" style="padding-bottom: 8px">
            Source
            <a-col :span="15">
              {{ vizLayer.sourceRef.name }}
            </a-col>
          </a-row>
          <a-row class="layer-style-option-row" style="padding-bottom: 8px">
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
            style="width: 100%"
          >
            <a-row class="layer-style-option-row">
              Style type
              <a-select
                :value="vizLayer.styledType"
                style="width: 250px"
                :options="VisualizedLayer.StyleTypes[vizLayer.styledFieldType]"
                :status="vizLayer.styledType === undefined ? 'error' : null"
                :placeholder="
                  vizLayer.styledType === undefined
                    ? 'Unsupported type for styling'
                    : ''
                "
                @change="(type) => vizLayer.onSelectStyleType(type)"
                @mouseleave="removeTooltipPopup"
              />
            </a-row>
            <a-row
              v-if="vizLayer.colorPickerColor !== undefined"
              class="layer-style-option-row"
            >
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
                    :style="{ backgroundColor: option.label, height: '100%' }"
                  />
                </a-select-option>
              </a-select>
            </a-row>
            <a-row
              v-if="vizLayer.colorPalette !== undefined"
              class="layer-style-option-row"
            >
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
                      :span="Math.round(24 / option.sample.length)"
                      :style="{
                        backgroundColor: color.startsWith('#')
                          ? color
                          : `#${color}`,
                        height: '35px',
                      }"
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
                  @change="
                    (checkedStatus) =>
                      vizLayer.onToggleShowStroke(checkedStatus)
                  "
                />
              </a-col>
            </a-row>
            <a-row class="layer-style-option-row">
              Show label
              <a-col :span="2">
                <a-switch
                  :checked="vizLayer.showLabel"
                  size="small"
                  @change="
                    (checkedStatus) =>
                      vizLayer.onToggleShowLabels(checkedStatus)
                  "
                />
              </a-col>
            </a-row>
          </a-space>
          <template #extra>
            <a-row>
              <a-tooltip title="Add layer style to favorites">
                <a-button
                  size="small"
                  type="text"
                  @click.stop="onSaveStyleBtnClick(vizLayer)"
                >
                  <component
                    :is="StarOutlined"
                    style="vertical-align: 0.1rem"
                  />
                </a-button>
              </a-tooltip>
              <a-tooltip title="Load layer style from favorites">
                <a-button
                  size="small"
                  type="text"
                  :disabled="savedStyles.length === 0"
                  @click.stop="onLoadSavedStyleBtnClick(vizLayer)"
                >
                  <component
                    :is="FolderOpenOutlined"
                    style="vertical-align: 0.1rem"
                  />
                </a-button>
              </a-tooltip>
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
    <!-- TODO: support group -->
    <!-- Save layer style modal -->
    <a-modal
      v-model:open="showSaveStyleModal"
      title="Add layer style to favorites"
      ok-text="Save"
      :ok-button-props="{ disabled: !styleNameInput }"
      @ok="onConfirmSaveStyle"
      @cancel="onCancelSaveStyleModal"
    >
      <a-form layout="vertical">
        <a-form-item label="Style name">
          <a-input
            v-model:value="styleNameInput"
            placeholder="e.g. Display asset name on map"
          />
        </a-form-item>
      </a-form>
    </a-modal>
    <!-- Load layer style modal -->
    <a-modal
      v-model:open="showLoadStyleModal"
      title="Load layer style from favorites"
      ok-text="Load"
      :ok-button-props="{ disabled: !selectedSavedStyleId }"
      @ok="onConfirmLoadStyle"
      @cancel="onCancelLoadStyleModal"
    >
      <a-select
        v-if="savedStyles.length > 0"
        v-model:value="selectedSavedStyleId"
        style="width: 100%"
        placeholder="Select a saved style"
        :options="savedStyles.map((s) => ({ value: s.id, label: s.name }))"
      />
      <p v-else class="text-only">No saved styles yet.</p>
    </a-modal>
  </a-space>
</template>

<script setup>
import { ref, onMounted, computed, watch, onUnmounted } from "vue";
import { v4 as uuidv4 } from "uuid";
import {
  DeleteOutlined,
  EyeInvisibleOutlined,
  EyeOutlined,
  FolderOpenOutlined,
  StarOutlined,
} from "@ant-design/icons-vue";
import { displayNotification } from "@/utils/notification";
// TODO: organize imports
import {
  getAssetFields,
  generateColorscale,
  setLeafletFeatureStyle,
  LeafletStyler,
} from "@/utils/spatialVisualization";
import { defaultColorScheme } from "@/utils/visualization";
import {
  useVisibleLayers,
  VisibleLayerType,
} from "@/composables/visibleLayers";

const { getLayerType } = useVisibleLayers();

// to prevent stuck popup on UI
const removeTooltipPopup = () => {
  window.jquery(".ui-tooltip-content").parents("div").remove();
};

const props = defineProps({
  // An array of objects with each object contains data to create a DataSource instance (and the corresponding GeoJSON FeatureCollection).
  layerSources: {
    type: Array,
    default: () => [],
  },
});

const datasources = ref([]);

const activeVizLayerKeys = ref([]);

onMounted(async () => {
  console.debug("Initializing Layer Studio component.");
  if (props.layerSources.length > 0) {
    datasources.value = createDatasources(props.layerSources);
  }
});

onUnmounted(() => {
  // TODO: should call ds.dispose() when ESDL is removed from the app.
  // console.debug("Disposing Layer Studio component.");
  // datasources.value.forEach((ds) => ds.dispose());
});

// // TODO: refinement; update on layerSources change and do not format existing data
// watch(
//   () => props.layerSources,
//   (newLayerSources) => {
//     datasources.value = initDatasources(newLayerSources);
//   }
// );

// -------------------------------------------------- //
// -------------- Save/Load layer style ------------- //
// -------------------------------------------------- //

const savedStyles = ref([]);

const showSaveStyleModal = ref(false);
const styleNameInput = ref("");
const vizLayerToSaveStyle = ref(undefined);

const showLoadStyleModal = ref(false);
const selectedSavedStyleId = ref(undefined);
const vizLayerToLoadStyle = ref(undefined);

const onSaveStyleBtnClick = (vizLayer) => {
  vizLayerToSaveStyle.value = vizLayer;
  styleNameInput.value = "";
  showSaveStyleModal.value = true;
};

const onLoadSavedStyleBtnClick = (vizLayer) => {
  vizLayerToLoadStyle.value = vizLayer;
  selectedSavedStyleId.value = undefined;
  showLoadStyleModal.value = true;
};

const resetSaveStyleModalInputs = () => {
  vizLayerToSaveStyle.value = undefined;
  styleNameInput.value = "";
};

const onCancelSaveStyleModal = () => {
  resetSaveStyleModalInputs();
};

/**
 * TODO: connect with MongoDB settings
 * Snapshot the target layer's current `paint` and add it to the savedStyles list.
 */
const onConfirmSaveStyle = () => {
  if (!styleNameInput.value || !vizLayerToSaveStyle.value) {
    return;
  }

  const styleName = styleNameInput.value;

  savedStyles.value.push({
    id: uuidv4(),
    name: styleName,
    paint: JSON.parse(JSON.stringify(vizLayerToSaveStyle.value.paint)),
  });

  displayNotification(
    "success",
    `Layer style '${styleName}' saved to favorites.`,
  );

  resetSaveStyleModalInputs();
  showSaveStyleModal.value = false;
};

const resetLoadStyleModalInputs = () => {
  vizLayerToLoadStyle.value = undefined;
  selectedSavedStyleId.value = undefined;
};

const onCancelLoadStyleModal = () => {
  resetLoadStyleModalInputs();
};

/**
 * TODO: review & show notification on fallback
 *
 * Applies a saved `paint` config onto the target vizLayer. Field references (color/size/label)
 * that don't exist on the target layer (e.g. the style was saved from a different sourceKey/asset
 * type) are treated as untrusted and dropped, falling back to a safe default, before applyStyle()
 * is called.
 *
 * @param {VisualizedLayer} vizLayer
 * @param {Object} savedPaint
 */
const applySavedStyleToVizLayer = (vizLayer, savedPaint) => {
  const paint = JSON.parse(JSON.stringify(savedPaint));
  const fieldNames = vizLayer.fieldOptions.map((f) => f.value);
  const numericFieldNames = vizLayer.numericFieldOptions.map((f) => f.value);

  if (paint.color.field !== undefined) {
    const validFieldNames =
      paint.color.mode === "gradient" ? numericFieldNames : fieldNames;
    if (!validFieldNames.includes(paint.color.field)) {
      paint.color.field = undefined;
      paint.color.mode = "single";
    }
  }
  if (
    paint.size.field !== undefined &&
    !numericFieldNames.includes(paint.size.field)
  ) {
    paint.size.field = undefined;
    paint.size.mode = "fixed";
  }
  if (
    paint.label.field !== undefined &&
    !fieldNames.includes(paint.label.field)
  ) {
    paint.label.field = undefined;
    paint.label.visible = false;
  }

  vizLayer.paint = paint;
  vizLayer.applyStyle();
};

// TODO: retrieve savedStyles from MongoDB settings
const onConfirmLoadStyle = () => {
  if (!selectedSavedStyleId.value || !vizLayerToLoadStyle.value) {
    return;
  }

  const savedStyle = savedStyles.value.find(
    (s) => s.id === selectedSavedStyleId.value,
  );
  if (savedStyle) {
    applySavedStyleToVizLayer(vizLayerToLoadStyle.value, savedStyle.paint);
    displayNotification("success", `Layer style '${savedStyle.name}' applied.`);
  }

  resetLoadStyleModalInputs();
  showLoadStyleModal.value = false;
};

// -------------------------------------------------- //
// --------  Data source and Visualized Layer  ------ //
// -------------------------------------------------- //

/**
 * Flatten all datasources' vizLayers (VisualizedLayer instances) into a single-level list.
 */
const visualizedLayers = computed(() => {
  return datasources.value
    .filter((ds) => ds.vizLayers !== undefined)
    .map((ds) => ds.vizLayers)
    .flat();
});

/**
 * Handle selection of a source (sourceKey) from the Add Layer dropdown for the
 * given datasource, loading it as a GeoJSON source.
 *
 * @param {DataSource} datasource
 * @param {string} sourceKey
 */
const onSelectSource = async (datasource, sourceKey) => {
  if (!datasource.geoJsonSources[sourceKey]) {
    await datasource.addAsGeoJsonSource(sourceKey);
  }

  datasource.onAddLayerToMap(sourceKey);
};

/**
 * Maps raw layer sources from the `layerSources` prop into typed DataSource instances.
 * Currently only ESDL layer sources are supported; unrecognised source types are skipped.
 *
 * @param {Array} layerSources - The raw layer source objects passed via the `layerSources` prop.
 * @returns {DataSource[]} Array of initialised DataSource instances ready to be used by the component.
 */
const createDatasources = (layerSources) => {
  let datasources = [];
  layerSources.forEach((source) => {
    if (getLayerType(source) === VisibleLayerType.ESDL) {
      const esId = source.es.id;
      const esdlTitle = source.es.title;
      const esdlSource = new EsdlLayerSource(esId, esdlTitle);
      datasources.push(esdlSource);
    }
  });
  return datasources;
};

/**
 * Enum of supported data-source types.
 * Only ESDL type is supported at the moment.
 */
const DataSourceType = Object.freeze({
  ESDL: "ESDL",
});

/**
 * Base class for all data sources.
 */
class DataSource {
  /**
   * @property {string} id - The unique identifier of the data source.
   * @property {string} name - The name of the data source.
   * @property {DataSourceType} type - The type of the data source (e.g., ESDL).
   */
  constructor(id, name, type) {
    this.id = id;
    this.name = name;
    this.type = type;

    // sources is a map of sourceKey to array of raw layer features
    // which can contain incomplete attribute data and not GeoJSON ready.
    this.sources = {};
    // geoJsonSources is a map of sourceKey to GeoJSON FeatureCollection
    this.geoJsonSources = {};
    this.vizLayers = [];
    this.loading = false;

    // Take the global Leaflet map instance
    this._map = map;
    this.mapLayerGroup = L.featureGroup().addTo(this._map);
  }

  /**
   * Subclasses must implement this method to convert raw features
   * under `sourceKey` into an enriched GeoJSON FeatureCollection and store the
   * result in `this.geoJsonSources[sourceKey]`.
   *
   * @param {string} sourceKey
   * @returns {Promise<void>}
   */
  async addAsGeoJsonSource(sourceKey) {
    throw new Error(
      `addAsGeoJsonSource() not implemented for source type '${this.type}'`,
    );
  }

  /**
   * Creates a new VisualizedLayer from the pre-loaded GeoJSON features for
   * `sourceKey` and registers it in `this.vizLayers`. The layer is added to
   * the this._map as a side-effect of `VisualizedLayer` construction.
   *
   * @param {string} sourceKey
   */
  onAddLayerToMap(sourceKey) {
    const layerName = this._createUniqueVizLayerName(sourceKey);
    if (!this.geoJsonSources[sourceKey]) {
      throw new Error(`GeoJSON source for '${sourceKey}' not found.`);
    }
    const features = this.geoJsonSources[sourceKey];
    const vizLayer = new VisualizedLayer(this, layerName, features);
    this.vizLayers.push(vizLayer);
  }

  dispose() {
    this.vizLayers.forEach((vl) => vl.removeLayerFromMap(vl.layer));
    this.mapLayerGroup?.remove();
    this.vizLayers = [];
  }

  _createUniqueVizLayerName = (name) => {
    let vizLayerName = name;
    if (this.vizLayers.find((l) => l.name === name)) {
      const suffixNr = this.vizLayers.filter((l) =>
        l.name.includes(name),
      ).length;
      vizLayerName = `${vizLayerName} ${suffixNr + 1}`;
    }
    return vizLayerName;
  };
}

/**
 * Data source class for ESDL layers, extending the base DataSource class.
 * It fetches and enriches ESDL asset features with attribute values from the backend.
 */
class EsdlLayerSource extends DataSource {
  constructor(id, name) {
    super(id, name, DataSourceType.ESDL);

    this._getEsdlAssetLayers();
  }

  /**
   * TODO: show loading icon
   * Enrich the asset features of the given sourceKey with attribute (field) values returned
   * from the backend and store them as a GeoJSON FeatureCollection in `this.geoJsonSources`.
   *
   * @param {string} sourceKey ESDL asset type
   * @override
   */
  async addAsGeoJsonSource(sourceKey) {
    const layerFeatures = this.sources[sourceKey];
    const geoJsonFeaturePromises = layerFeatures.map(async (f) => {
      const g = f.toGeoJSON();

      const assetId = f.id;
      // TODO: this method is ESDL specific, but it could be made more generic if needed
      // TODO: support references; this is not very efficient?
      const fields = await getAssetFields(this.id, assetId);
      g["_fields"] = fields["attributes"];

      const properties = {};
      // Direct asset attributes
      fields.attributes.forEach((attr) => {
        properties[attr.name] = attr.value;
      });
      // Reference sub-attributes — namespaced as "refName.attrName" to avoid collisions
      fields.references.forEach((ref) => {
        ref.attributes.forEach((attr) => {
          properties[`${ref.name}.${attr.name}`] = attr.value;
        });
      });
      g.properties = properties;

      return g;
    });

    const geoJsonFeatureCollection = await Promise.all(geoJsonFeaturePromises);

    this.geoJsonSources = {
      ...(this.geoJsonSources || {}),
      [sourceKey]: geoJsonFeatureCollection,
    };
  }

  /**
   * Get ESDL Leaflet FeatureGroup layer by energy system ID and layer name.
   *
   * @param {string} esId Energy system ID
   * @param {string} layerName Layer name defined in multi_esdl.js
   * @returns {Object} Leaflet FeatureGroup layer object.
   */
  _getEsdlFeatureGroupLayer(esId, layerName) {
    return window.get_layers(esId, layerName);
  }

  /**
   * Get all asset layers of the ESDL model as a map of layer type to Leaflet layers.
   */
  async _getEsdlAssetLayers() {
    const esdlLayer = this._getEsdlFeatureGroupLayer(this.id, "esdl_layer");
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
}

/**
 * Class representing a visualized layer on the map, with styling and interactivity.
 */
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
    boolean: [{ value: "categoricalColor", label: "Categorical Color" }],
    string: [
      { value: "singleColor", label: "Single Color" },
      { value: "categoricalColor", label: "Categorical Color" },
    ],
    number: [
      { value: "size", label: "Size" },
      { value: "gradientColor", label: "Gradient Color" },
      { value: "colorAndSize", label: "Color and Size" },
    ],
  });

  static colorPickerPalette = defaultColorScheme.map((c) => ({
    value: c,
    label: c,
  }));

  static sampleNum = 12;
  static colorPalettes = {
    Categorical: [
      {
        label: "Default",
        value: "Default",
        sample: defaultColorScheme.slice(0, VisualizedLayer.sampleNum),
      },
      {
        label: "Qualitative",
        value: "Qualitative",
        sample: window.palette("mpn65", VisualizedLayer.sampleNum),
      },
    ],
    Continuous: [
      {
        label: "Diverging",
        value: "Diverging",
        sample: window.palette("tol-dv", VisualizedLayer.sampleNum),
      },
      {
        label: "Sequential",
        value: "Sequential",
        sample: window.palette("tol-sq", VisualizedLayer.sampleNum),
      },
      {
        label: "Rainbow",
        value: "Rainbow",
        sample: window.palette("tol-rainbow", VisualizedLayer.sampleNum),
      },
    ],
  };

  // TODO: remove and reuse the one from setLeafletFeatureStyle
  static setFeatureStyle(
    geometryType,
    color = "#1f78b4",
    opacity = 1,
    radius = 5,
    weight = 2,
    stroke = false,
  ) {
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

  static customMapPane = "vizLayerPane";

  constructor(sourceRef, name, features) {
    this.sourceRef = sourceRef;
    this.name = name;
    this.features = features;

    this._initVizLayerPane();

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

  createGeoJsonLayer(features) {
    const layer = L.geoJSON(features, {
      style: function (feature) {
        return VisualizedLayer.setFeatureStyle(feature.geometry.type);
      },
      pointToLayer: function (feature, latlng) {
        return L.circleMarker(
          latlng,
          VisualizedLayer.setFeatureStyle(feature.geometry.type),
        );
      },
    });

    // Add the layer to the custom pane after initialization.
    layer.eachLayer((featureLayer) => {
      featureLayer.options.pane = VisualizedLayer.customMapPane;
    });

    return layer;
  }

  removeLayerFromMap(layer) {
    if (this.sourceRef.mapLayerGroup.hasLayer(layer)) {
      // Remove existing tooltips to avoid them lingering on the map.
      layer.eachLayer((featureLayer) => {
        featureLayer.closeTooltip();
        featureLayer.unbindTooltip();
      });
      this.sourceRef.mapLayerGroup.removeLayer(layer);
    }
  }

  addLayerToMap(layer) {
    this.sourceRef.mapLayerGroup.addLayer(layer);
  }

  redrawLayerOnFeaturesUpdate(updatedFeatures) {
    this.features = updatedFeatures;
    this.removeLayerFromMap(this.layer);
    this.layer = this.createGeoJsonLayer(this.features);
    this.addLayerToMap(this.layer);
    this.styleLayer(this.styledType);
  }

  toggleLayer(event) {
    event.stopPropagation();
    if (this.visible) {
      this.sourceRef.mapLayerGroup.removeLayer(this.layer);
      this.visible = false;
    } else {
      this.sourceRef.mapLayerGroup.addLayer(this.layer);
      this.visible = true;
    }
  }

  removeLayer(event) {
    event.stopPropagation();
    if (this.sourceRef) {
      this.sourceRef.vizLayers = this.sourceRef.vizLayers.filter(
        (layer) => layer.id !== this.id,
      );
      this.removeLayerFromMap(this.layer);
    }
  }

  onSelectStyledField(selectedField) {
    this.styledField = selectedField;
    this.styledFieldType = this.fieldOptions.find(
      (f) => f.value === selectedField,
    ).type;

    let defaultStyleType = undefined;
    if (
      Object.keys(VisualizedLayer.StyleTypes).includes(this.styledFieldType)
    ) {
      // Default to the first StyleType when the styledField is updated.
      defaultStyleType =
        VisualizedLayer.StyleTypes[this.styledFieldType][0].value;
    } else {
      console.warn(
        `No supported style type for ${this.styledField} [${this.styledFieldType}]`,
      );
    }
    this._setStyleType(defaultStyleType);
  }

  onSelectStyleType (selectedStyleType) {
    this._setStyleType(selectedStyleType);
  }

  onSizeChange(size) {
    this.markerSizeValue = size;
    this.styleLayer(this.styledType);
  }

  onSelectColor(color) {
    this.colorPickerColor = color;
    this.styleLayer(this.styledType);
  }

  onSelectPalette(palette) {
    this.colorPalette = palette;
    this.styleLayer(this.styledType);
  }

  onOpacityChange(opacity) {
    this.opacity = opacity;
    this.styleLayer(this.styledType);
  }

  onToggleShowStroke(checkedStatus) {
    this.showStroke = checkedStatus;
    this.styleLayer(this.styledType);
  }

  onToggleShowLabels(checkedStatus) {
    this.showLabel = checkedStatus;
    this.styleLayer(this.styledType);
  }

  /**
   * Style layer according to the given styleType and current style options.
   *
   * @param {string|undefined} styleType The style type to be applied.
   */
  styleLayer(styleType) {
    switch (styleType) {
      default:
      case "singleColor":
        this._styleMarkerWithSingleColor(this.colorPickerColor);
        this._styleMarkerSize(this.markerSizeValue);
        break;
      case "categoricalColor":
        this._styleMarkerColorOnCategorizedFieldValue(
          this.styledField,
          this.colorPalette,
        );
        this._styleMarkerSize(this.markerSizeValue);
        break;
      case "size":
        this._styleMarkerWithSingleColor(this.colorPickerColor);
        this._styleMarkerSizeOnNumericalFieldValue(this.styledField);
        break;
      case "gradientColor":
        this._styleMarkerColorOnNumericalFieldValue(
          this.styledField,
          this.colorPalette,
        );
        this._styleMarkerSize(this.markerSizeValue);
        break;
      case "colorAndSize":
        this._styleMarkerColorOnNumericalFieldValue(
          this.styledField,
          this.colorPalette,
        );
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

  _styleMarkerWithSingleColor(color) {
    this.layer.setStyle({
      fillColor: color,
      color: color,
    });
  }

  _styleMarkerSize(size) {
    const isPolyline = this.features[0].geometry.type.includes("LineString");
    this.layer.setStyle({
      radius: size,
      weight: isPolyline
        ? size * VisualizedLayer.radiusToWeight
        : VisualizedLayer.initStrokeWeight,
    });
  }

  _styleMarkerOpacity(opacity) {
    this.layer.setStyle({
      opacity: opacity,
      fillOpacity: opacity,
    });
  }

  // Should only be applied to Point or Polygon feature
  _showHideMarkerStroke(showStroke) {
    const isPolyline = this.features[0].geometry.type.includes("LineString");
    if (!isPolyline) {
      this.layer.setStyle({
        stroke: showStroke,
        weight: VisualizedLayer.initStrokeWeight,
        color: "#2e4053",
      });
    }
  }

  /**
   * Show or hide the selected field value from features as tooltip labels.
   */
  _showHideFeatureLabels(selectedField, showLabel = false) {
    this.layer.eachLayer((featureLayer) => {
      // Clean up existing tooltip
      featureLayer.closeTooltip();
      featureLayer.unbindTooltip();

      if (
        showLabel &&
        featureLayer.feature &&
        featureLayer.feature.properties
      ) {
        const fieldValue = featureLayer.feature.properties[selectedField];
        const popupContent = fieldValue !== null ? `${fieldValue}` : "No data";
        featureLayer
          .bindTooltip(popupContent, {
            permanent: true,
            direction: "top",
            opacity: 0.8,
          })
          .openTooltip();
      }
    });
  }

  _styleMarkerColorOnCategorizedFieldValue(styledField, palette) {
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
          color: markerColor,
        };
      });
    } else {
      const markerColor = generateColorscale(palette, 1);
      this._styleMarkerWithSingleColor(markerColor[0]);
    }
  }

  _styleMarkerColorOnNumericalFieldValue(styledField, palette) {
    const fieldUniqueValues = this._getFieldUniqueValues(styledField);

    // TODO: how should this be defined?
    const colorNum = 25;
    const colorscale = generateColorscale(palette, colorNum + 1);

    if (fieldUniqueValues.length > 1) {
      const min = Math.min(...fieldUniqueValues);
      const max = Math.max(...fieldUniqueValues);

      this.layer.setStyle((feature) => {
        const fieldValue = feature.properties[styledField];
        const normalizedValue =
          (Math.log1p(fieldValue) - Math.log1p(min)) /
          (Math.log1p(max) - Math.log1p(min));
        const colorIndex = parseInt(normalizedValue * colorNum);
        const markerColor = colorscale[colorIndex];
        return {
          fillColor: markerColor,
          color: markerColor,
        };
      });
    } else {
      const markerColor = generateColorscale(palette, 1);
      this._styleMarkerWithSingleColor(markerColor[0]);
    }
  }

  _styleMarkerSizeOnNumericalFieldValue(styledField) {
    const fieldUniqueValues = this._getFieldUniqueValues(styledField);
    if (fieldUniqueValues.length > 1) {
      const min = Math.min(...fieldUniqueValues);
      const max = Math.max(...fieldUniqueValues);

      const sizeMin = this.markerSizeValue;
      const sizeMax = sizeMin * 6;

      this.layer.setStyle((feature) => {
        const normalizedValue =
          (Math.log1p(feature.properties[styledField]) - Math.log1p(min)) /
          (Math.log1p(max) - Math.log1p(min));
        const size = normalizedValue * (sizeMax - sizeMin) + sizeMin;
        const isPolyline = feature.geometry.type.includes("LineString");
        return {
          radius: size,
          weight: isPolyline
            ? size * VisualizedLayer.radiusToWeight
            : VisualizedLayer.initStrokeWeight,
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
  _setStyleType(styleType) {
    this.styledType = styleType;

    this._resetStyleOptions();

    if (
      styleType === undefined ||
      styleType === "singleColor" ||
      styleType === "size"
    ) {
      this.colorPickerColor = "#1f78b4";
    } else {
      if (["string", "boolean"].includes(this.styledFieldType)) {
        this.displayedPalettes = VisualizedLayer.colorPalettes["Categorical"];
        this.colorPalette = this.displayedPalettes[0].value;
      } else if (this.styledFieldType === "number") {
        this.displayedPalettes = VisualizedLayer.colorPalettes["Continuous"];
        this.colorPalette = this.displayedPalettes[0].value;
      } else {
        console.warn(
          `No supported color palette for styledFieldType: ${this.styledFieldType}`,
        );
      }
    }

    this.styleLayer(styleType);
  }

  _resetStyleOptions() {
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
  _initVizLayerPane() {
    if (map.getPane(VisualizedLayer.customMapPane) === undefined) {
      const vizLayerPane = map.createPane(VisualizedLayer.customMapPane);
      vizLayerPane.style.zIndex = 640; // Keep it below the tooltippane (650)
    }
  }

  _listLayerFieldOptions() {
    const options = this.features[0]._fields.map((f) => ({
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
  _getFieldUniqueValues(fieldName) {
    const fieldVals = this.features
      .map((f) => f.properties[fieldName])
      .filter((element) => element !== null);
    return [...new Set(fieldVals)];
  }
}
</script>

<style scoped>
.layer-style-option-row {
  justify-content: space-between;
}

.style-section-divider {
  margin: 8px 0 6px 0;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}
</style>
