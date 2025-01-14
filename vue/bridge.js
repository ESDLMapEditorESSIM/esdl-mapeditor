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
    GEOJSON_PROCESSED: 'GEOJSON_PROCESSED',
    NEW_ESDL: 'NEW_ESDL',
    KEY_ESCAPE: 'KEY_ESCAPE',
    // The below are all the mandatory parts of loading a single ESDL.
    CREATE_NEW_ESDL_LAYER: 'CREATE_NEW_ESDL_LAYER',
    SET_ACTIVE_LAYER_ID: 'SET_ACTIVE_LAYER_ID',
    CARRIER_LIST: 'CARRIER_LIST',
    ADD_BUILDING_OBJECTS: 'ADD_BUILDING_OBJECTS',
    ADD_ESDL_OBJECTS: 'ADD_ESDL_OBJECTS',
    AREA_BLD_LIST: 'AREA_BLD_LIST',
    ADD_CONNECTIONS: 'ADD_CONNECTIONS',
    ADD_NOTES: 'ADD_NOTES',
    BRING_KPIS_TO_FRONT: 'BRING_KPIS_TO_FRONT',
});

export const PubSubManager = {
    // Make a list of all the subscriptions.
    subscriptions: Object.keys(MessageNames).reduce((acc, key) => {
        acc[MessageNames[key]] = [];
        return acc;
    }, {}),

    subscribe: function (name, callback) {
        if (!this.subscriptions[name]) {
            console.warn("No subscriptions found for " + name)
        } else {
            this.subscriptions[name].push({callback: callback});
        }
    },

    broadcast: function (name, message) {
        const subscribers = this.subscriptions[name];
        subscribers.forEach(function (subscriber) {
            subscriber.callback(name, message);
        });

    },

};

window.PubSubManager = PubSubManager
