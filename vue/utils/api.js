import {checkAndRefreshAuthStatus} from "./status";
import {genericErrorHandler} from "./errors";
import {useLoader} from "@/composables/loader";

const {startLoader, stopLoader} = useLoader();

/**
 * Send a GET request to the backend.
 *
 * @param url (string) The URL to perform the request to.
 * @param request_params (object) The key-value query parameters.
 * @returns {Promise<Response|null>} The response, or null if nothing was received / an error occurs.
 */
export async function doGet(url, request_params) {
    const loaderId = startLoader();
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
        stopLoader(loaderId);
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
    const loaderId = startLoader();
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
        stopLoader(loaderId);
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
    } else if (e.message) {
        genericErrorHandler(e.message);
    } else if (e.status) {
        // The backend may explain the failure (e.g. an unreachable service) in the response body.
        extractResponseMessage(e).then((message) => {
            genericErrorHandler(
                message || "Invalid response received - status " + e.status + " " + e.statusText
            );
        });
    } else {
        genericErrorHandler(
            "An unknown error occurred while retrieving data. If the problem persists, please contact us."
        );
    }
}


/**
 * Try to read an error message from a Response body.
 *
 * @param response (Response) The failed response.
 * @returns {Promise<string|null>} The message, or null if none could be determined.
 */
async function extractResponseMessage(response) {
    if (typeof response.json !== "function") {
        return null;
    }
    try {
        const body = await response.json();
        // 'detail' is what FastAPI-based services put their HTTPException message in.
        return body?.detail || body?.message || body?.error || null;
    } catch (err) {
        return null;
    }
}


/**
 * Fetches data from the specified resource using a WebSocket connection.
 * 
 * @param {string} path The path of the resource to fetch data from.
 * @param {Object} requestBody Optional. The request body to send with the WebSocket emit.
 * @returns {Promise<Array|Object>} A promise that resolves with the response or rejects with an error.
 */
export const fetchData = async (path, requestBody) => {
    while (window.socket === undefined) await new Promise(resolve => setTimeout(resolve, 10));
    const result = new Promise((resolve, reject) => {
        const callback = (response) => {
            if (response) {
                resolve(response);
            } else {
                reject(new Error(`An unknown error occurred while fetching data from ${path}`));
            }
        };

        if (requestBody) {
            window.socket.emit(path, requestBody, callback);
        } else {
            window.socket.emit(path, callback);
        }
    });
    return result;
};
