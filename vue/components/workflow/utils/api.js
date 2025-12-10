import {handleErrorResponse} from "../../../utils/api";
import {checkAndRefreshAuthStatus} from "../../../utils/status";


/**
 * Send a request to the workflow get_data proxy, which forwards it to a remote
 * service.
 *
 * @param remote_url (string) The URL to forward to.
 * @param request_params (object) The key-value query parameters.
 * @param headers (object) The headers to send with the request.
 * @returns {Promise<Response|null>} The respoose, or null if nothing was received.
 */
export async function workflowGetData(remote_url, request_params, headers) {
    window.show_loader();
    request_params["url"] = remote_url;
    if (!headers) {
        headers = {};
    }
    try {
        const is_logged_in = await checkAndRefreshAuthStatus();
        if (is_logged_in) {
            const queryString = new URLSearchParams(request_params).toString();
            // Perform the request to the mapeditor backend, who will forward it to the service.
            const response = await fetch(`workflow/get_data?${queryString}`, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    ...headers,
                },
            });
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
export async function workflowPostData(remote_url, body, headers, request_params={}) {
    window.show_loader();
    if (!headers) {
        headers = {};
    }
    try {
        const is_logged_in = await checkAndRefreshAuthStatus();
        if (is_logged_in) {
            // Perform the request to the mapeditor backend, who will forward it to the service.
            const params = {
                remote_url: remote_url,
                request_params: request_params,
                body: body,
            };
            const response = await fetch("workflow/post_data", {
                method: "POST",
                body: JSON.stringify(params),
                headers: {
                    "Content-Type": "application/json",
                    ...headers,
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


export async function getJsonForm(url) {
    try {
        const is_logged_in = await checkAndRefreshAuthStatus();
        if (is_logged_in) {
            const response = await fetch(url)
            if (response.ok) {
                const data = await response.json();
                return data;
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


export async function postJsonForm(url, body) {
    window.show_loader();
    try {
        const is_logged_in = await checkAndRefreshAuthStatus();
        if (is_logged_in) {
            const response = await fetch(url, {
                method: "POST",
                body: JSON.stringify(body),
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