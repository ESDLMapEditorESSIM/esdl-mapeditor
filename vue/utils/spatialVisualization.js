
const mapEcoreTypeToJsType = (ecoreType) => {
    switch (ecoreType) {
        case 'EString': return 'string';
        case 'EEnum': return 'string';
        case 'EInt': return 'number';
        case 'EDouble': return 'number';
        case 'EBoolean': return 'boolean';
        case 'EDate': return 'date';
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

// TODO: improve performance
const getAssetFields = async(esId, assetId) => {
    try {
      const response = await fetch(`/spatial_visualization/asset_fields/${esId}/${assetId}`);
      const fields = await response.json();
  
      const parsedFields = fields.map((f) => {
        const jsType = mapEcoreTypeToJsType(f.type);
        let parsedValue = f.value;
        if (f.value !== null) {
          parsedValue = parseFieldValue(f.value, jsType);
        }
        return {
          ...f,
          type: jsType,
          value: parsedValue,
        };
      });
  
      return parsedFields;
    } catch (error) {
      console.error(error);
    }
};

// TODO: avoid duplicated code (ESDLAnalytics.vue)
/**
 * Generates a colorscale based on the specified palette and number of colors.
 * 
 * @param {string} palette The type of color palette to use. Options include:
 *                         'Qualitative', 'Diverging', 'Sequential', 'Rainbow', and 'Default'.
 * @param {number} numColors The number of colors to generate in the colorscale.
 * @param {Array} defaultColors Default colors array (pie_chart_color_list is defined in area_building_layer.js)
 * @returns {Array} An array of colorscale values.
 */
const generateColorscale = (palette, numColors, defaultColors = pie_chart_color_list) => {
    let colorscale = defaultColors;
    switch (palette) {
      case 'Qualitative':
        // The maximum number of colors: 65
        colorscale = window.palette('mpn65', numColors > 65 ? 65 : numColors);
        break;
      case 'Diverging': 
        colorscale = window.palette('tol-dv', numColors);
        break;
      case 'Sequential':
        colorscale = window.palette('tol-sq', numColors);
        break;
      case 'Rainbow':
        colorscale = window.palette('tol-rainbow', numColors);
        break;
      case 'Default':
      default:
    }
    return colorscale.map(c => c.startsWith('#') ? c : `#${c}`);
};

export { getAssetFields, generateColorscale };

