export const PubSubManager = {
  subscribers: [],

  subscribe: function(parent, callback) {
    this.subscribers.push({ parent: parent, callback: callback });
  },

  color: function(name) {
    // Notify subscribers of event.
    this.subscribers.forEach(function(subscriber) {
      subscriber.callback(name, subscriber.parent);
    });
  }
};

