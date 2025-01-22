import {useToast} from "vue-toastification";
import {useSocketIO} from "./socketio";
import {watchEffect} from "vue";

const toast = useToast();
const {socket} = useSocketIO();

const showToast = (message) => {
    toast.info(message);
}

watchEffect(() => {
    if (socket.value) {
        socket.value.on('toast_message', (message) => {
            if (message) {
                showToast(message);
            }
        });
    }
});

export function useToasts () {
    return {
        showToast
    }
}
