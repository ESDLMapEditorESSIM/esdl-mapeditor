/**
 * Bridging functionality, to bridge the gap between classic JS / JQuery and Vue.
 */


export const MessageNames = Object.freeze({
    ADD_BUILDING_TO_LAYER: 'ADD_BUILDING_TO_LAYER',
    ADD_AREA_TO_LAYER: 'ADD_AREA_TO_LAYER',
    USER_SETTINGS: 'USER_SETTINGS',
    ASSET_PROPERTIES: 'ASSET_PROPERTIES',
    CARRIER_COLORS: 'CARRIER_COLORS',
    PROJECT_LOADED: 'PROJECT_LOADED',
    SOCKET_CONNECTED: 'SOCKET_CONNECTED',
    SELECT_ACTIVE_LAYER: 'SELECT_ACTIVE_LAYER',
    REMOVE_ESDL_LAYER: 'REMOVE_ESDL_LAYER',
    CLEAR_ESDL_LAYER_LIST: 'CLEAR_ESDL_LAYER_LIST',
    VISIBLE_LAYER_VISIBILITY_CHANGED: 'VISIBLE_LAYER_VISIBILITY_CHANGED',
    GEOJSON_PROCESSED: 'GEOJSON_PROCESSED',
    NEW_ESDL: 'NEW_ESDL',
    KEY_ESCAPE: 'KEY_ESCAPE',
    ESDL_LOAD_STARTED: 'ESDL_LOAD_STARTED',
    ESDL_LOAD_FAILED: 'ESDL_LOAD_FAILED',
    // The below are all the mandatory parts of loading a single ESDL.
    CREATE_NEW_ESDL_LAYER: 'CREATE_NEW_ESDL_LAYER',
    SET_ACTIVE_LAYER_ID: 'SET_ACTIVE_LAYER_ID',
    CARRIER_LIST: 'CARRIER_LIST',
    PLANS: 'PLANS',
    ADD_BUILDING_OBJECTS: 'ADD_BUILDING_OBJECTS',
    ADD_ESDL_OBJECTS: 'ADD_ESDL_OBJECTS',
    AREA_BLD_LIST: 'AREA_BLD_LIST',
    ADD_CONNECTIONS: 'ADD_CONNECTIONS',
    ADD_NOTES: 'ADD_NOTES',
    BRING_KPIS_TO_FRONT: 'BRING_KPIS_TO_FRONT',
    REMOVE_LAYER: 'REMOVE_LAYER',
});

export const PubSubManager = {
    // Make a list of all the subscriptions.
    subscriptions: Object.keys(MessageNames).reduce((acc, key) => {
        acc[MessageNames[key]] = [];
        return acc;
    }, {}),

    subscribe: function (name, callback) {
        if (!this.subscriptions[name]) {
            console.warn("No subscriptions found for " + name);
            return null;
        } else {
            const id = Math.random().toString(36).substring(2, 9);
            this.subscriptions[name].push({callback: callback, id: id});
            return id;
        }
    },

    broadcast: function (name, message) {
        const subscribers = this.subscriptions[name];
        if (!subscribers) {
            console.warn("No subscribers found for " + name);
            return;
        }
        subscribers.forEach(function (subscriber) {
            subscriber.callback(name, message);
        });
    },

    unsubscribe: function (id) {
        if (!id) {
            return;
        }
        for (const name in this.subscriptions) {
            const subscribers = this.subscriptions[name];
            const index = subscribers.findIndex(subscriber => subscriber.id === id);
            if (index !== -1) {
                subscribers.splice(index, 1);
                return;
            }
        }
        console.warn("No subscription found with id " + id);
    },

    listSubscriptions: function () {
        const activeSubscriptions = {};
        for (const name in this.subscriptions) {
            activeSubscriptions[name] = this.subscriptions[name].map(subscriber => subscriber.id);
        }
        return activeSubscriptions;
    }
};

window.PubSubManager = PubSubManager;