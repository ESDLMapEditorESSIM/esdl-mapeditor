
export function render_button(text, clazz, type = "", onclick = "", btn_id = "") {
    return `
        <button id="${btn_id}" class="btn btn-${clazz}" type="${type}" onclick="${onclick}">
            ${text}
        </button>
    `;
}

export function render_btn_group(buttons) {
    if (buttons.length >= 0) {
        return `
            <div class="btn-group btn-block" style="margin-top: 10px">
                ${buttons.join('')}
            </div>
        `;
    } else {
        return '';
    }
}
