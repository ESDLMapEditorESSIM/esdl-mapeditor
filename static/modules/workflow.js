import { render_button, render_btn_group } from './buttons.js';
import { render_form, render_form_field, render_submit } from './form.js';
import { download_binary_file_from_base64_str } from './files.js';

const WorkflowStepTypes = Object.freeze({
    CHOICE: 'choice',
    FORM: 'form',
    MULTI_SELECT_QUERY: 'multi-select-query',
    SELECT_QUERY: 'select-query',
    SERVICE: 'service',
    DOWNLOAD_FILE: 'download_file',
    UPLOAD_FILE: 'upload_file',
    GET_DATA: 'get_data',
    CALL_JS_FUNCTION: 'call_js_function',
});

// The currently active workflow.
export let current_workflow = null;

/**
 * Start a brand new workflow.
 * 
 * @param {*} service_index 
 * @param {*} service 
 */
export function start_new_workflow(service_index, service) {
    current_workflow = new Workflow(service_index, service);
    return current_workflow;
}

/**
 * If the workflow results in a service, return this object.
 */
export class ResultService {
    constructor(service_obj, state_params) {
        this.service_obj = service_obj;
        this.state_params = state_params;
    }
}

export class Workflow {
    constructor(service_index, service) {
        // The array index in the list sent from the server.
        this.service_index = service_index;
        this.service = service;
        this.workflow_step = service.workflow[0];
        this.step_idx = 0;
        this.state = {};
    }

    /**
     * Show a workflow service, designed to be called from esdl_services.js:show_service_settings.
     * 
     * Optionally returns a service object, for which show_service_settings should do further processing.
     */
    show_service = () => {
        const service_settings_div = document.getElementById('service_settings_div');
        try {

            service_settings_div.innerHTML += `
            <h3>${this.workflow_step.name}</h3>
            <p>${this.workflow_step.description}</p>
        `;

            let result_service = null;
            // A workflow consists of multiple steps. Every step consists of a service, plus metadata.
            if (this.workflow_step.type === WorkflowStepTypes.CHOICE) {
                service_settings_div.innerHTML += this.render_choice();
            } else if (this.workflow_step.type === WorkflowStepTypes.SELECT_QUERY) {
                this.handle_select_query_step(service_settings_div, this.workflow_step['multiple']);
            } else if (this.workflow_step.type === WorkflowStepTypes.FORM) {
                const form_elements = [];
                for (const field of this.workflow_step.fields) {
                    form_elements.push(render_form_field(field.type, field.target_variable, field.description));
                }
                service_settings_div.innerHTML += render_form(this.get_form_id(), form_elements)
                service_settings_div.innerHTML += this.render_prev_next(false);
                $(`form#${this.get_form_id()}`).submit(event => this.submit_form(event))
            } else if (this.workflow_step.type === WorkflowStepTypes.DOWNLOAD_FILE) {
                this.handle_download_file_step(service_settings_div);
            } else if (this.workflow_step.type === WorkflowStepTypes.UPLOAD_FILE) {
                this.handle_upload_file_step(service_settings_div);
            } else if (this.workflow_step.type === WorkflowStepTypes.GET_DATA) {
                this.handle_get_data_step(service_settings_div);
            } else if (this.workflow_step.type === WorkflowStepTypes.CALL_JS_FUNCTION) {
                this.handle_call_js_function_step(service_settings_div);
                service_settings_div.innerHTML += this.render_prev_next();
            } else if (this.workflow_step.type === WorkflowStepTypes.SERVICE) {
                // Continue with the service. Provide state params.
                let params = this.get_from_state(this.workflow_step.state_params);
                window.render_service(this.workflow_step['service'], service_settings_div, params);
                service_settings_div.innerHTML += this.render_prev_next();
            } else {
                // Not sure what to do, so do nothing.
                service_settings_div.innerHTML += 'Unknown step type.';
                return null;
            }

            return result_service;
        } catch (e) {
            console.error(e, e.stack);
            this._error_handler(service_settings_div);
        }
    }


