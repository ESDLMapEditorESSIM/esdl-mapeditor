import { notification } from "ant-design-vue";

/**
 * Displays a toast notification.
 *
 * @param {string} level The level of the notification ("info", "warning", "error").
 * @param {string} description The description text of the notification.
 * @param {string} placement The placement of the notification. Default to "bottomRight".
 * @param {number} duration Notification duration in second. Default to 8.
 */
export const displayNotification = (
  level,
  description,
  placement = "bottomRight",
  duration = 8
) => {
  notification[level.toLowerCase()]({
    message: level.toUpperCase(),
    description: description,
    placement: placement,
    duration: duration,
  });
};
