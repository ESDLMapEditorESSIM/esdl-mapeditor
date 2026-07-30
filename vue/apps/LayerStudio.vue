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
          <a-col class="layer-info-row">
            <a-typography-text strong>
              Source
            </a-typography-text>
            <a-col :span="15">
              {{ vizLayer.sourceRef.name }}
            </a-col>
          </a-col>
          <a-col class="layer-info-row">
            <a-typography-text strong>
              Field
            </a-typography-text>
            <a-select
              :value="vizLayer.style.field"
              :options="vizLayer.fieldOptions"
              style="width: 100%"
              @change="(field) => vizLayer.onSelectField(field)"
              @mouseleave="removeTooltipPopup"
            />
          </a-col>
          <a-space
            v-if="vizLayer.style.field !== undefined"
            direction="vertical"
            style="width: 100%"
          >
            <a-col class="layer-info-row">
              <a-typography-text strong>
                Style options
              </a-typography-text>
              <a-row>
                <a-segmented
                  v-model:value="vizLayer.style.styleType"
                  :options="VisualizedLayer.StyleTypes[vizLayer.style.fieldType]"
                  style="width: 100%"
                  size="small"
                  block
                  @change="(type) => vizLayer.onSelectStyleType(type)"
                >
                  <template #label="{ payload = {} }">
                    <div style="padding: 4px 4px">
                      <component
                        :is="payload.icon"
                        style="vertical-align: 0.05rem"
                      />
                      <div>{{ payload.label }}</div>
                    </div>
                  </template>
                </a-segmented>
              </a-row>
            </a-col>
            <a-col 
              v-if="vizLayer.style.paint.color.mode === 'fixed'"
              class="layer-info-row"
            >
              <a-typography-text strong>
                Color
              </a-typography-text>
              <input
                type="color"
                :value="vizLayer.style.paint.color.value"
                @input="(e) => vizLayer.onSelectColor(e.target.value)"
                style="width: 100%; height: 35px; cursor: pointer; border: none;"
              />
            </a-col>
            <a-col 
              v-if="vizLayer.style.paint.color.mode !== 'fixed'"
              class="layer-info-row"
            >
              <a-typography-text strong>
                Color palette
              </a-typography-text>
              <a-select
                :value="vizLayer.style.paint.color.palette"
                style="width: 100%"
                @change="(palette) => vizLayer.onSelectPalette(palette)"
              >
                <a-select-option
                  v-for="option in VisualizedLayer.colorPalettes[vizLayer.style.paint.color.mode]"
                  :key="option.value"
                  :value="option.value"
                >
                  <div
                    v-if="vizLayer.style.paint.color.mode === ColorMode.GRADIENT"
                    :style="{ background: toCssGradient(option.sample), height: '35px', width: '100%', borderRadius: '2px' }"
                  />
                  <a-row v-else>
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
            </a-col>
            <a-col class="layer-info-row">
              <a-typography-text strong>
                Size
              </a-typography-text>
              <a-slider
                :value="vizLayer.style.paint.symbol.size.value"
                :min="vizLayer.style.paint.symbol.size.minSize"
                :max="vizLayer.style.paint.symbol.size.maxSize"
                :step="1"
                @change="(size) => vizLayer.onSizeChange(size)"
              />
            </a-col>
            <a-col class="layer-info-row">
              <a-typography-text strong>
                Opacity
              </a-typography-text>
              <a-slider
                :value="vizLayer.style.paint.opacity"
                :min="0"
                :max="1"
                :step="0.01"
                @change="(opacity) => vizLayer.onOpacityChange(opacity)"
              />
            </a-col>
            <a-row
              v-if="!vizLayer.features[0].geometry.type.includes('LineString')"
              class="layer-style-option-row"
            >
              <a-typography-text strong>
                Show outline
              </a-typography-text>
              <a-col :span="2">
                <a-switch
                  :checked="vizLayer.style.paint.stroke.visible"
                  size="small"
                  @change="
                    (visible) =>
                      vizLayer.onToggleShowStroke(visible)
                  "
                />
              </a-col>
            </a-row>
            <a-row class="layer-style-option-row">
              <a-typography-text strong>
                Show label
              </a-typography-text>
              <a-col :span="2">
                <a-switch
                  :checked="vizLayer.style.paint.label.visible"
                  size="small"
                  @change="
                    (visible) =>
                      vizLayer.onToggleShowLabels(visible)
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
  BgColorsOutlined,
  AppstoreOutlined,
  ExpandAltOutlined,
  BarChartOutlined,
  DotChartOutlined,
} from "@ant-design/icons-vue";
import { displayNotification } from "@/utils/notification";
import {
  getAssetFields,
  generateColorscale,
  setLeafletFeatureStyle,
  FieldType,
  StyleType,
  ColorMode,
  SizeMode,
  PaletteName,
} from "@/utils/spatialVisualization";
import {
  useVisibleLayers,
  VisibleLayerType,
} from "@/composables/visibleLayers";

