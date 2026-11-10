const PLAN_PANE_NAME = "planPane";
export const PLAN_COLOR = "#00a86b";
const PLAN_PANE_Z_INDEX = 340;
const PLAN_OPACITY = 0.95;
const PLAN_MARKER_RADIUS = 17;
const PLAN_MARKER_WEIGHT = 5;
const PLAN_POLYGON_WEIGHT = 7;
const PLAN_GEOMETRY_WEIGHT = 3;
const PLAN_GEOMETRY_HOVER_WEIGHT = 5;
const PLAN_GEOMETRY_DASH_ARRAY = "8 6";
const PLAN_GEOMETRY_FILL_OPACITY = 0.12;
const PLAN_GEOMETRY_HOVER_FILL_OPACITY = 0.24;
const PLAN_POLYLINE_OUTLINE_WIDTH = 8;
const BUILDING_TYPES = new Set([
    "AggregatedBuilding",
    "Building",
]);

/**
 * Returns the Leaflet layer from a layer lookup result.
 */
function normalizeLayer(layer) {
    if (Array.isArray(layer)) {
        return layer[1];
    }
    return layer;
}

/**
 * Finds a matching layer that is currently visible on the map.
 */
function findVisibleLayer(esdlId, layerName, elementId, type) {
    const layer = normalizeLayer(window.find_layer_by_id(esdlId, layerName, elementId, type));
    if (layer && window.map.hasLayer(layer)) {
        return layer;
    }
    return null;
}

/**
 * Finds the visible source layer for a plan element.
 */
function findPlanElementLayer(esdlId, element) {
    if (BUILDING_TYPES.has(element.type)) {
        return findVisibleLayer(esdlId, "bld_layer", element.id);
    }
    if (element.type === "Pipe") {
        return findVisibleLayer(esdlId, "esdl_layer", element.id);
    }

    return findVisibleLayer(esdlId, "esdl_layer", element.id, "polygon") ||
        findVisibleLayer(esdlId, "esdl_layer", element.id, "marker") ||
        findVisibleLayer(esdlId, "esdl_layer", element.id);
}

/**
 * Creates the pane used for plan geometry and highlights.
 */
function ensurePlanPane() {
    let pane = window.map.getPane(PLAN_PANE_NAME);
    if (!pane) {
        pane = window.map.createPane(PLAN_PANE_NAME);
        pane.style.zIndex = PLAN_PANE_Z_INDEX;
    }
    pane.style.pointerEvents = "";
}

/**
 * Keeps the plan casing visible outside the zoom-scaled source line.
 */
function getPlanPolylineWeight(layer) {
    let sourceWeight = layer.options.weight;
    if (layer._path) {
        const renderedWeight = Number.parseFloat(window.getComputedStyle(layer._path).strokeWidth);
        if (Number.isFinite(renderedWeight)) {
            sourceWeight = renderedWeight;
        }
    }
    return sourceWeight + PLAN_POLYLINE_OUTLINE_WIDTH;
}

/**
 * Creates a highlight matching the source layer geometry.
 */
function createPlanHighlight(layer) {
    const options = {
        color: PLAN_COLOR,
        interactive: false,
        opacity: PLAN_OPACITY,
        pane: PLAN_PANE_NAME,
    };

    if (layer instanceof window.L.Marker || layer instanceof window.L.CircleMarker) {
        return window.L.circleMarker(layer.getLatLng(), {
            ...options,
            fill: false,
            radius: PLAN_MARKER_RADIUS,
            weight: PLAN_MARKER_WEIGHT,
        });
    }
    if (layer instanceof window.L.Polygon) {
        return window.L.polygon(layer.getLatLngs(), {
            ...options,
            fill: false,
            weight: PLAN_POLYGON_WEIGHT,
        });
    }
    if (layer instanceof window.L.Polyline) {
        return window.L.polyline(layer.getLatLngs(), {
            ...options,
            lineCap: "round",
            weight: getPlanPolylineWeight(layer),
        });
    }
    return null;
}

/**
 * Creates a layer for the geometry stored on the Plan itself.
 */
function createPlanGeometry(geometry) {
    if (!geometry) {
        return null;
    }

    const options = {
        color: PLAN_COLOR,
        dashArray: PLAN_GEOMETRY_DASH_ARRAY,
        fill: true,
        fillOpacity: PLAN_GEOMETRY_FILL_OPACITY,
        interactive: true,
        opacity: PLAN_OPACITY,
        pane: PLAN_PANE_NAME,
        weight: PLAN_GEOMETRY_WEIGHT,
    };
    return window.L.geoJSON(geometry, {
        pointToLayer: (feature, latLng) => window.L.circleMarker(latLng, {
            ...options,
            radius: PLAN_MARKER_RADIUS,
        }),
        style: options,
    });
}

/**
 * Renders highlights for the elements in the selected plan.
 * @param {string} esdlId
 * @param {import('@/composables/plans').Plan|null} plan
 */
export function renderPlanLayer(esdlId, plan) {
    const planLayer = window.esdl_list?.[esdlId]?.layers?.plan_layer;
    if (!planLayer) {
        return;
    }

    planLayer.clearLayers();
    if (!plan || !window.map.hasLayer(planLayer)) {
        return;
    }

    ensurePlanPane();
    const geometryLayer = createPlanGeometry(plan.geometry);
    if (geometryLayer) {
        window.bindMapObjectPopup(geometryLayer, () => plan);
        geometryLayer.on("mouseover", () => {
            geometryLayer.setStyle({
                fillOpacity: PLAN_GEOMETRY_HOVER_FILL_OPACITY,
                weight: PLAN_GEOMETRY_HOVER_WEIGHT,
            });
        });
        geometryLayer.on("mouseout", () => {
            geometryLayer.setStyle({
                fillOpacity: PLAN_GEOMETRY_FILL_OPACITY,
                weight: PLAN_GEOMETRY_WEIGHT,
            });
        });
        geometryLayer.on("click", (event) => {
            window.object_properties_window(plan.id);
            window.L.DomEvent.stopPropagation(event);
        });
        planLayer.addLayer(geometryLayer);
    }
    plan.elements.forEach((element) => {
        const sourceLayer = findPlanElementLayer(esdlId, element);
        if (!sourceLayer) {
            return;
        }

        const highlight = createPlanHighlight(sourceLayer);
        if (highlight) {
            planLayer.addLayer(highlight);
        }
    });
}
