import { defaultColorScheme } from "@/utils/visualization";
import { fetchData } from "@/utils/api";

/** Valid field data types that can be used for layer styling. */
const FieldType = Object.freeze({
  BOOLEAN: 'boolean',
  STRING:  'string',
  NUMBER:  'number',
});

/** Visual style mode applied to a field. */
const StyleType = Object.freeze({
  SINGLE_COLOR:      'singleColor',
  CATEGORICAL_COLOR: 'categoricalColor',
  SIZE:              'size',
  GRADIENT_COLOR:    'gradientColor',
  COLOR_AND_SIZE:    'colorAndSize',
});

/** How fill/line color is derived per feature. */
const ColorMode = Object.freeze({
  FIXED:       'fixed',
  CATEGORICAL: 'categorical',
  GRADIENT:    'gradient',
});

/** How symbol size is derived per feature. */
const SizeMode = Object.freeze({
  FIXED:     'fixed',
  GRADUATED: 'graduated',
});

/** Named color palettes available for styling. */
const PaletteName = Object.freeze({
  DEFAULT:     'Default',
  QUALITATIVE: 'Qualitative',
  DIVERGING:   'Diverging',
  SEQUENTIAL:  'Sequential',
  RAINBOW:     'Rainbow',
});

const mapEcoreTypeToJsType = (ecoreType) => {
    switch (ecoreType) {
        case 'EString': return FieldType.STRING;
        case 'EEnum': return FieldType.STRING;
        case 'EInt': return FieldType.NUMBER;
        case 'EDouble': return FieldType.NUMBER;
        case 'EBoolean': return FieldType.BOOLEAN;
        case 'EDate': return 'date'; // not a supported style field type
        default:
        console.error(`Unsupported Ecore type: ${ecoreType}`);
        return ecoreType;
    }
};

const parseFieldValue = (value, type) => {
    switch (type) {
      case 'number':
        return isNaN(Number(value)) ? null : Number(value);
      case 'boolean':
        if (value.toLowerCase() === 'true') return true;
        if (value.toLowerCase() === 'false') return false;
        return null; // Return null if not a valid boolean
      case 'string':
        return value.toString();
      default:
        console.error(`Unsupported type: ${type}`);
        return value;
    }
};

const getAssetFields = async(esId, assetId) => {
    try {
      const attributes = await fetchData('spatial_visualization/asset_fields', { es_id: esId, asset_id: assetId });

      return attributes.map((attr) => {
        const jsType = mapEcoreTypeToJsType(attr.type);
        return {
          ...attr,
          type: jsType,
          value: attr.value !== null ? parseFieldValue(attr.value, jsType) : attr.value,
        };
      });
    } catch (error) {
      console.error(error);
      return [];
    }
};

/**
 * Fetch the complete reference field tree for the given assets in a single pass.
 *
 * The tree carries ref field names and types only; values are
 * fetched by getRefFieldValues() separately once a leaf is selected.
 *
 * @param {string} esId - Energy system ID.
 * @param {string[]} assetIds - Assets the tree is built over.
 * @returns {Promise<Array>} Nested tree nodes; leaves carry { value, display, type }.
 */
const getRefFieldSchema = async (esId, assetIds) => {
  const refFieldSchemaRequest = {
    es_id: esId,
    asset_ids: assetIds,
  };
  try {
    const data = await fetchData('spatial_visualization/ref_field_schema', refFieldSchemaRequest);
    const nodes = [];

    // Parse costInformation dict into a-tree-select nodes; KPIs ignored for now.
    const costInfo = data?.ref?.costInformation;
    if (costInfo && typeof costInfo === 'object') {
      const children = Object.entries(costInfo)
        .map(([refName, attrs]) => {
          const leaves = (attrs || []).map((a) => {
            const jsType = mapEcoreTypeToJsType(a.attrType);
            return {
              value: a.path,
              label: `${a.attr} [${jsType}]`,
              display: `Cost Information > ${refName} > ${a.attr}`,
              attrType: a.attrType,
              type: jsType,
              disabled: !Object.values(FieldType).includes(jsType),
              isLeaf: true,
            };
          });
          if (!leaves.length) return null;
          return { value: `costInformation:${refName}`, label: refName, selectable: false, children: leaves };
        })
        .filter(Boolean);
      if (children.length) {
        nodes.push({ value: 'costInformation', label: 'Cost Information', selectable: false, children });
      }
    }

    return nodes;
  } catch (error) {
    console.error('Error fetching ref field schema:', error);
    throw error;
  }
};

/**
 * Fetch the values of a scalar ref field in bulk for the given assets.
 *
 * @param {string} esId - Energy system ID.
 * @param {string[]} assetIds - Array of asset IDs to fetch values for.
 * @param {string} path - Opaque path token from a leaf node's `value`.
 * @returns {Promise<Object>} Map of { assetId: { value, type } | null }.
 *   The `value` is already parsed to the correct JS type; `type` is a {@link FieldType} value.
 */
const getRefFieldValues = async (esId, assetIds, path) => {
  const refFieldValuesRequest = {
    es_id: esId,
    asset_ids: assetIds,
    path: path,
  };
  const data = await fetchData('spatial_visualization/ref_field_values', refFieldValuesRequest);
  // data: { assetId: { value: string | null, type: EcoreTypeName } | null }

  const result = {};
  for (const [assetId, entry] of Object.entries(data)) {
      if (entry === null || entry.type === null) {
          result[assetId] = null;
      } else {
          const jsType = mapEcoreTypeToJsType(entry.type);
          result[assetId] = {
              value: entry.value !== null ? parseFieldValue(entry.value, jsType) : null,
              type: jsType,
          };
      }
  }
  return result;
};
 
/**
 * Generates a colorscale based on the specified palette and number of colors.
 * 
 * @param {string} palette The type of color palette to use. Use {@link PaletteName} values.
 * @param {number} numColors The number of colors to generate in the colorscale.
 * @param {Array} defaultColors Default color scheme array.
 * @returns {Array} An array of colorscale values.
 */
const generateColorscale = (palette, numColors = 12, defaultColors = defaultColorScheme) => {
    let colorscale = defaultColors.slice(0, numColors);
    switch (palette) {
      case PaletteName.QUALITATIVE:
        // The maximum number of colors: 65
        colorscale = window.palette('mpn65', numColors > 65 ? 65 : numColors);
        break;
      case PaletteName.DIVERGING:
        colorscale = window.palette('tol-dv', numColors);
        break;
      case PaletteName.SEQUENTIAL:
        colorscale = window.palette('tol-sq', numColors);
        break;
      case PaletteName.RAINBOW:
        colorscale = window.palette('tol-rainbow', numColors);
        break;
      case PaletteName.DEFAULT:
      default:
    }
    return colorscale.map(c => c.startsWith('#') ? c : `#${c}`);
};

/**
 * @param {string} geometryType Leaflet geometry type
 * @param {FeatureStyle} style a basic feature style object
 */
const setLeafletFeatureStyle = (geometryType, style = {}) => {
  const {
    color = '#1f78b4',
    opacity = 1,
    radius = 5,
    weight = 2,
    stroke = false
  } = style;

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

export { getAssetFields, getRefFieldSchema, getRefFieldValues, generateColorscale, setLeafletFeatureStyle, FieldType, StyleType, ColorMode, SizeMode, PaletteName };

