import {computed, ref} from "vue";
import {MessageNames, PubSubManager} from "@/bridge";
import {renderPlanLayer} from "@/utils/planVisualization";

/**
 * @typedef {Object} PlanElement
 * @property {string} id
 * @property {string|null} name
 * @property {string} type
 */

/**
 * @typedef {Object} Plan
 * @property {string} id
 * @property {string|null} name
 * @property {string|null} description
 * @property {{id: string, name: string|null}} group
 * @property {PlanElement[]} elements
 */

export const PLAN_LAYER_NAME = "plan_layer";
export const NO_PLAN_ID = "__no_plan__";

const activeEsdlId = ref(window.active_layer_id);
/** @type {import('vue').Ref<Record<string, Plan[]>>} */
const plansByEsdlId = ref({});
const selectedPlanIdByEsdlId = ref({});

/**
 * Clear all Plan state for one ESDL.
 */
function clearPlansForEsdl(esdlId) {
    delete plansByEsdlId.value[esdlId];
    delete selectedPlanIdByEsdlId.value[esdlId];
}

/**
 * Clear Plan state for every loaded ESDL.
 */
function clearAllPlans() {
    Object.keys(plansByEsdlId.value).forEach((esdlId) => {
        clearPlansForEsdl(esdlId);
    });
    activeEsdlId.value = null;
}

/**
 * Render the selected Plan for an ESDL.
 */
function refreshPlan(esdlId = activeEsdlId.value) {
    if (!esdlId) {
        return;
    }

    const plans = plansByEsdlId.value[esdlId] || [];
    const selectedPlanId = selectedPlanIdByEsdlId.value[esdlId];
    const plan = plans.find((item) => item.id === selectedPlanId) || null;
    renderPlanLayer(esdlId, plan);
}

/**
 * Store Plans and keep the selection valid.
 */
function setPlans(esdlId, plans) {
    if (window.active_layer_id === esdlId) {
        activeEsdlId.value = esdlId;
    }
    let esdlPlans = [];
    if (Array.isArray(plans)) {
        esdlPlans = plans;
    }
    plansByEsdlId.value[esdlId] = esdlPlans;

    const selectedPlanId = selectedPlanIdByEsdlId.value[esdlId];
    if (
        selectedPlanId !== NO_PLAN_ID &&
        !esdlPlans.some((plan) => plan.id === selectedPlanId)
    ) {
        if (esdlPlans.length > 0) {
            selectedPlanIdByEsdlId.value[esdlId] = esdlPlans[0].id;
        } else {
            delete selectedPlanIdByEsdlId.value[esdlId];
        }
    }
}

PubSubManager.subscribe(MessageNames.PLANS, (name, message) => {
    setPlans(message.es_id, message.plans);
});

PubSubManager.subscribe(MessageNames.SELECT_ACTIVE_LAYER, (name, message) => {
    activeEsdlId.value = message.active_layer_id;
    refreshPlan(activeEsdlId.value);
});

PubSubManager.subscribe(MessageNames.VISIBLE_LAYER_VISIBILITY_CHANGED, (name, message) => {
    if (message.es_id in plansByEsdlId.value) {
        refreshPlan(message.es_id);
    }
});

PubSubManager.subscribe(MessageNames.REMOVE_ESDL_LAYER, (name, message) => {
    clearPlansForEsdl(message.es_id);
});

PubSubManager.subscribe(MessageNames.CLEAR_ESDL_LAYER_LIST, () => {
    clearAllPlans();
});

window.map.on("draw:edited", () => refreshPlan());
window.map.on("draw:deleted", () => refreshPlan());
window.map.on("zoomend", () => {
    Object.keys(plansByEsdlId.value).forEach((esdlId) => refreshPlan(esdlId));
});

/**
 * Manage Plan data and selection for loaded ESDLs.
 */
export function usePlans() {
    const activePlans = computed(() => {
        if (!activeEsdlId.value) {
            return [];
        }
        return plansByEsdlId.value[activeEsdlId.value] || [];
    });

    const selectedPlanId = computed({
        get: () => selectedPlanIdByEsdlId.value[activeEsdlId.value],
        set: (planId) => selectPlan(activeEsdlId.value, planId),
    });

    /**
     * Get the Plans available for an ESDL.
     */
    function getPlans(esdlId) {
        return plansByEsdlId.value[esdlId] || [];
    }

    /**
     * Select a Plan and refresh its map decorators.
     */
    function selectPlan(esdlId, planId) {
        const plans = plansByEsdlId.value[esdlId] || [];
        if (planId !== NO_PLAN_ID && !plans.some((plan) => plan.id === planId)) {
            return false;
        }
        selectedPlanIdByEsdlId.value[esdlId] = planId;
        refreshPlan(esdlId);
        return true;
    }

    return {
        activeEsdlId,
        activePlans,
        getPlans,
        selectedPlanId,
    };
}
