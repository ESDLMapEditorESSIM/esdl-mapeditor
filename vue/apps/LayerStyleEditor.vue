<template>
  <a-space
    id="layer-style-editor"
    direction="vertical"
    style="width: 100%; padding-top: 20px; height: 100%"
  >
    <!-- HEADER -->
    <a-row type="flex" justify="space-between" align="middle">
      <a-col>
        <h3>Layer Style Editor</h3>
      </a-col>
      <a-col>
        <a-dropdown trigger="click">
          <a-button
            type="primary"
            size="small"
            :disabled="isLoading"
            :loading="isLoading"
            @click.prevent
            >Style Layer</a-button
          >
          <template #overlay>
            <a-menu>
              <template v-if="datasources.some((ds) => ds.visible)">
                <a-menu-item-group
                  v-for="datasource in datasources.filter((ds) => ds.visible)"
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
          style="background: #fafafa; border-bottom: 1px solid #d9d9d9"
        >
          <a-col class="layer-info-col">
            <a-typography-text strong> Source </a-typography-text>
            <a-col :span="15">
              {{ vizLayer.sourceRef.name }}
            </a-col>
          </a-col>
          <a-col class="layer-info-col">
            <a-row style="align-items: center">
              <a-typography-text strong> Field </a-typography-text>
              <a-tooltip
                title="Type to search a field for styling. Reference fields load their values on selection."
                placement="right"
              >
                <a-button size="small" type="text">
                  <component
                    :is="InfoCircleOutlined"
                    style="vertical-align: 0.1rem"
                  />
                </a-button>
              </a-tooltip>
            </a-row>
            <a-tree-select
              :value="vizLayer.style.field"
              :tree-data="vizLayer.fieldTree"
              :tree-default-expanded-keys="[
                '__attributes__',
                '__costInformation__',
                '__KPIs__',
              ]"
              :loading="vizLayer.loadingRefSchema || vizLayer.loadingRefField"
              style="width: 100%"
              :show-search="true"
              tree-node-filter-prop="label"
              @focus="vizLayer.loadRefSchema()"
              @change="(field) => vizLayer.onSelectField(field)"
              @mouseleave="removeTooltipPopup"
            />
          </a-col>
          <a-space
            v-if="vizLayer.style.field !== undefined"
            direction="vertical"
            style="width: 100%"
          >
            <a-col class="layer-info-col">
              <a-typography-text strong> Style options </a-typography-text>
              <a-row>
                <a-segmented
                  v-model:value="vizLayer.style.styleType"
                  :options="vizLayer.styleTypeOptions"
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
              v-if="vizLayer.style.paint.color.mode === ColorMode.FIXED"
              class="layer-info-col"
            >
              <a-typography-text strong> Color </a-typography-text>
              <input
                type="color"
                :value="vizLayer.style.paint.color.value"
                @input="(e) => vizLayer.onSelectColor(e.target.value)"
                style="width: 100%; height: 35px; cursor: pointer; border: none"
              />
            </a-col>
            <a-col
              v-if="vizLayer.style.paint.color.mode !== ColorMode.FIXED"
              class="layer-info-col"
            >
              <a-typography-text strong> Color palette </a-typography-text>
              <a-select
                :value="vizLayer.style.paint.color.palette"
                style="width: 100%"
                @change="(palette) => vizLayer.onSelectPalette(palette)"
              >
                <a-select-option
                  v-for="option in VisualizedLayer.colorPalettes[
                    vizLayer.style.paint.color.mode
                  ]"
                  :key="option.value"
                  :value="option.value"
                >
                  <div
                    v-if="
                      vizLayer.style.paint.color.mode === ColorMode.GRADIENT
                    "
                    :style="{
                      background: toCssGradient(option.sample),
                      height: '35px',
                      width: '100%',
                      borderRadius: '2px',
                    }"
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
            <!-- Legend -->
            <a-col v-if="vizLayer.legend" class="layer-info-col">
              <a-typography-text strong>Legend</a-typography-text>
              <!-- Categorical legend -->
              <template
                v-if="
                  [ColorMode.CATEGORICAL, StyleType.PIE_CHART].includes(
                    vizLayer.legend.type,
                  )
                "
              >
                <div style="max-height: 250px; overflow-y: auto">
                  <div
                    v-for="entry in vizLayer.legend.entries"
                    :key="entry.label"
                    style="
                      display: flex;
                      align-items: center;
                      gap: 6px;
                      padding: 2px 0;
                    "
                  >
                    <span
                      :style="{
                        backgroundColor: entry.color.startsWith('#')
                          ? entry.color
                          : `#${entry.color}`,
                        width: '14px',
                        height: '14px',
                        display: 'inline-block',
                        borderRadius: '2px',
                        flexShrink: 0,
                      }"
                    />
                    <a-typography-text style="font-size: small">{{
                      entry.label
                    }}</a-typography-text>
                  </div>
                </div>
              </template>
              <!-- Gradient legend (min/max only; scale is log-normalized) -->
              <template v-else-if="vizLayer.legend.type === ColorMode.GRADIENT">
                <div
                  :style="{
                    background: toCssGradient(vizLayer.legend.colors),
                    height: '14px',
                    borderRadius: '2px',
                    width: '100%',
                  }"
                />
                <div
                  style="
                    display: flex;
                    justify-content: space-between;
                    margin-top: 2px;
                  "
                >
                  <a-typography-text style="font-size: small">{{
                    fmtNl(vizLayer.legend.min)
                  }}</a-typography-text>
                  <a-typography-text style="font-size: small">{{
                    fmtNl(vizLayer.legend.max)
                  }}</a-typography-text>
                </div>
              </template>
            </a-col>
            <a-col
              class="layer-info-col"
              v-if="
                !vizLayer.isPolygon ||
                vizLayer.style.styleType === StyleType.PIE_CHART
              "
            >
              <a-typography-text strong> Size </a-typography-text>
              <a-slider
                :value="vizLayer.style.paint.symbol.size.value"
                :min="vizLayer.style.paint.symbol.size.minSize"
                :max="vizLayer.style.paint.symbol.size.maxSize"
                :step="1"
                @change="(size) => vizLayer.onSizeChange(size)"
              />
            </a-col>
            <a-col class="layer-info-col">
              <a-typography-text strong> Opacity </a-typography-text>
              <a-slider
                :value="vizLayer.style.paint.opacity"
                :min="0"
                :max="1"
                :step="0.01"
                @change="(opacity) => vizLayer.onOpacityChange(opacity)"
              />
            </a-col>
            <a-row
              v-if="
                !vizLayer.isPolyline &&
                vizLayer.style.styleType !== StyleType.PIE_CHART
              "
              class="layer-info-row"
            >
              <a-typography-text strong> Show outline </a-typography-text>
              <a-col :span="2">
                <a-switch
                  :checked="vizLayer.style.paint.stroke.visible"
                  size="small"
                  @change="(visible) => vizLayer.onToggleShowStroke(visible)"
                />
              </a-col>
            </a-row>
            <a-row class="layer-info-row">
              <a-typography-text strong> Show label </a-typography-text>
              <a-col :span="2">
                <a-switch
                  :checked="vizLayer.style.paint.label.visible"
                  size="small"
                  @change="(visible) => vizLayer.onToggleShowLabels(visible)"
                />
              </a-col>
            </a-row>
            <template v-if="vizLayer.style.paint.label.visible">
              <a-row class="layer-info-row" style="padding-left: 16px">
                <a-typography-text> Show on hover </a-typography-text>
                <a-col :span="2">
                  <a-switch
                    :checked="!vizLayer.style.paint.label.permanent"
                    size="small"
                    @change="
                      (hoverOnly) => vizLayer.onToggleLabelPermanent(!hoverOnly)
                    "
                  />
                </a-col>
              </a-row>
              <a-row
                v-if="vizLayer.style.styleType !== StyleType.PIE_CHART"
                class="layer-info-row"
                style="padding-left: 16px"
              >
                <a-typography-text> Show 'No data' labels </a-typography-text>
                <a-col :span="2">
                  <a-switch
                    :checked="vizLayer.style.paint.label.showNullValues"
                    size="small"
                    @change="(v) => vizLayer.onToggleLabelShowNullValues(v)"
                  />
                </a-col>
              </a-row>
              <a-col class="layer-info-col" style="padding-left: 16px">
                <a-typography-text>Label offset</a-typography-text>
                <a-row :gutter="8" style="margin-top: 4px">
                  <a-col :span="12">
                    <a-input-number
                      :value="vizLayer.style.paint.label.offset[0]"
                      :controls="true"
                      size="small"
                      style="max-width: 150px"
                      addon-before="X"
                      @change="(v) => vizLayer.onLabelOffsetChange('x', v)"
                    />
                  </a-col>
                  <a-col :span="12">
                    <a-input-number
                      :value="vizLayer.style.paint.label.offset[1]"
                      :controls="true"
                      size="small"
                      style="max-width: 150px"
                      addon-before="Y"
                      @change="(v) => vizLayer.onLabelOffsetChange('y', v)"
                    />
                  </a-col>
                </a-row>
              </a-col>
            </template>
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
    <!-- Save layer style modal -->
    <SaveFavoritesModal
      v-model:open="showSaveStyleModal"
      title="Add layer style to favorites"
      :existing-groups="savedStyleGroups"
      name-placeholder="e.g. Style demand asset power"
      @save="({ name, group }) => onConfirmSaveStyle({ name, group })"
      @cancel="onCancelSaveStyleModal"
    />
    <!-- Load layer style modal -->
    <LoadFavoritesModal
      v-model:open="showLoadStyleModal"
      title="Load layer style from favorites"
      :items="savedStyles"
      :label-formatter="
        (s) =>
          s.lastUpdate
            ? `${s.name} (${new Date(s.lastUpdate).toLocaleString()})`
            : s.name
      "
      @load="(id) => onConfirmLoadStyle(id)"
      @delete-item="(id) => onDeleteSavedStyle(id)"
      @delete-group="(groupName) => onDeleteSavedStyleGroup(groupName)"
      @cancel="onCancelLoadStyleModal"
    />
  </a-space>
