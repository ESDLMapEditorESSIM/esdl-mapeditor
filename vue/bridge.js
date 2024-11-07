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
});

export const PubSubManager = {
    subscriptions: {
        'ADD_BUILDING_TO_LAYER': [],
        'ADD_AREA_TO_LAYER': [],
        'USER_SETTINGS': [],
        'ASSET_PROPERTIES': [],
        'CARRIER_COLORS': [],
        'PROJECT_LOADED': [],
        'SOCKET_CONNECTED': [],
        'SELECT_ACTIVE_LAYER': [],
        'REMOVE_ESDL_LAYER': [],
        'CLEAR_ESDL_LAYER_LIST': [],
        'GEOJSON_PROCESSED': [],
        'NEW_ESDL': [],
        'KEY_ESCAPE': [],
    },

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
