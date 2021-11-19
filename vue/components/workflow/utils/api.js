import { genericErrorHandler } from "../../../utils/errors.js";
import {checkAndRefreshAuthStatus} from "../../../utils/status";


/**
 * Send a request to the workflow get_data proxy, which forwards it to a remote
 * service.
 *
 * @param remote_url (string) The URL to forward to.
 * @param request_params (object) The key-value query parameters.
 * @returns {Promise<Response|null>} The respoose, or null if nothing was received.
 */
export async function workflowGetData(remote_url, request_params) {
    request_params["url"] = remote_url;
    window.show_loader();
    try {
        const is_logged_in = await checkAndRefreshAuthStatus();
        if (is_logged_in) {
            const queryString = new URLSearchParams(request_params).toString();
            // Perform the request to the mapeditor backend, who will forward it to the service.
            const response = await fetch(`workflow/get_data?${queryString}`);
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
 * Send a request to the workflow post_data proxy, which forwards it to a remote
 * service.
 * 
 * Returns the response.
 */
export async function workflowPostData(remote_url, request_params) {
    window.show_loader();
    try {
        const is_logged_in = await checkAndRefreshAuthStatus();
        if (is_logged_in) {
            // Perform the request to the mapeditor backend, who will forward it to the service.
            const params = {
                remote_url: remote_url,
                request_params: request_params,
            };
            const response = await fetch("workflow/post_data", {
                method: "POST",
                body: JSON.stringify(params),
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


export async function workflowGetJsonForm(queryString, schemaName) {
    try {
        const is_logged_in = await checkAndRefreshAuthStatus();
        if (is_logged_in) {
            const response = await fetch(`workflow/get_options?${queryString}`)
            if (response.ok) {
                const data = await response.json();
                return data.definitions[schemaName];
            } else {
                throw response;
            }
        } else {
            return null;
        }
    } catch (e) {
        handleErrorResponse(e);
        return null;
    }
}

/**
 * Function to handle errors thrown by workflow api module.
 * @param e Error we throw ourselves (containing the response).
 * @returns {null}
 */
function handleErrorResponse(e) {
    console.error(e);
    if (e.status == 401) {
        const answer = confirm("Session has expired, reauthentication is necessary.\nPress Ok to go to the login page.");
        if (answer) {
            window.location.reload();
        }
    } else {
        let message;
        if (e.status) {
            message = "Invalid response received - status " + e.status + " " + e.statusText;
        } else {
            message = "An unknown error occurred while retrieving data. If the problem persists, please contact us."
        }
        genericErrorHandler(message);
    }
}