</template>

<script setup>
import { ref, onMounted, computed, watch, onUnmounted, markRaw } from "vue";
import { v4 as uuidv4 } from "uuid";
import {
  AppstoreOutlined,
  BarChartOutlined,
  BgColorsOutlined,
  DeleteOutlined,
  DotChartOutlined,
  EyeInvisibleOutlined,
  EyeOutlined,
  ExpandAltOutlined,
  FolderOpenOutlined,
  InfoCircleOutlined,
  StarOutlined,
  PieChartOutlined,
} from "@ant-design/icons-vue";
import SaveFavoritesModal from "@/components/modals/SaveFavoritesModal.vue";
import LoadFavoritesModal from "@/components/modals/LoadFavoritesModal.vue";
import { fetchData } from "@/utils/api";
import { displayNotification } from "@/utils/notification";
import {
  getEsdlObjectFields,
  getRefFieldSchema,
  getRefFieldValues,
  generateColorscale,
  setLeafletFeatureStyle,
  FieldType,
  StyleType,
  ColorMode,
  SizeMode,
  PaletteName,
} from "@/utils/layerStyle";
import { useESDLProjects } from "@/composables/esdlProjects";
import {
  useEsdlLayers,
  collectAllLayers,
  groupByLevels,
} from "@/composables/esdlLayers";

const { getAllVariants } = useESDLProjects();
const { enabledEsdlIdList, isEsdlLoaded } = useEsdlLayers();

const toCssGradient = (colors) => {
  const stops = colors.map((c) => (c.startsWith("#") ? c : `#${c}`)).join(", ");
  return `linear-gradient(to right, ${stops})`;
};

const fmtNl = (n) =>
  n.toLocaleString("nl-NL", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });

// to prevent stuck popup on UI
const removeTooltipPopup = () => {
  window.jquery(".ui-tooltip-content").parents("div").remove();
};

