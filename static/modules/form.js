import { render_button } from "./buttons.js";

const FormFieldTypes = Object.freeze({
    TEXT: 'text',
});

export function render_form(id, form_elements, submit_text = 'Submit') {
    let form_content = "";
    for (const element of form_elements) {
        form_content += `
            <div class="form-group">
                ${element}
            </div>
        `;
    }
    const content = `
        <form id="${id}" action="#">
            ${form_content}
            ${render_submit(submit_text)}
        </form>
    `;
    return content;
}

export function render_form_field(type, name, label) {
    if (type === FormFieldTypes.TEXT) {
        return `
            <input type="text" required="true" name="${name}" placeholder="${label}">
        `;
    }

}

export function render_submit(text = 'Submit') {
    return `
        <div class="form-group">
            <input class="btn btn-primary" type="submit" value="${text}"/>
        </div>
    `;
}
