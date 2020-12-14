/**
 * Bridging functionality, to bridge the gap between classic JS / JQuery and Vue.
 */


export const MessageNames = Object.freeze({
    ADD_FEATURE_TO_LAYER: 'ADD_FEATURE_TO_LAYER',
});

export const PubSubManager = {
  subscriptions: {
    'ADD_FEATURE_TO_LAYER': [],
  },

  subscribe: function(name, callback) {
    console.log(`Adding subscriber for ${name}`)
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
