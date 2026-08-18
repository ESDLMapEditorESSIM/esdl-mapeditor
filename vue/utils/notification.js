import { notification } from "ant-design-vue";
import { watchEffect } from "vue";
import { useSocketIO } from "@/composables/socketio";
import { download_binary_file_from_base64_str_with_type } from "@/utils/files";

/**
 * @enum {string}
 */
export const NotificationType = Object.freeze({
  INFO: "info",
  SUCCESS: "success",
  WARNING: "warning",
  ERROR: "error",
});

/**
 * @enum {string}
 */
export const NotificationPlacement = Object.freeze({
  TOP: "top",
  TOP_LEFT: "topLeft",
  TOP_RIGHT: "topRight",
  BOTTOM: "bottom",
  BOTTOM_LEFT: "bottomLeft",
  BOTTOM_RIGHT: "bottomRight",
});

/**
 * Displays a toast notification.
 *
 * @param {string} [level=NotificationType.INFO] The notification level.
 * @param {string} description The description text of the notification.
 * @param {object} options Notification title, placement, and duration.
 */
export const displayNotification = (
  level = NotificationType.INFO,
  description = "",
  options = {}
) => {
  const notificationType = String(level).toLowerCase();
  if (!Object.values(NotificationType).includes(notificationType)) {
    console.warn(`Unknown notification type: ${level}`);
    return;
  }

  let placement = options.placement ?? NotificationPlacement.BOTTOM_RIGHT;
  if (!Object.values(NotificationPlacement).includes(placement)) {
    placement = NotificationPlacement.BOTTOM_RIGHT;
  }

  let duration = options.duration ?? 8;
  if (typeof duration !== "number" || duration < 0) {
    duration = 8;
  }

  notification[notificationType]({
    message: options.title ?? notificationType.toUpperCase(),
    description: description,
    placement: placement,
    duration: duration,
  });
};

/**
 * The backend can send notification data. We listen to the socket messages
 * and display notification.
 */
function showNotificationFromBackend(data) {
  if (!data || typeof data !== "object") {
    return;
  }

  const fileDownload = data.file_download;
  if (fileDownload) {
    // TODO: We kind of abuse this message to double as a download command.
    download_binary_file_from_base64_str_with_type(
      fileDownload.content_b64string,
      fileDownload.file_name,
      fileDownload.file_type
    );
  }

  displayNotification(data.type, data.description, {
    title: data.title,
    placement: data.placement,
    duration: data.close_after_seconds,
  });
}

export function registerNotificationListeners() {
  const { subscribe, socket } = useSocketIO();

  subscribe("toast_message", (message) => {
    if (message) {
      displayNotification(NotificationType.INFO, message);
    }
  });
  subscribe("toast_notification", showNotificationFromBackend);

  watchEffect(() => {
    if (socket.value) {
      socket.value.emit("toast_notifications_service_ready");
    }
  });
}
