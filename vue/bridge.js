/**
 * Bridging functionality, to bridge the gap between classic JS / JQuery and Vue.
 */


export const MessageNames = Object.freeze({
    ADD_FEATURE_TO_LAYER: 'ADD_FEATURE_TO_LAYER',
    USER_SETTINGS: 'USER_SETTINGS',
    ASSET_PROPERTIES: 'ASSET_PROPERTIES',
    CARRIER_COLORS: 'CARRIER_COLORS',
    PROJECT_LOADED: 'PROJECT_LOADED',
    SOCKET_CONNECTED: 'SOCKET_CONNECTED',
});

export const PubSubManager = {
  subscriptions: {
    'ADD_FEATURE_TO_LAYER': [],
    'USER_SETTINGS': [],
    'ASSET_PROPERTIES': [],
    'CARRIER_COLORS': [],
    'PROJECT_LOADED': [],
    'SOCKET_CONNECTED': [],
  },

  subscribe: function(name, callback) {
    this.subscriptions[name].push({ callback: callback });
  },

  broadcast: function (name, message) {
    const subscribers = this.subscriptions[name];
    subscribers.forEach(function(subscriber) {
      subscriber.callback(name, message);
    });

  },

};

window.PubSubManager = PubSubManager