// NOTE: As a placeholder for future extension to support other data source type.
// At the moment, only ESDL data source is supported and created during onMounted() and watch() of enabledEsdlIdList below.
// const props = defineProps({
//   // An array of objects with each object contains data to create a DataSource instance (and the corresponding GeoJSON FeatureCollection).
//   layerSources: {
//     type: Array,
//     default: () => [],
//   },
// });

const datasources = ref([]);

const activeVizLayerKeys = ref([]);

onMounted(async () => {
  console.debug("Mount Layer Style Editor component.");
  await fetchLayerStyles();
  // Initialize datasources for ESDLs already fully loaded at mount time
  for (const esId of enabledEsdlIdList.value.filter((id) => isEsdlLoaded(id))) {
    const es = window.esdl_list?.[esId];
    if (es) {
      datasources.value = [
        ...datasources.value,
        new EsdlLayerSource(esId, es.title),
      ];
    }
  }
});

onUnmounted(() => {
  console.debug("Unmount Layer Style Editor component.");
  datasources.value.forEach((ds) => ds.dispose());
});

// Create datasource when an ESDL becomes fully loaded (ADD_ESDL_OBJECTS and other mandatory messages
// arrive after enableEsdl fires from area_layer, so we must wait for isEsdlLoaded).
watch(
  () => enabledEsdlIdList.value.filter((id) => isEsdlLoaded(id)),
  (loadedIds) => {
    for (const esId of loadedIds) {
      if (!datasources.value.find((ds) => ds.id === esId)) {
        const es = window.esdl_list?.[esId];
        if (es) {
          datasources.value = [
            ...datasources.value,
            new EsdlLayerSource(esId, es.title),
          ];
        }
      }
    }
  },
);

// Watch enabled ESDL list to show/hide/dispose datasources based on project state.
watch(
  () => [...enabledEsdlIdList.value],
  (newIds, oldIds) => {
    const prevIds = oldIds ?? [];
    const addedIds = newIds.filter((id) => !prevIds.includes(id));
    const removedIds = prevIds.filter((id) => !newIds.includes(id));
    const projectEsIds = new Set(getAllVariants().map((v) => v.es_id));

    for (const esId of addedIds) {
      const existing = datasources.value.find((ds) => ds.id === esId);
      if (existing) existing.setVisible(true);
      // Creation is handled by the loading watch above
    }

    for (const esId of removedIds) {
      const ds = datasources.value.find((d) => d.id === esId);
      if (!ds) continue;
      if (projectEsIds.has(esId)) {
        ds.setVisible(false);
      } else {
        ds.dispose();
        datasources.value = datasources.value.filter((d) => d.id !== esId);
      }
    }
  },
);

// -------------------------------------------------- //
// -------------- Save/Load layer style ------------- //
// -------------------------------------------------- //

const savedStyles = ref([]);

const fetchLayerStyles = async () => {
  try {
    const styles = await fetchData("layer_style/get_layer_styles");
    savedStyles.value = styles;
  } catch (error) {
    console.error(error);
    displayNotification("error", "Failed to retrieve saved layer styles.");
  }
};

/**
 * Persists the full styles list to the backend.
 * On failure reverts `savedStyles` to its previous value.
 *
 * @param {Array} updatedStyles
 * @param {Array} previousStyles
 */
const persistLayerStyles = async (updatedStyles, previousStyles) => {
  savedStyles.value = updatedStyles;
  try {
    const saved = await fetchData("layer_style/save_layer_styles", {
      styles: updatedStyles,
    });
    savedStyles.value = saved;
  } catch (error) {
    console.error(error);
    displayNotification("error", "Failed to save layer styles.");
    savedStyles.value = previousStyles;
  }
};

const showSaveStyleModal = ref(false);
const vizLayerToSaveStyle = ref(undefined);

const savedStyleGroups = computed(() => [
  ...new Set(savedStyles.value.map((s) => s.group).filter(Boolean)),
]);

const showLoadStyleModal = ref(false);
const vizLayerToLoadStyle = ref(undefined);

const onSaveStyleBtnClick = (vizLayer) => {
  vizLayerToSaveStyle.value = vizLayer;
  showSaveStyleModal.value = true;
};

const onLoadSavedStyleBtnClick = (vizLayer) => {
  vizLayerToLoadStyle.value = vizLayer;
  showLoadStyleModal.value = true;
};

const onCancelSaveStyleModal = () => {
  vizLayerToSaveStyle.value = undefined;
};

/**
 * Snapshot the target layer's current `style` and persist the updated list to the backend.
 */
const onConfirmSaveStyle = async ({ name, group }) => {
  if (!vizLayerToSaveStyle.value) return;

  const newStyle = {
    id: uuidv4(),
    name,
    group,
    sourceType: vizLayerToSaveStyle.value.sourceType,
    // Used as a simple way to distinguish styles sharing the same name and group.
    lastUpdate: Date.now(),
    style: JSON.parse(JSON.stringify(vizLayerToSaveStyle.value.style)),
  };
  const previousStyles = savedStyles.value;
  const updatedStyles = [...previousStyles, newStyle];

  vizLayerToSaveStyle.value = undefined;

  await persistLayerStyles(updatedStyles, previousStyles);
  displayNotification("success", `Layer style '${name}' saved to favorites.`);
};

const onCancelLoadStyleModal = () => {
  vizLayerToLoadStyle.value = undefined;
};

const onDeleteSavedStyle = async (id) => {
  const previousStyles = savedStyles.value;
  const updatedStyles = previousStyles.filter((s) => s.id !== id);
  await persistLayerStyles(updatedStyles, previousStyles);
};

const onDeleteSavedStyleGroup = async (groupName) => {
  const previousStyles = savedStyles.value;
  const updatedStyles = previousStyles.filter(
    (s) => (s.group || "Ungrouped") !== groupName,
  );
  await persistLayerStyles(updatedStyles, previousStyles);
};

/**
 * Applies a saved style config onto the target vizLayer.
 * If the saved style references a ref path that hasn't been loaded yet, it is loaded first.
 *
 * @param {VisualizedLayer} vizLayer
 * @param {Object} savedStyle - Full savedStyle object ({ id, name, group, style }).
 */
