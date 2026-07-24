<!-- TODO: move this to components -->
<template>
  <a-space
    id="layer-studio"
    direction="vertical"
    style="width: 100%; padding: 8px; height: 100%"
  >
    <a-col>
      <a-dropdown trigger="click">
        <a-button type="primary" size="small" @click.prevent
          >Add Layer</a-button
        >
        <template #overlay>
          <a-menu>
            <template v-if="sourceOptions.length > 0">
              <a-menu-item
                v-for="option in sourceOptions"
                :key="option.value"
                @click="onSelectSource(option.datasource, option.sourceKey)"
              >
                {{ option.label }}
              </a-menu-item>
            </template>
            <a-menu-item v-else key="no-sources" disabled>
              No sources available
            </a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>
    </a-col>
  </a-space>
</template>

<script setup>
import { ref, onMounted, computed, watch } from "vue";
import { getAssetFields } from "@/utils/spatialVisualization";

// TODO: needed? avoid such dependency here?
import { useEsdlLayers } from "@/composables/esdlLayers";
const  { getEsdlLayers, getEsdlFeatureGroupLayer } = useEsdlLayers();

import { useVisibleLayers, VisibleLayerType } from '@/composables/visibleLayers';

const {
  getLayerType
} = useVisibleLayers();

const props = defineProps({
    // TODO: give a proper name and define what is it exactly
    layerSources: {
        type: Array,
        default: () => [],
    },
});

const datasources = ref([]);

/**
 * TODO: review
 * Flatten all datasources' sources (sourceKeys) into a single-level list of
 * options to populate the Add Layer dropdown.
 */
const sourceOptions = computed(() => {
  const options = [];
  datasources.value.forEach((datasource) => {
    Object.keys(datasource.sources).forEach((sourceKey) => {
      options.push({
        value: `${datasource.id}::${sourceKey}`,
        label: `${datasource.name} - ${sourceKey}`,
        datasource,
        sourceKey,
      });
    });
  });
  return options;
});

onMounted(async () => {
  console.debug("Initializing Layer Studio component.");
  if (props.layerSources.length > 0) {
    datasources.value = initDatasources(props.layerSources);
  }
});

// TODO: refinement; update on layerSources change
watch(
  () => props.layerSources,
  (newLayerSources) => {
    datasources.value = initDatasources(newLayerSources);
  }
);

/**
 * Handle selection of a source (sourceKey) from the Add Layer dropdown for the
 * given datasource, loading it as a GeoJSON source.
 *
 * @param {DataSource} datasource
 * @param {string} sourceKey
 */
const onSelectSource = async (datasource, sourceKey) => {
  await datasource.addAsGeoJsonSource(sourceKey);
};

/**
 * TODO: rename method?
 * 
 * Populate the datasources array from the existing sources (the ones kept in esdlListRef)
 * or instantiate a new EsdlLayerSource.
 */
const initDatasources = (layerSources) => {
  let datasources = [];
  layerSources.forEach((source) => {
    if (getLayerType(source) === VisibleLayerType.ESDL) {
      const esId = source.es.id;
      const esdlTitle = source.es.title;
      const esdlSource = new EsdlLayerSource(esId, esdlTitle, 'ESDL');
      datasources.push(esdlSource);
    }
  });
  console.debug(layerSources, datasources); // TODO: remove
  return datasources;
};

/**
 * TODO: docstring
 */
class DataSource {
  constructor(
    id, name, type
  ) {
    this.id = id;
    this.name = name;
    // TODO: make type an enum (e.g. ESDL, WMS, etc.)
    this.type = type;
    // TODO: properly define sources, what is it exactly? a featureCollection?
    this.sources = {};
    // loadedSources is a map of sourceKey to GeoJSON FeatureCollection
    this.loadedSources = {};
    this.vizLayers = [];
    this.loading = false;
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

class EsdlLayerSource extends DataSource {
  constructor(id, name, type) {
    super(id, name, type);

    this._getEsdlAssetLayers();
    // this._addFeatureGroupLayerToMap();
  }

  /**
   * TODO: make it more generic and move to DataSource class?
   * Add a note that source contains a feature collection which is a leaflet object
   * 
   * Enrich the asset features of the given sourceKey with attribute (field) values returned 
   * from the backend and add them as a GeoJSON FeatureCollection to loadedSources.
   * 
   * @param {string} sourceKey ESDL asset type 
   */
  async addAsGeoJsonSource (sourceKey) {
    const layerFeatures = this.sources[sourceKey];
    const geoJsonFeaturePromises = layerFeatures.map(async (f) => {
      const g = f.toGeoJSON();

      const assetId = f.id;
      // TODO: this method is ESDL specific, but it could be made more generic if needed  
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
      [sourceKey]: geoJsonFeatureCollection 
    };

    console.debug(this.loadedSources);
  }

  /**
   * Initialize a new VisualizedLayer of the given sourceKey and add it to the vizLayers collection.
   * 
   * @param {string} sourceKey ESDL asset type
   */
  onAddLayerToMap (sourceKey) {
    const layerName = this._createUniqueVizLayerName(sourceKey);
    const features = this.loadedSources[sourceKey];
    // When instantiated, new layer will be added to the map.
    const vizLayer = new VisualizedLayer(this, layerName, features);
    this.vizLayers.push(vizLayer);
  }

  // ---------------------------- //
  // ----- Internal methods ----- //
  // ---------------------------- //

  /**
   * TODO: docstring
   * TODO: this method assumes data is coming multi_esdl object; maybe it should be made more generic?
   */
  async _getEsdlAssetLayers() {
    const esdlLayer = getEsdlFeatureGroupLayer(this.id, 'esdl_layer');
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

  // /**
  //  * TODO: remove esdlListRef dependency
  //  * Create viz layer to leaflet map if it does not exist yet. Don't bind viz layer to specific source.
  //  * Maybe this method should be moved to DataScource class?
  //  * 
  //  * Add a visualization feature group layer to the map if it does not exist.
  //  * NOTE: The "viz_layer" is initialized in multi_esdl.js
  //  */
  // _addFeatureGroupLayerToMap () {
  //   if (!Object.keys(esdlListRef[this.id].layers).includes("viz_layer")) {
  //     esdlListRef[this.id].layers["viz_layer"] = L.featureGroup().addTo(map);
  //   }
  // }
}
</script>
