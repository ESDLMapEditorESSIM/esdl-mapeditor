export function carrierToken(id) {
    return encodeURIComponent(id);
}

function withCarrierClasses(className, classes) {
    return (className || "").split(/\s+/)
        .filter(name => name && !name.startsWith("esdl-carrier-"))
        .concat(classes).join(" ");
}

/** Set carrier classes on Leaflet render options and existing asset elements. */
export function registerAssetCarriers(esId, object) {
    if (!object.ports) {
        return;
    }
    object.updateCarrierClasses = () => {
        const classes = [`esdl-carrier-system-${carrierToken(esId)}`];
        for (const port of object.ports) {
            if (port.carrier) {
                classes.push(`esdl-carrier-${carrierToken(port.carrier)}`);
            }
        }
        object.carrierClasses = classes.join(" ");
        let options = object.options;
        if (options.icon) {
            options = options.icon.options;
        }
        options.className = withCarrierClasses(options.className, classes);
        for (const element of [object.getElement(), object._textNode]) {
            if (!element) {
                continue;
            }
            for (const className of Array.from(element.classList)) {
                if (className.startsWith("esdl-carrier-")) {
                    element.classList.remove(className);
                }
            }
            element.classList.add(...classes);
        }
        if (object._textOptions) {
            object._textOptions.attributes = {...object._textOptions.attributes, class: object.carrierClasses};
        }
    };
    object.updateCarrierClasses();
}