const { getLayerType } = useVisibleLayers();

const toCssGradient = (colors) => {
  const stops = colors.map(c => c.startsWith('#') ? c : `#${c}`).join(', ');
  return `linear-gradient(to right, ${stops})`;
};

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
  // NICE TO HAVE: custom icons
  // Supported style types
  static StyleTypes = Object.freeze({
    [FieldType.BOOLEAN]: [{
      value: StyleType.CATEGORICAL_COLOR,
      payload: {
        label: "Categorical Color",
        icon: AppstoreOutlined,
      }
    }],
    [FieldType.STRING]: [
      {
        value: StyleType.SINGLE_COLOR,
        payload: {
          label: "Single Color",
          icon: BgColorsOutlined,
        }
      },
      {
        value: StyleType.CATEGORICAL_COLOR,
        payload: {
          label: "Categorical Color",
          icon: AppstoreOutlined,
        }
      },
    ],
    [FieldType.NUMBER]: [
      {
        value: StyleType.SIZE,
        payload: {
          label: "Size",
          icon: ExpandAltOutlined,
        }
      },
      {
        value: StyleType.GRADIENT_COLOR,
        payload: {
          label: "Gradient Color",
          icon: BarChartOutlined,
        }
      },
      {
        value: StyleType.COLOR_AND_SIZE,
        payload: {
          label: "Color and Size",
          icon: DotChartOutlined,
        }
      },
    ],
  });

  static colorPalettes = {
    [ColorMode.CATEGORICAL]: [
      {
        label: "Default",
        value: PaletteName.DEFAULT,
        sample: generateColorscale(PaletteName.DEFAULT),
      },
      {
        label: "Qualitative",
        value: PaletteName.QUALITATIVE,
        sample: generateColorscale(PaletteName.QUALITATIVE),
      },
    ],
    [ColorMode.GRADIENT]: [
      {
        label: "Diverging",
        value: PaletteName.DIVERGING,
        sample: generateColorscale(PaletteName.DIVERGING),
      },
      {
        label: "Sequential",
        value: PaletteName.SEQUENTIAL,
        sample: generateColorscale(PaletteName.SEQUENTIAL),
      },
      {
        label: "Rainbow",
        value: PaletteName.RAINBOW,
        sample: generateColorscale(PaletteName.RAINBOW),
      },
    ],
  };

  static customMapPane = "vizLayerPane";

  // a constant factor to scale between marker radius and weight.
  static radiusToWeight = 0.4;

  static defaultStyle = {
    field: undefined,
    fieldType: undefined, // undefined || FieldType Enum
    styleType: undefined, // undefined || StyleType Enum
    paint: {
      color: {
        mode: ColorMode.FIXED, // ColorMode Enum
        value: "#1f78b4",
        field: undefined,
        palette: undefined,
        stops: [],
      },
      symbol: {
        size: {
          mode: SizeMode.FIXED, // SizeMode Enum
          field: undefined,
          value: 5,
          minSize: 1,
          maxSize: 10,
        }
      },
      stroke: {
        visible: false,
        color: "#000000",
        weight: 2,
        opacity: 1.0,
      },
      opacity: 1.0,
      label: {
        visible: false,
      },
    },
  };

  constructor(sourceRef, name, features) {
    this.sourceRef = sourceRef;
    this.name = name;
    this.features = features;

    this._initVizLayerPane();

    this.id = `${sourceRef.id}-${name}`;
    this.layer = this.styleGeoJsonFeatures(this.features);
    this.visible = true;
    this.fieldOptions = this._listLayerFieldOptions();

    this.style = JSON.parse(JSON.stringify(VisualizedLayer.defaultStyle));

    this.addLayerToMap(this.layer);
  }

  styleGeoJsonFeatures(features) {
    const layer = L.geoJSON(features, {
      style: function (feature) {
        return setLeafletFeatureStyle(feature.geometry.type);
      },
      pointToLayer: function (feature, latlng) {
        return L.circleMarker(
          latlng,
          setLeafletFeatureStyle(feature.geometry.type),
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
    this.layer = this.styleGeoJsonFeatures(this.features);
    this.addLayerToMap(this.layer);
    this.applyStyle();
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

  // ---------------------------------------- //
  // ----------- Event handlers ------------- //
  // ---------------------------------------- //

  onSelectField (field) {
    this.style.field = field;
    this.style.fieldType = this.fieldOptions.find(
      (f) => f.value === field,
    ).type;

    this.preSelectStyleTypeOnFieldSelection();
    this.applyStyle();
  }

  preSelectStyleTypeOnFieldSelection() {
    if (Object.keys(VisualizedLayer.StyleTypes).includes(this.style.fieldType)) {
      this.style.styleType = VisualizedLayer.StyleTypes[this.style.fieldType][0].value;
      this.preSelectColorOnStyleTypeChange();
    } else {
      console.warn(
        `No supported style type for ${this.style.field} [${this.style.fieldType}]`,
      );
    }
  }

  onSelectStyleType (type) {
    this.style.styleType = type;

    this.preSelectColorOnStyleTypeChange();
    this.applyStyle();
  }

  preSelectColorOnStyleTypeChange() {
    if (
      this.style.styleType === StyleType.SINGLE_COLOR ||
      this.style.styleType === StyleType.SIZE
    ) {
      this.style.paint.color.value = VisualizedLayer.defaultStyle.paint.color.value;
    } else if (
      this.style.styleType === StyleType.CATEGORICAL_COLOR ||
      this.style.styleType === StyleType.GRADIENT_COLOR ||
      this.style.styleType === StyleType.COLOR_AND_SIZE
    ) {
      if (this.style.fieldType === FieldType.STRING || this.style.fieldType === FieldType.BOOLEAN) {
        this.style.paint.color.palette = VisualizedLayer.colorPalettes[ColorMode.CATEGORICAL][0].value;
      } else if (this.style.fieldType === FieldType.NUMBER) {
        this.style.paint.color.palette = VisualizedLayer.colorPalettes[ColorMode.GRADIENT][0].value;
      }
    }
  }

  onSelectColor(color) {
    this.style.paint.color.value = color;
    this.applyStyle();
  }

  onSelectPalette(palette) {
    this.style.paint.color.palette = palette;
    this.applyStyle();
  }

  onSizeChange(size) {
    this.style.paint.symbol.size.value = size;
    this.applyStyle();
  }

  onOpacityChange(opacity) {
    this.style.paint.opacity = opacity;
    this.applyStyle();
  }

  onToggleShowStroke(visible) {
    this.style.paint.stroke.visible = visible;
    this.applyStyle();
  }

  onToggleShowLabels(visible) {
    this.style.paint.label.visible = visible;
    this.applyStyle();
  }

  /**
   * Builds and returns a new style object derived from the current `this.style` state.
   * It maps `fieldType` and `styleType` to derive `paint.color.mode` and
   *   `paint.symbol.size.mode` values.
   *
   * @returns {Object} A fresh style object.
   */
  _updateStyle() {
    // Start from a safe default base.
    const updated = JSON.parse(JSON.stringify(VisualizedLayer.defaultStyle));

    // Carry over the field selection.
    updated.field = this.style.field;
    updated.fieldType = this.style.fieldType;
    updated.styleType = this.style.styleType;

    // Derive paint modes from fieldType + styleType.
    const { fieldType } = updated;
    if (fieldType === FieldType.BOOLEAN || fieldType === FieldType.STRING) {
      updated.paint.color.mode = updated.styleType === StyleType.CATEGORICAL_COLOR ? ColorMode.CATEGORICAL : ColorMode.FIXED;
      updated.paint.symbol.size.mode = SizeMode.FIXED;
    } else if (fieldType === FieldType.NUMBER) {
      if (updated.styleType === StyleType.SIZE) {
        updated.paint.color.mode = ColorMode.FIXED;
        updated.paint.symbol.size.mode = SizeMode.GRADUATED;
      } else if (updated.styleType === StyleType.GRADIENT_COLOR) {
        updated.paint.color.mode = ColorMode.GRADIENT;
        updated.paint.symbol.size.mode = SizeMode.FIXED;
      } else if (updated.styleType === StyleType.COLOR_AND_SIZE) {
        updated.paint.color.mode = ColorMode.GRADIENT;
        updated.paint.symbol.size.mode = SizeMode.GRADUATED;
      }
    }

    // Preserve explicit user-configured paint values from the previous style.
    updated.paint.color.value = this.style.paint.color.value;
    updated.paint.color.palette = this.style.paint.color.palette;
    updated.paint.symbol.size.value = this.style.paint.symbol.size.value;
    updated.paint.opacity = this.style.paint.opacity;
    updated.paint.stroke = { ...this.style.paint.stroke };
    updated.paint.label = { ...this.style.paint.label };

    return updated;
  }

  applyStyle() {
    this.style = this._updateStyle();

    const { paint, field } = this.style;

    // Apply color
    if (paint.color.mode === ColorMode.FIXED) {
      this._styleMarkerWithSingleColor(paint.color.value);
    } else if (paint.color.mode === ColorMode.CATEGORICAL) {
      this._styleMarkerColorOnCategorizedFieldValue(field, paint.color.palette);
    } else if (paint.color.mode === ColorMode.GRADIENT) {
      this._styleMarkerColorOnNumericalFieldValue(field, paint.color.palette);
    }

    // Apply size
    if (paint.symbol.size.mode === SizeMode.FIXED) {
      this._styleMarkerSize(paint.symbol.size.value, paint.stroke.weight);
    } else if (paint.symbol.size.mode === SizeMode.GRADUATED) {
      this._styleMarkerSizeOnNumericalFieldValue(field, paint.symbol.size.value, paint.stroke.weight);
    }

    // Apply opacity, stroke, labels
    this._styleMarkerOpacity(paint.opacity);
    this._showHideMarkerStroke(paint.stroke);
    this._showHideFeatureLabels(field, paint.label.visible);
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

  _styleMarkerSize(size, strokeWeight) {
    const isPolyline = this.features[0].geometry.type.includes("LineString");
    this.layer.setStyle({
      radius: size,
      weight: isPolyline ? size * VisualizedLayer.radiusToWeight : strokeWeight
    });
  }

  _styleMarkerOpacity(opacity) {
    this.layer.setStyle({
      opacity: opacity,
      fillOpacity: opacity,
    });
  }

  /** Should only be applied to Point or Polygon features. */
  _showHideMarkerStroke(stroke) {
    const isPolyline = this.features[0].geometry.type.includes("LineString");
    if (!isPolyline) {
      this.layer.setStyle({
        stroke: stroke.visible,
        weight: stroke.weight,
        color: stroke.color,
      });
    }
  }

  _showHideFeatureLabels(selectedField, showLabel = false) {
    this.layer.eachLayer((featureLayer) => {
      featureLayer.closeTooltip();
      featureLayer.unbindTooltip();

      if (showLabel && featureLayer.feature?.properties) {
        const fieldValue = featureLayer.feature.properties[selectedField];
        const popupContent = fieldValue !== null ? `${fieldValue}` : "No data";
        featureLayer
          .bindTooltip(popupContent, { permanent: true, direction: "top", opacity: 0.8 })
          .openTooltip();
      }
    });
  }

  _styleMarkerColorOnCategorizedFieldValue(field, palette) {
    const fieldUniqueValues = this._getFieldUniqueValues(field);
    if (fieldUniqueValues.length) {
      const colorscale = generateColorscale(palette, fieldUniqueValues.length);
      this.layer.setStyle((feature) => {
        const idx = fieldUniqueValues.findIndex((val) => val === feature.properties[field]);
        const markerColor = colorscale[idx % colorscale.length];
        return { fillColor: markerColor, color: markerColor };
      });
    } else {
      this._styleMarkerWithSingleColor(generateColorscale(palette, 1)[0]);
    }
  }

  _styleMarkerColorOnNumericalFieldValue(field, palette) {
    const fieldUniqueValues = this._getFieldUniqueValues(field);
    const colorNum = 25; // TODO: how to determine this number?
    const colorscale = generateColorscale(palette, colorNum + 1);

    if (fieldUniqueValues.length > 1) {
      const min = Math.min(...fieldUniqueValues);
      const max = Math.max(...fieldUniqueValues);
      this.layer.setStyle((feature) => {
        const normalizedValue =
          (Math.log1p(feature.properties[field]) - Math.log1p(min)) /
          (Math.log1p(max) - Math.log1p(min));
        const markerColor = colorscale[parseInt(normalizedValue * colorNum)];
        return { fillColor: markerColor, color: markerColor };
      });
    } else {
      this._styleMarkerWithSingleColor(generateColorscale(palette, 1)[0]);
    }
  }

  _styleMarkerSizeOnNumericalFieldValue(field, baseSize, strokeWeight) {
    const fieldUniqueValues = this._getFieldUniqueValues(field);
    if (fieldUniqueValues.length > 1) {
      const min = Math.min(...fieldUniqueValues);
      const max = Math.max(...fieldUniqueValues);
      const sizeMin = baseSize;
      const sizeMax = sizeMin * 6;
      this.layer.setStyle((feature) => {
        const normalizedValue =
          (Math.log1p(feature.properties[field]) - Math.log1p(min)) /
          (Math.log1p(max) - Math.log1p(min));
        const size = normalizedValue * (sizeMax - sizeMin) + sizeMin;
        const isPolyline = feature.geometry.type.includes("LineString");
        return {
          radius: size,
          weight: isPolyline ? size * VisualizedLayer.radiusToWeight : strokeWeight,
        };
      });
    } else {
      this._styleMarkerSize(baseSize, strokeWeight);
    }
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
      disabled: !Object.values(FieldType).includes(f.type),
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

:deep(.ant-segmented-item),
:deep(.ant-segmented-item::selection) {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.layer-style-option-row {
  justify-content: space-between;
}

.layer-info-row {
  padding-bottom: 8px;
}

</style>