    handle_get_data_step(service_settings_div) {
        let request_params = null;
        if (this.workflow_step.request_params) {
            request_params = this.get_from_state(this.workflow_step.request_params);
        } else {
            request_params = {};
        }
        request_params['url'] = this.workflow_step.url;
        const query_string = $.param(request_params);

        function _humanize_value(value) {
            let humanized_value = value;
            if (value == null) {
                humanized_value = '-';
            } else if (_.isBoolean(value)) {
                humanized_value = value ? 'Yes' : value == null ? '-' : 'No';
            }
            return humanized_value;
        }

        /**
         * Recursively go through the data and render it as a list.
         */
        function _render_object_data(data, fields) {
            const content = [];
            for (const field of fields) {
                const field_name = field.name;
                const value = data[field_name];
                if (Array.isArray(value)) {
                    const list_content = [];
                    for (const list_value of value) {
                        if (value == null) {
                            continue;
                        } else if (_.isObject(list_value)) {
                            list_content.push(_render_object_data(list_value, field.fields).join(''));
                        } else {
                            list_content.push(`
                                <li>${_humanize_value(list_value)}</li>
                            `);
                        }
                    }
                    content.push(`
                        <li>${_.startCase(field_name)}:</li>
                        <ul>
                            ${list_content.join('')}
                        </ul>
                    `);
                } else {
                    content.push(`
                        <li>${_.startCase(field_name)}: ${_humanize_value(value)}</li>
                    `);
                }
            }
            return content;
        }

        window.show_loader();
        $.ajax({
            url: `workflow/get_data?${query_string}`,
            success: (data) => {
                const content = _render_object_data(data, this.workflow_step.fields);
                service_settings_div.innerHTML += `
                    <ul>${content.join('')}</ul>
                    ${this.render_prev_next()}
                `;
            },
            error: this._error_handler(service_settings_div),
            complete: () => window.hide_loader(),
        });
    }


    handle_select_query_step(service_settings_div, multiple = false) {
        let request_params = null;
        if (this.workflow_step.request_params) {
            request_params = this.get_from_state(this.workflow_step.request_params);
        } else {
            request_params = {};
        }
        request_params['url'] = this.workflow_step.source.url;
        const query_string = $.param(request_params);

        show_loader();
        $.ajax({
            url: `workflow/get_data?${query_string}`,
            success: (data) => {
                service_settings_div.innerHTML += `
                    <form id="${this.get_form_id()}">
                        ${this.render_select_query(data, multiple)}
                        ${render_submit("Select")}
                    </form>
                `;
                $(`form#${this.get_form_id()}`).submit(event => this.submit_form(event, multiple));
            },
            error: this._error_handler(service_settings_div),
            complete: () => window.hide_loader(),
        });
    }

    /**
     * Render a choice step in a workflow.
     * 
     * Example:
     *  {
     *      "nr": 1,
     *      "name": "Area Contour",
     *      "description": "Do you want to get the area contours",
     *      "type": "choice",
     *      "options": [
     *          {
     *              "id": 2,
     *              "name": "Yes",
     *              "next_step": 3
     *          },
     *          {
     *              "id": 3,
     *              "name": "No",
     *              "next_step": 4
     *          }
     *      ]
     *  },
     * 
     */
    render_choice() {
        const buttons = [];
        for (const option of this.workflow_step['options']) {
            buttons.push(render_button(option.name, 'info', "", `modules.workflow.current_workflow.do_next(${option.next_step})`));
        }
        return render_btn_group(buttons);
    }

    /**
     * Render a multi select from a query. Perform the query and render the options.
     * 
     * @param {*} service_index 
     * @param {*} step 
     */
    render_select_query(data, multiple = false) {
        const source = this.workflow_step.source;
        const entities = data[source.choices_attr];
        const options = entities.map(entity => {
            const label_list = source.label_fields.map(label_field => entity[label_field]);
            const label = label_list.join(' - ');
            return `
                <option value="${entity[source.value_field]}">${label}</option>
            `;
        });

        const multiple_attr = multiple ? `multiple=${multiple}` : ''

        return `
            <select ${multiple_attr} name="${this.workflow_step.target_variable}">
                <option value="">--Please choose an option--</option>
                ${options.join('')}
            </select>
        `;
    }

    /**
     * Render the previous and next step buttons.
     */
    render_prev_next(render_next = true) {
        const buttons = [];
        if (this.workflow_step.previous_step >= 0) {
            buttons.push(render_button('Previous', 'light', "button", `modules.workflow.current_workflow.do_previous()`));
        }
        if (render_next && this.workflow_step.next_step >= 0) {
            buttons.push(render_button('Next', 'info', "button", `modules.workflow.current_workflow.do_next()`));
        }
        return render_btn_group(buttons);
    }

    /**
     * Render the close button.
     */
    render_close() {
        return render_button('Close', 'light', 'button', `sidebar.hide()`)
    }

    /**
     * Called after a form is submitted.
     * 
     * Parses the form data into the state.
     */
    submit_form(event, multiple = false) {
        event.preventDefault();
        const form = $(event.currentTarget);
        const form_data = form.serializeArray()

        if (multiple) {
            // Initialize all fields as a list.
            for (const field of form_data) {
                this.state[field.name] = [];
            }
        }
        for (const field of form_data) {
            if (multiple) {
                this.state[field.name].push(field.value);
            } else {
                this.state[field.name] = field.value;
            }
        }
        this.do_next();
    }

    /**
     * Go to the next step.
     */
    do_next(step_idx = null) {
        if (step_idx === null) {
            this.step_idx = this.workflow_step.next_step;
        } else {
            this.step_idx = step_idx
        }
        if (this.step_idx >= 0) {
            this.workflow_step = this.service.workflow[this.step_idx];
            window.show_service_settings(this.service_index, false);
        }
    }

