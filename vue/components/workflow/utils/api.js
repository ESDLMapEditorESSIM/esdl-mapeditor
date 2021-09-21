import { genericErrorHandler } from "../../../utils/errors.js";

/**
 * Send a request to the workflow post_data proxy, which forwards it to a remote
 * service.
 * 
 * Returns the response.
 */
export async function workflowPostData(remote_url, request_params) {
    window.show_loader();
    try {
        // Perform the request to the mapeditor backend, who will forward it to the service.
        const params = {
            remote_url: remote_url,
            request_params: request_params,
        };
        return await fetch("workflow/post_data", {
            method: "POST",
            body: JSON.stringify(params),
            headers: {
                "Content-Type": "application/json",
            },
        });
    } catch (e) {
        genericErrorHandler(e);
        return null;
    } finally {
        window.hide_loader();
    }
}


export async function workflowGetJsonForm(queryString, schemaName) {
    try {
        const response = await fetch(`workflow/get_options?${queryString}`)
        let data;
        if (response.ok) {
            data = await response.json();
        } else {
            throw new Error("No data received - status " + response.status);
        }
        if (data == null || data == undefined) {
            throw new Error("No data received - status " + response.status);
        }
        console.log(data);
        return data.definitions[schemaName];
    } catch (e) {
        genericErrorHandler(e);
        return null;
    }
}