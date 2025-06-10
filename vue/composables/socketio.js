/*
 * This work is based on original code developed and copyrighted by TNO 2020.
 * Subsequent contributions are licensed to you by the developers of such code and are
 * made available to the Project under one or several contributor license agreements.
 *
 * This work is licensed to you under the Apache License, Version 2.0.
 * You may obtain a copy of the license at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Contributors:
 *     TNO         - Initial implementation
 * Manager:
 *     TNO
 */

import {ref, watchEffect} from "vue";
import {MessageNames, PubSubManager} from "../bridge";
import {isDebug} from "../utils/utils";

/**
 * @typedef {import('socket.io-client').Socket} Socket
 */

/** @type {import('vue').Ref<Socket|null>} */
export const socket = ref(null);

PubSubManager.subscribe(MessageNames.SOCKET_CONNECTED, (msg, incomingSocket) => {
    socket.value = incomingSocket;
    if (isDebug()) {
        incomingSocket.onAny((event, ...args) => {
            console.debug(`<<< ${event} (args: ${args}`);
        });
    }
});


export function useSocketIO() {
    function subscribe(event, callback) {
      watchEffect(() => {
        if (socket.value) {
          console.debug("Subscribing to", event);
          socket.value.on(event, callback);
        }
      });
    }

    return {
        subscribe,
        socket
    };
}