    /**
     * Go to the previous step.
     */
    do_previous(step_idx = null) {
        if (step_idx === null) {
            this.step_idx = this.workflow_step.previous_step;
        } else {
            this.step_idx = step_idx
        }
        if (this.step_idx >= 0) {
            this.workflow_step = this.service.workflow[this.step_idx];
            window.show_service_settings(this.service_index, false);
        }
    }

    /**
     * Download a file.
     */
    handle_download_file_step(service_settings_div) {
        service_settings_div.innerHTML += render_button('Download', 'primary', "button", "", this.get_form_id())
        service_settings_div.innerHTML += this.render_prev_next();
        $(`button#${this.get_form_id()}`).click(() => {
            // Build the target request parameters by getting the values from the state.
            const request_params = this.get_from_state(this.workflow_step['request_params']);
            const params = {
                'remote_url': this.workflow_step.url,
                'request_params': request_params,
            };
            // Perform the request to the Webeditor backend, who will forward it to the service.
            window.show_loader();
            $.ajax({
                type: "POST",
                url: 'workflow/download_file',
                data: JSON.stringify(params),
                contentType: "application/json",
                success: (data) => {
                    download_binary_file_from_base64_str(data['base64file'], data['filename']);
                    if (this.workflow_step.next_step == null) {
                        service_settings_div.innerHTML = '';
                    }
                },
                error: this._error_handler(service_settings_div),
                complete: () => window.hide_loader(),
            });
        });
    }

    /**
     * Upload a file to a remote API.
     */
    handle_upload_file_step(service_settings_div) {
        const file_input_id = `file-${this.get_form_id()}`;
        const elements = [];
        elements.push(`
            <input type="file" id="${file_input_id}"/>
        `);
        service_settings_div.innerHTML += render_form(this.get_form_id(), elements, "Upload");
        service_settings_div.innerHTML += this.render_prev_next();
        $(`form#${this.get_form_id()}`).submit((event) => {
            event.preventDefault();
            // Get the file input element, and read the file with the FileReader API.
            const file_input = document.getElementById(file_input_id);
            const file_reader = new FileReader()
            const file_to_upload = file_input.files[0];
            if (file_to_upload) {
                const file_name = file_to_upload.name;

                // This function will do the actual uploading. It is triggered when
                // calling readAsDataURL on the file_reader.
                const upload_file = () => {
                    // Build the target request parameters by getting the values from the state.
                    const request_params = this.get_from_state(this.workflow_step['request_params']);
                    // Add file upload specific fields.
                    request_params['base64_file'] = file_reader.result;
                    request_params['file_name'] = file_name;
                    const params = {
                        'remote_url': this.workflow_step.url,
                        'request_params': request_params,
                    }
                    // Perform the request to the Webeditor backend, who will forward it to the service.
                    window.show_loader();
                    $.ajax({
                        type: "POST",
                        url: 'workflow/post_data',
                        data: JSON.stringify(params),
                        contentType: "application/json",
                        success: () => {
                            alert('Upload successful!');
                            if (this.workflow_step.next_step == null) {
                                service_settings_div.innerHTML = '';
                            }
                        },
                        error: this._error_handler(service_settings_div),
                        complete: () => window.hide_loader(),
                    });
                }

                file_reader.onload = upload_file
                // Trigger the onload.
                file_reader.readAsDataURL(file_to_upload);
            } else {
                alert("Please select a valid file to upload.")
            }
        });
    }

    /**
     * Call a JS function.
     */
    handle_call_js_function_step(service_settings_div) {
        const dom_elements = this.workflow_step['dom_elements'];
        for (const [id, state_param_name] of Object.entries(dom_elements)) {
            const param = this.state[state_param_name];
            service_settings_div.innerHTML += `<input id=${id} type=hidden value=${param} />`;
        }
        service_settings_div.innerHTML += render_button(this.workflow_step.name, 'primary', "button", "", this.get_form_id())
        setTimeout(() => {
            $(`button#${this.get_form_id()}`).click(() => {
                const js_function_name = this.workflow_step['js_function'];
                window[js_function_name](...this.workflow_step.parameters);
            });
        });
    }

    _error_handler(service_settings_div) {
        return (error) => {
            let text = null;
            if (error.status == 401) {
                text = "You are logged out. Please log out and back in again.";
                window.auth_status();
            }
            service_settings_div.innerHTML += window.service_render_error(this.service_index, text);
        }
    }

    /**
     * Get values from the state.
     * 
     * @param {*} to_obtain_params An object mapping a key (what it should be in the
     * result) to a value (the name in the state).
     */
    get_from_state(to_obtain_params) {
        const params = {};
        for (const [key, value] of Object.entries(to_obtain_params)) {
            params[key] = this.state[value];
        }
        return params;
    }

    get_form_id() {
        return `${this.service['id']}_${this.step_idx}`;
    }

    get_next_step_idx() {
        return this.workflow_step.next_step;
    }

}
