/*
 * This work is based on original code developed and copyrighted by TNO 2025.
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
let toastNotificationInstance = null;

export const ToastNotificationType = Object.freeze({
    INFO: "info",
    SUCCESS: "success",
    WARNING: "warning",
    ERROR: "error",
});

export const ToastNotificationPlacement = Object.freeze({
    TOP: "top",
    TOP_LEFT: "topLeft",
    TOP_RIGHT: "topRight",
    BOTTOM: "bottom",
    BOTTOM_LEFT: "bottomLeft",
    BOTTOM_RIGHT: "bottomRight",
});

export const FileDownloadType = Object.freeze({
    EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
});

export class FileDownload {
    /**
     * FileDownload object to be passed to the notification
     *
     * @param {string} fileName
     * @param {string} contentB64string
     * @param {FileDownloadType} fileType
     */
    constructor(fileName, contentB64string, fileType) {
        this.fileName = fileName;
        this.contentB64string = contentB64string;
        this.fileType = fileType;
    }
}

export function useToastNotifications() {

    const setToastNotificationsInstance = (instance) => {
        toastNotificationInstance = instance;
    };

    /**
     * Show a notification, required data object:
     *
     * @param {string} title
     * @param {string} description
     * @param {ToastNotificationType} type
     * @param {ToastNotificationPlacement} placement
     * @param {number} closeAfterSeconds
     * @param {FileDownload} fileDownload optional file info which will be downloaded after the notification is given
     *
     */
    const showNotification = (
        title, description = "", type = "info", placement = "topRight", closeAfterSeconds = 5, fileDownload = null
    ) => {
        toastNotificationInstance.showNotification(title, description, type, placement, closeAfterSeconds, fileDownload);
    };

    return {
        setToastNotificationsInstance,
        showNotification,
    };
}
