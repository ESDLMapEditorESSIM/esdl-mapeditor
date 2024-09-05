/**
 * Bridging functionality, to bridge the gap between classic JS / JQuery and Vue.
 */


export const MessageNames = Object.freeze({
    ADD_BUILDING_TO_LAYER: 'ADD_BUILDING_TO_LAYER',
    ADD_AREA_TO_LAYER: 'ADD_AREA_TO_LAYER',
    USER_SETTINGS: 'USER_SETTINGS',
    ASSET_PROPERTIES: 'ASSET_PROPERTIES',
    CARRIER_COLORS: 'CARRIER_COLORS',
    SOCKET_CONNECTED: 'SOCKET_CONNECTED',
    SELECT_ACTIVE_LAYER: 'SELECT_ACTIVE_LAYER',
});

export const PubSubManager = {
    subscriptions: {
        'ADD_BUILDING_TO_LAYER': [],
        'ADD_AREA_TO_LAYER': [],
        'USER_SETTINGS': [],
        'ASSET_PROPERTIES': [],
        'CARRIER_COLORS': [],
        'SOCKET_CONNECTED': [],
        'SELECT_ACTIVE_LAYER': [],
    },

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