const applySavedStyleToVizLayer = async (vizLayer, savedStyle) => {
  if (savedStyle.sourceType && savedStyle.sourceType !== vizLayer.sourceType) {
    displayNotification(
      "warning",
      `Style '${savedStyle.name}' was saved for a layer of type '${savedStyle.sourceType}' and cannot be applied to this layer of type '${vizLayer.sourceType}'.`,
    );
    return;
  }

  const style = JSON.parse(JSON.stringify(savedStyle.style));

  // Ensure ref field is enriched before checking fieldOptions.
  if (style.refPath && !vizLayer.loadedRefPaths[style.refPath]) {
    await vizLayer.loadRefField(style.refPath, style.refLabel);
  }

  const fieldNames = vizLayer.fieldOptions.map((f) => f.value);

  // If the saved field does not exist on the target layer, abort and warn the user.
  if (style.field !== undefined && !fieldNames.includes(style.field)) {
    displayNotification(
      "warning",
      `Field '${style.field}' is not available on this layer. Style not applied.`,
    );
    return;
  }

  vizLayer.style = style;
  vizLayer.applyStyle();
  displayNotification("success", `Layer style '${savedStyle.name}' applied.`);
};

// Applies a saved style to the target vizLayer.
const onConfirmLoadStyle = async (id) => {
  if (!vizLayerToLoadStyle.value) return;

  const savedStyle = savedStyles.value.find((s) => s.id === id);
  if (savedStyle) {
    await applySavedStyleToVizLayer(vizLayerToLoadStyle.value, savedStyle);
  }

  vizLayerToLoadStyle.value = undefined;
};

// -------------------------------------------------- //
// --------  Data source and Visualized Layer  ------ //
// -------------------------------------------------- //

const isLoading = computed(() => {
  return datasources.value.find((ds) => ds.loading === true) ? true : false;
});

/**
 * Flatten all datasources' vizLayers (VisualizedLayer instances) into a single-level list.
 */
