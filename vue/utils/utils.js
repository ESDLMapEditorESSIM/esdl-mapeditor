/**
 * Get an attribute of an object by name. Supports dot-notation (so execution.id
 * will do obj[execution][id] effectively.)
 *
 * @param {*} obj
 * @param {*} name
 */
export function getattrd(obj, name) {
    const splitted_name = name.split(".")
    // Starting point == obj
    let value = obj
    try {
        // in case of name = session.* , ignore resolving, but just pass the name further
        // session.* variables are resolved in the backend (see workflow.py)
        // eg. session.email 
        if (splitted_name[0] === 'session') {
            return name;
        }
        for (const n of splitted_name) {
            value = value[n];
        }
        return value
    } catch {
        // console.error(`Attribute not found on object: ${name}`)
        return null;
    }
}

/**
 * Set an attribute of an object by name. Supports dot-notation (so execution.id
 * will set obj[execution][id] to the desired value effectively).
 * @param {*} obj
 * @param {*} name
 * @param {*} value
 */
export function setattrd(obj, name, value) {
    const splitted_name = name.split(".")
    let currentObj = obj

    try {
        for (let i = 0; i < splitted_name.length - 1; i++) {
            const n = splitted_name[i];
            // Add new empty object if object for nested key does not exist yet
            if (!currentObj[n] || typeof currentObj[n] !== "object") {
                currentObj[n] = {}
            }
            currentObj = currentObj[n];
        }
        
        // Merge new value with current value and/or existing values for this key
        const lastKey = splitted_name[splitted_name.length - 1];
        currentObj[lastKey] = {...currentObj[lastKey] ?? {}, ...value};
    } catch {
        console.log("error in setattrd");
    }
}

export function isDebug() {
    return window.DEBUG;
}

export const unique = (a) => [...new Set(a)];
export const uniqueBy = (x, f) => Object.values(x.reduce((a, b) => ((a[f(b)] = b), a), {}));
export const intersection = (a, b) => a.filter((v) => b.includes(v));
export const diff = (a, b) => a.filter((v) => !b.includes(v));
export const symDiff = (a, b) => diff(a, b).concat(diff(b, a));
export const union = (a, b) => diff(a, b).concat(b);

export const camelCase = (str) => {
    return window.camelCaseToWords(str);
};
