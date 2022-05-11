import {checkAndRefreshAuthStatus} from "./status";
import {genericErrorHandler} from "./errors";


/**
 * Send a GET request to the backend.
 *
 * @param url (string) The URL to perform the request to.
 * @param request_params (object) The key-value query parameters.
 * @returns {Promise<Response|null>} The response, or null if nothing was received / an error occurs.
 */
export async function doGet(url, request_params) {
    window.show_loader();
    try {
        const is_logged_in = await checkAndRefreshAuthStatus();
        if (is_logged_in) {
            let target_url = url;
            if (request_params) {
                const queryString = new URLSearchParams(request_params).toString();
                target_url += `?${queryString}`;
            }
            const response = await fetch(target_url);
            if (response.ok) {
                return await response.json();
            } else {
                throw response;
            }
        } else {
            return null;
        }
    } catch (e) {
        handleErrorResponse(e);
        return null;
    } finally {
        window.hide_loader();
    }
}

/**
 * Send a POST request to the backend.
 *
 * @param url (string) The URL to perform the request to.
 * @param payload (any) The payload to POST to the API. Needs to be JSON.stringify-able.
 * @returns {Promise<Response|null>} The response, or null if nothing was received / an error occurs.
 */
export async function doPost(url, payload) {
    window.show_loader();
    try {
        const is_logged_in = await checkAndRefreshAuthStatus();
        if (is_logged_in) {
            const response = await fetch(url, {
                method: "POST",
                body: JSON.stringify(payload),
                headers: {
                    "Content-Type": "application/json",
                },
            });
            if (response.ok) {
                return response;
            } else {
                throw response;
            }
        } else {
            return null;
        }
    } catch (e) {
        handleErrorResponse(e);
        return null;
    } finally {
        window.hide_loader();
    }
}


/**
 * Function to handle errors thrown by api module.
 * @param e Error we throw ourselves (containing the response).
 * @returns {null}
 */
export function handleErrorResponse(e) {
    console.error(e);
    if (e.status === 401) {
        const answer = confirm("Session has expired, authentication is necessary.\nPress Ok to go to the login page.");
        if (answer) {
            window.location.reload();
        }
    } else {
        let message;
        if (e.message) {
            message = e.message;
        } else {
            if (e.status) {
                message = "Invalid response received - status " + e.status + " " + e.statusText;
            } else {
                message = "An unknown error occurred while retrieving data. If the problem persists, please contact us."
            }
        }
        genericErrorHandler(message);
    }
}