const visualizedLayers = computed(() => {
  return datasources.value
    .filter((ds) => ds.vizLayers !== undefined && ds.visible)
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
    datasource.loading = true;
    await datasource.addAsGeoJsonSource(sourceKey);
  }
  datasource.loading = false;

  datasource.onAddLayerToMap(sourceKey);
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
    // markRaw prevents Vue's Proxy from wrapping Leaflet internals, avoiding _map = null during zoom animation.
    // Ref: https://stackoverflow.com/questions/65981712/uncaught-typeerror-this-map-is-null-vue-js-3-leaflet/66693709#66693709
    this.mapLayerGroup = markRaw(L.featureGroup().addTo(this._map));
    this.visible = true; // whether this datasource's ESDL variant is currently enabled in the project tree
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
    const vizLayer = new VisualizedLayer(this, layerName, sourceKey);
    this.vizLayers.push(vizLayer);
  }

  /**
   * Categorizes a sourceKey. Subclasses may override this;
   * the base implementation returns undefined when a source has no such distinction.
   *
   * @param {string} sourceKey
   * @returns {string|undefined}
   */
  getSourceType(sourceKey) {
    return undefined;
  }

  dispose() {
    console.debug(`Disposing DataSource ${this.name} (${this.id})`);
    this.vizLayers.forEach((vl) => {
      vl._clearSymbolLayer();
      vl.removeLayerFromMap(vl.layer);
    });
    this.mapLayerGroup?.remove();
    this.vizLayers = [];
  }

  setVisible(visible) {
    this.visible = visible;
    if (visible) {
      this._map.addLayer(this.mapLayerGroup);
    } else {
      this._map.removeLayer(this.mapLayerGroup);
    }
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
 * It fetches and enriches ESDL asset and area features with attribute values from the backend.
 */
class EsdlLayerSource extends DataSource {
  /** Category of ESDL entity a VisualizedLayer's features originate from. */
  static SourceType = Object.freeze({
    ASSET: "ESDL Asset",
    AREA: "ESDL Area",
  });

  constructor(id, name) {
    super(id, name, DataSourceType.ESDL);

    const assetEntries = this._getEsdlAssetLayers();
    const areaEntries = this._getEsdlAreaLevels();
    this.sources = Object.fromEntries([...assetEntries, ...areaEntries]);
    // Tracks SourceType per sourceKey.
    this._sourceTypeByKey = {
      ...Object.fromEntries(
        assetEntries.map(([key]) => [key, EsdlLayerSource.SourceType.ASSET]),
      ),
      ...Object.fromEntries(
        areaEntries.map(([key]) => [key, EsdlLayerSource.SourceType.AREA]),
      ),
    };
  }

  /**
   * Enrich the features of the given sourceKey (asset type or area hierarchy level) with attribute
   * (field) values returned from the backend and store them as a GeoJSON FeatureCollection in
   * `this.geoJsonSources`.
   *
   * @param {string} sourceKey ESDL asset type, or area level (e.g. "Area L1 (Municipality)")
   * @override
   */
  async addAsGeoJsonSource(sourceKey) {
    const layerFeatures = this.sources[sourceKey];
    const isArea =
      this.getSourceType(sourceKey) === EsdlLayerSource.SourceType.AREA;

    // First pass: compute geometry and objectId synchronously — no field fetching yet.
    const rawFeatures = layerFeatures.map((f) => {
      const g = f.toGeoJSON();
      const objectId = isArea ? f.id.replace(/ \(\d+ of \d+\)$/, "") : f.id;
      // g.id retains the suffixed piece id for grouping; _objectId is the real ESDL id used after merge.
      g.id = f.id;
      g._objectId = objectId;
      return g;
    });

    // Group split Polygon pieces that share the same _objectId and merge into one MultiPolygon.
    const byObjectId = new Map();
    for (const g of rawFeatures) {
      if (!byObjectId.has(g._objectId)) byObjectId.set(g._objectId, []);
      byObjectId.get(g._objectId).push(g);
    }

    // Second pass: fetch fields once per unique objectId, not once per polygon piece.
    const featurePromises = [...byObjectId.entries()].map(
      async ([objectId, pieces]) => {
        const fields = await getEsdlObjectFields(this.id, objectId);
        const properties = {};
        fields.forEach((attr) => {
          properties[attr.name] = attr.value;
        });

        // Polygon feature
        if (pieces.length === 1) {
          pieces[0].id = objectId;
          pieces[0]["_fields"] = fields;
          pieces[0].properties = properties;
          return pieces[0];
        } else {
          // Reassemble split Polygon pieces into a single MultiPolygon feature.
          return {
            ...pieces[0],
            id: objectId,
            _fields: fields,
            properties,
            geometry: {
              type: "MultiPolygon",
              coordinates: pieces.map((p) => p.geometry.coordinates),
            },
          };
        }
      },
    );

    const geoJsonFeatureCollection = await Promise.all(featurePromises);

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

  /** @override */
  getSourceType(sourceKey) {
    return this._sourceTypeByKey[sourceKey];
  }

  /**
   * Get all asset layers of the ESDL model, grouped by ESDL asset type.
   *
   * @returns {Array<[string, Object[]]>} [sourceKey, layers[]] pairs, to be merged into `this.sources`.
   */
  _getEsdlAssetLayers() {
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
    return Object.entries(layers);
  }

  /**
   * Get all area layers of the ESDL model, grouped by hierarchy depth (for example, municipality, wijk, buurt, ...),
   * derived from `parent_area_id` regardless of any ESDL `logicalGroup` nesting.
   *
   * @returns {Array<[string, Object[]]>} [sourceKey, layers[]] pairs, to be merged into `this.sources`.
   */
  _getEsdlAreaLevels() {
    const areaFeatureGroup = this._getEsdlFeatureGroupLayer(
      this.id,
      "area_layer",
    );
    const allAreaLayers = collectAllLayers(areaFeatureGroup); // TODO: review and check
    const levels = groupByLevels(allAreaLayers);

    return levels.map((levelLayers, idx) => {
      const scopes = new Set(
        levelLayers.map((l) => l.feature?.properties?.scope).filter(Boolean),
      );
      let sourceKey = `Area L${idx + 1}`;
      if (scopes.size === 1) {
        sourceKey += ` (${[...scopes][0]})`;
      } else if (scopes.size > 1) {
        sourceKey += ` (mixed scope)`;
      }
      return [sourceKey, levelLayers];
    });
  }
}

/**
 * Class representing a visualized layer on the map, with styling and interactivity.
 */
class VisualizedLayer {
  // NICE TO HAVE: custom icons
  // Supported style types
  static StyleTypes = Object.freeze({
    [FieldType.BOOLEAN]: [
      {
        value: StyleType.CATEGORICAL_COLOR,
        payload: {
          label: "Categorical Color",
          icon: AppstoreOutlined,
        },
      },
    ],
    [FieldType.STRING]: [
      {
        value: StyleType.SINGLE_COLOR,
        payload: {
          label: "Single Color",
          icon: BgColorsOutlined,
        },
      },
      {
        value: StyleType.CATEGORICAL_COLOR,
        payload: {
          label: "Categorical Color",
          icon: AppstoreOutlined,
        },
      },
    ],
    [FieldType.NUMBER]: [
      {
        value: StyleType.SIZE,
        payload: {
          label: "Size",
          icon: ExpandAltOutlined,
        },
      },
      {
        value: StyleType.GRADIENT_COLOR,
        payload: {
          label: "Gradient Color",
          icon: BarChartOutlined,
        },
      },
      {
        value: StyleType.COLOR_AND_SIZE,
        payload: {
          label: "Color and Size",
          icon: DotChartOutlined,
        },
      },
    ],
    [FieldType.ARRAY]: [
      {
        value: StyleType.PIE_CHART,
        payload: {
          label: "Pie Chart",
          icon: PieChartOutlined,
        },
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

  // Solid fill opacity makes adjacent/overlapping area polygons unreadable, so default them lower.
  static defaultPolygonOpacity = 0.5;

  static defaultStyle = {
    field: undefined,
    fieldType: undefined, // undefined || FieldType Enum
    styleType: undefined, // undefined || StyleType Enum
    refPath: null, // opaque ref path token when the field is a reference attribute
    refLabel: null, // human readable form of refPath, kept so saved styles can restore the field option
    paint: {
      color: {
        mode: ColorMode.FIXED, // ColorMode Enum
        value: "#1f78b4",
        palette: undefined,
      },
      symbol: {
        size: {
          mode: SizeMode.FIXED, // SizeMode Enum
          value: 10,
          minSize: 1,
          maxSize: 20,
        },
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
        permanent: true,
        offset: [0, 0],
        showNullValues: false,
      },
    },
  };

  constructor(sourceRef, name, sourceKey) {
    this.sourceRef = sourceRef;
    this.name = name;
    this.features = sourceRef.geoJsonSources[sourceKey];
    // Resolved by the owning DataSource; recorded on saved styles so they aren't cross-applied to the wrong source type.
    this.sourceType = sourceRef.getSourceType(sourceKey);

    this._initVizLayerPane();

    this.id = `${sourceRef.id}-${name}`;
    // The persistent feature store. Holds feature geometries and field data.
    this.layer = markRaw(this.styleGeoJsonFeatures(this.features));
    this.visible = true; // whether this individual viz layer is shown on the map (user eye-toggle)
    this.fieldOptions = this._listLayerFieldOptions();

    // A separate Leaflet layer group used only for distribution PIE_CHART,
    // via leaflet-dvf PieChartMarker subclass.
    this._symbolLayer = null;

    this.style = JSON.parse(JSON.stringify(VisualizedLayer.defaultStyle));
    // To make default style more visible for polygon with lower opacity and visible stroke.
    if (this.isPolygon) {
      this.style.paint.opacity = VisualizedLayer.defaultPolygonOpacity;
      this.style.paint.stroke.visible = true;
    }
    this.legend = null;

    // Tracks which ref paths have already had their values fetched, keyed by path token → JS type.
    this.loadedRefPaths = {};
    this.loadingRefField = false;

    // Reference field tree.
    this.refSchema = [];
    this.loadingRefSchema = false;
    this.fieldTree = this._buildFieldTree();

    this.addLayerToMap(this.layer);
  }

  styleGeoJsonFeatures(features) {
    const layer = L.geoJSON(features, {
      style: function (feature) {
        const isPolygon = feature.geometry.type.includes("Polygon");
        return setLeafletFeatureStyle(
          feature.geometry.type,
          isPolygon
            ? { opacity: VisualizedLayer.defaultPolygonOpacity, stroke: true }
            : {},
        );
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

  // TODO
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
      if (this._symbolLayer)
        this.sourceRef.mapLayerGroup.removeLayer(this._symbolLayer);
      this.sourceRef.mapLayerGroup.removeLayer(this.layer);
      this.visible = false;
    } else {
      this.sourceRef.mapLayerGroup.addLayer(this.layer);
      if (this._symbolLayer)
        this.sourceRef.mapLayerGroup.addLayer(this._symbolLayer);
      this.visible = true;
    }
  }

  removeLayer(event) {
    event.stopPropagation();
    if (this.sourceRef) {
      this._clearSymbolLayer();
      this.sourceRef.vizLayers = this.sourceRef.vizLayers.filter(
        (layer) => layer.id !== this.id,
      );
      this.removeLayerFromMap(this.layer);
    }
  }

  /**
   * Loads the full reference field tree once, on first focus of the field selector.
   */
  async loadRefSchema() {
    if (this.refSchema.length > 0 || this.loadingRefSchema) return;
    this.loadingRefSchema = true;
    try {
      this.refSchema = await getRefFieldSchema(
        this.sourceRef.id,
        this._objectIds(),
      );
      this.fieldTree = this._buildFieldTree();
    } catch (error) {
      console.error("Failed to load reference field schema:", error);
      displayNotification("error", "Failed to load reference field schema.");
    } finally {
      this.loadingRefSchema = false;
    }
  }

  /**
   * @param {string} path - Opaque ref path token.
   * @returns {Object|null} The schema leaf with that value, if the tree is loaded.
   */
  findRefSchemaNode(path) {
    const search = (nodes) => {
      for (const node of nodes) {
        if (node.value === path) return node;
        const found = node.children ? search(node.children) : null;
        if (found) return found;
      }
      return null;
    };
    return search(this.refSchema);
  }

  /** Style type options for the current field, excluding radius-based options which don't apply to polygon fill. */
  get styleTypeOptions() {
    const options = VisualizedLayer.StyleTypes[this.style.fieldType] ?? [];
    if (!this.isPolygon) return options;
    return options.filter(
      (opt) =>
        opt.value !== StyleType.SIZE && opt.value !== StyleType.COLOR_AND_SIZE,
    );
  }

  get isPolygon() {
    return (
      this.features[0].geometry.type.includes("Polygon") ||
      this.features[0].geometry.type.includes("MultiPolygon")
    );
  }

  get isPolyline() {
    return (
      this.features[0].geometry.type.includes("LineString") ||
      this.features[0].geometry.type.includes("MultiLineString")
    );
  }

  _objectIds() {
    return this.features.map((f) => f._objectId ?? f.id);
  }

  _buildFieldTree() {
    const attributes = this.fieldOptions
      .filter((opt) => !opt.refPath)
      .map((opt) => ({
        value: opt.value,
        label: opt.label,
        disabled: opt.disabled,
        isLeaf: true,
      }));
    return [
      {
        value: "__attributes__",
        label: "Attributes",
        selectable: false,
        children: attributes,
      },
      ...this.refSchema,
    ];
  }

  /**
   * Enriches the layer features with values for the given ref path and
   * registers the path as a selectable field.
   *
   * @param {string} path - Opaque ref path token produced by the backend schema endpoint.
   * @param {string} [label] - Fallback readable path, used when the schema tree isn't loaded.
   */
  async loadRefField(path, label) {
    if (this.loadedRefPaths[path]) return;
    this.loadingRefField = true;
    try {
      // Needed so a restored saved style can resolve its label without a prior browse.
      await this.loadRefSchema();
      const displayLabel =
        this.findRefSchemaNode(path)?.display || label || path;
      const result = await getRefFieldValues(
        this.sourceRef.id,
        this._objectIds(),
        path,
      );

      const firstEntry = Object.values(result).find((r) => r !== null);
      if (!firstEntry) {
        console.warn(`No data returned for ref path '${path}'`);
        return;
      }

      const jsType = firstEntry.type;

      // Inject ref values into each feature's properties so styling methods can access them.
      this.features.forEach((f) => {
        f.properties[path] = result[f._objectId ?? f.id]?.value ?? null;
      });

      if (!this.fieldOptions.find((opt) => opt.value === path)) {
        this.fieldOptions = [
          ...this.fieldOptions,
          {
            label: `${displayLabel} [${jsType}]`,
            value: path,
            type: jsType,
            refPath: path,
            refLabel: displayLabel,
            disabled: !Object.values(FieldType).includes(jsType),
          },
        ];
      }

      this.loadedRefPaths[path] = jsType;
    } catch (error) {
      console.error(`Failed to load reference field '${path}':`, error);
      displayNotification("error", "Failed to load reference field values.");
    } finally {
      this.loadingRefField = false;
    }
  }

  // ---------------------------------------- //
  // ----------- Event handlers ------------- //
  // ---------------------------------------- //

  async onSelectField(field) {
    // Reference fields only exist as schema nodes until picked; their values load on first selection.
    if (!this.fieldOptions.find((f) => f.value === field)) {
      await this.loadRefField(field);
    }
    const opt = this.fieldOptions.find((f) => f.value === field);
    if (!opt) return;

    this.style.field = field;
    this.style.fieldType = opt.type;
    this.style.refPath = opt.refPath || null;
    this.style.refLabel = opt.refLabel || null;

    this.preSelectStyleTypeOnFieldSelection();
    this.applyStyle();
  }

  preSelectStyleTypeOnFieldSelection() {
    if (
      Object.keys(VisualizedLayer.StyleTypes).includes(this.style.fieldType)
    ) {
      this.style.styleType = this.styleTypeOptions[0]?.value;
      this.preSelectColorOnStyleTypeChange();
      // Overwrite opacity for array type for pie chart style.
      if (this.style.fieldType === FieldType.ARRAY) {
        this.style.paint.opacity = 1.0;
      }
    } else {
      console.warn(
        `No supported style type for ${this.style.field} [${this.style.fieldType}]`,
      );
    }
  }

  onSelectStyleType(type) {
    this.style.styleType = type;

    this.preSelectColorOnStyleTypeChange();
    this.applyStyle();
  }

  preSelectColorOnStyleTypeChange() {
    if (
      this.style.styleType === StyleType.SINGLE_COLOR ||
      this.style.styleType === StyleType.SIZE
    ) {
      this.style.paint.color.value =
        VisualizedLayer.defaultStyle.paint.color.value;
    } else if (
      this.style.styleType === StyleType.CATEGORICAL_COLOR ||
      this.style.styleType === StyleType.GRADIENT_COLOR ||
      this.style.styleType === StyleType.COLOR_AND_SIZE
    ) {
      if (
        this.style.fieldType === FieldType.STRING ||
        this.style.fieldType === FieldType.BOOLEAN
      ) {
        this.style.paint.color.palette =
          VisualizedLayer.colorPalettes[ColorMode.CATEGORICAL][0].value;
      } else if (this.style.fieldType === FieldType.NUMBER) {
        this.style.paint.color.palette =
          VisualizedLayer.colorPalettes[ColorMode.GRADIENT][0].value;
      }
    } else if (this.style.styleType === StyleType.PIE_CHART) {
      this.style.paint.color.palette =
        VisualizedLayer.colorPalettes[ColorMode.CATEGORICAL][0].value;
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

  onToggleLabelPermanent(permanent) {
    this.style.paint.label.permanent = permanent;
    this.applyStyle();
  }

  onToggleLabelShowNullValues(showNullValues) {
    this.style.paint.label.showNullValues = showNullValues;
    this.applyStyle();
  }

  onLabelOffsetChange(axis, value) {
    const offset = [...this.style.paint.label.offset];
    offset[axis === "x" ? 0 : 1] = value ?? 0;
    this.style.paint.label.offset = offset;
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
    updated.refPath = this.style.refPath;
    updated.refLabel = this.style.refLabel;

    // Derive paint modes from fieldType + styleType.
    const { fieldType } = updated;
    if (fieldType === FieldType.BOOLEAN || fieldType === FieldType.STRING) {
      updated.paint.color.mode =
        updated.styleType === StyleType.CATEGORICAL_COLOR
          ? ColorMode.CATEGORICAL
          : ColorMode.FIXED;
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
    } else if (fieldType === FieldType.ARRAY) {
      updated.paint.color.mode = ColorMode.CATEGORICAL;
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

    // Reset legend; set by color-styling methods when applicable.
    this.legend = null;

    // Special handling for Distribution KPIs piechart
    if (this.style.styleType === StyleType.PIE_CHART) {
      this._styleMarkersAsPieCharts(
        field,
        paint.color.palette,
        paint.symbol.size.value,
        paint.opacity,
      );
      this._showHidePieChartLabels(field, paint.label);
      return;
    }

    // For non-pie-chart styles, clean up any existing symbol overlay.
    this._clearSymbolLayer();

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
      this._styleMarkerSizeOnNumericalFieldValue(
        field,
        paint.symbol.size.value,
        paint.stroke.weight,
      );
    }

    // Apply opacity, stroke, labels
    this._styleMarkerOpacity(paint.opacity);
    this._showHideMarkerStroke(paint.stroke);
    this._showHideFeatureLabels(field, paint.label);
  }

  // ---------------------------------------- //
  // ----- Internal methods for styling ----- //
  // ---------------------------------------- //

  _clearSymbolLayer() {
    if (!this._symbolLayer) return;
    // Close tooltips before removing to avoid orphaned zoom-animation listeners.
    this._symbolLayer.eachLayer((layer) => {
      layer.closeTooltip();
      layer.unbindTooltip();
    });
    this._symbolLayer.clearLayers();
    this.sourceRef.mapLayerGroup.removeLayer(this._symbolLayer);
    this._symbolLayer = null;
    // Restore pointer events on base layer paths (were disabled while in pie chart mode).
    this.layer.eachLayer((fl) => {
      if (fl._path) fl._path.style.pointerEvents = "";
    });
  }

  _styleMarkersAsPieCharts(field, palette, size, opacity) {
    // Full teardown of existing _symbolLayer, so Leaflet properly removes zoom-animation listeners on old markers.
    this._clearSymbolLayer();
    this._symbolLayer = markRaw(L.layerGroup());
    this._symbolLayer.addTo(this.sourceRef.mapLayerGroup);

    // NICE TO HAVE: cache allLabels to avoid recalculating on each style change.
    // Collect all unique labels across features for a consistent color assignment.
    const allLabels = new Set();
    this.features.forEach((f) => {
      const items = f.properties[field];
      if (Array.isArray(items)) items.forEach((i) => allLabels.add(i.label));
    });
    const labelList = [...allLabels].sort();
    const colorscale = generateColorscale(palette, labelList.length);
    const colorByLabel = Object.fromEntries(
      labelList.map((l, i) => [l, colorscale[i]]),
    );

    // NICE TO HAVE: cache featureSums to avoid recalculating on each style change.
    // Compute each feature's distribution sum to drive proportional radius scaling.
    const featureSums = new Map();
    this.features.forEach((f) => {
      const items = f.properties[field];
      if (!Array.isArray(items) || items.length === 0) return;
      const sum = items.reduce((acc, i) => acc + (i.value ?? 0), 0);
      if (sum > 0) featureSums.set(f.id, sum);
    });
    const sums = [...featureSums.values()];
    const minSum = sums.length ? Math.min(...sums) : 0;
    const maxSum = sums.length ? Math.max(...sums) : 0;
    const rMin = size ?? 5;
    const rMax = rMin * 6;

    // Log-normalized radius;
    const calcRadius = (id) => {
      const sum = featureSums.get(id);
      if (!sum) return 0;
      if (minSum === maxSum) return rMax;
      return (
        ((Math.log1p(sum) - Math.log1p(minSum)) /
          (Math.log1p(maxSum) - Math.log1p(minSum))) *
          (rMax - rMin) +
        rMin
      );
    };

    // Hide base layer visually and disable pointer events so underlying layers remain interactive.
    this.layer.eachLayer((fl) => {
      fl.setStyle({ opacity: 0, fillOpacity: 0, stroke: false });
      if (fl._path) fl._path.style.pointerEvents = "none";
    });

    this.layer.eachLayer((featureLayer) => {
      const feature = featureLayer.feature;
      const items = feature.properties[field];
      if (!Array.isArray(items) || items.length === 0) return;

      const radius = calcRadius(feature.id);
      if (radius <= 0) return;

      // TODO: also get polyline midpoint
      // Points use their own location; polygons use their bounds centroid (computed client-side).
      const center = feature.geometry.type.includes("Point")
        ? featureLayer.getLatLng()
        : featureLayer.getBounds().getCenter();
      const data = {};
      const chartOptions = {};
      labelList.forEach((label) => {
        const item = items.find((i) => i.label === label);
        data[label] = item?.value ?? 0;
        chartOptions[label] = {
          fillColor: colorByLabel[label],
          displayText: function (value) {
            return typeof value === "number" ? fmtNl(value) : value;
          },
        };
      });

      const pieChart = markRaw(
        new L.PieChartMarker(center, {
          radius,
          fillOpacity: opacity ?? 1.0,
          opacity: opacity ?? 1.0,
          data,
          chartOptions,
          // Use the popup method instead of LegendIcon method.
          usePopup: true,
          // Leaflet DVF plugin bug: a non-null stroke triggers _updateBounds() which doesn't exist on sector paths.
          stroke: null,
          rotation: -90,
          pane: VisualizedLayer.customMapPane,
        }),
      );
      this._symbolLayer.addLayer(pieChart);
      pieChart._featureId = feature.id; // required by _showHidePieChartLabels to look up the feature
    });

    this.legend = {
      type: StyleType.PIE_CHART,
      entries: labelList.map((label, i) => ({ label, color: colorscale[i] })),
    };
  }

  _showHidePieChartLabels(field, label) {
    // Tooltips for features with data are bound to the PieChartMarker in _symbolLayer.
    if (this._symbolLayer) {
      this._symbolLayer.eachLayer((pieChart) => {
        pieChart.closeTooltip();
        pieChart.unbindTooltip();
        if (!label.visible) {
          return;
        }
        const feature = this.features.find((f) => f.id === pieChart._featureId);
        const items = feature?.properties[field];
        if (!Array.isArray(items)) {
          return;
        }

        const lines = items.map((i) => `${i.label}: ${fmtNl(i.value ?? 0)}`);
        const total = items.reduce((acc, i) => acc + (i.value ?? 0), 0);
        lines.push(`<b>Total: ${fmtNl(total)}</b>`);

        // Bind custom tooltip to the PieChartMarker with the aggregated data.
        pieChart.bindTooltip(lines.join("<br>"), {
          permanent: label.permanent,
          direction: "top",
          offset: label.offset,
          opacity: 0.8,
        });

        // Strip DVF's per-slice popup so only the custom _showHidePieChartLabels tooltip is shown.
        pieChart.eachLayer((slice) => {
          slice.off("mouseover").off("mouseout");
        });

        if (label.permanent) pieChart.openTooltip();
      });
    }
  }

  _styleMarkerWithSingleColor(color) {
    this.layer.setStyle({
      fillColor: color,
      color: color,
    });
  }

  _styleMarkerSize(size, strokeWeight) {
    this.layer.setStyle({
      radius: size,
      weight: this.isPolyline
        ? size * VisualizedLayer.radiusToWeight
        : strokeWeight,
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
    if (!this.isPolyline) {
      this.layer.setStyle({
        stroke: stroke.visible,
        weight: stroke.weight,
        color: stroke.color,
      });
    }
  }

  _showHideFeatureLabels(selectedField, label) {
    this.layer.eachLayer((featureLayer) => {
      featureLayer.closeTooltip();
      featureLayer.unbindTooltip();

      if (label.visible && featureLayer.feature?.properties) {
        const fieldValue = featureLayer.feature.properties[selectedField];
        if (fieldValue === null && !label.showNullValues) return;
        const popupContent =
          fieldValue !== null
            ? typeof fieldValue === "number"
              ? fmtNl(fieldValue)
              : `${fieldValue}`
            : "No data";
        featureLayer.bindTooltip(popupContent, {
          permanent: label.permanent,
          direction: "top",
          offset: label.offset,
          opacity: 0.8,
        });
        if (label.permanent) featureLayer.openTooltip();
      }
    });
  }

  _styleMarkerColorOnCategorizedFieldValue(field, palette) {
    const fieldUniqueValues = this._getFieldUniqueValues(field);
    if (fieldUniqueValues.length) {
      const colorscale = generateColorscale(palette, fieldUniqueValues.length);
      this.layer.setStyle((feature) => {
        const idx = fieldUniqueValues.findIndex(
          (val) => val === feature.properties[field],
        );
        const markerColor = colorscale[idx % colorscale.length];
        return { fillColor: markerColor, color: markerColor };
      });
      this.legend = {
        type: ColorMode.CATEGORICAL,
        entries: fieldUniqueValues.map((val, i) => ({
          label: String(val),
          color: colorscale[i % colorscale.length],
        })),
      };
    } else {
      this._styleMarkerWithSingleColor(generateColorscale(palette, 1)[0]);
    }
  }

  _styleMarkerColorOnNumericalFieldValue(field, palette) {
    const fieldUniqueValues = this._getFieldUniqueValues(field);
    const colorNum = 25;
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
      this.legend = {
        type: ColorMode.GRADIENT,
        colors: colorscale,
        min,
        max,
      };
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
          weight: isPolyline
            ? size * VisualizedLayer.radiusToWeight
            : strokeWeight,
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

.layer-info-row {
  justify-content: space-between;
}

.layer-info-col {
  padding-bottom: 8px;
}
</style>
