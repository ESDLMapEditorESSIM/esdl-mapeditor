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
        console.error("Attribute not found on object")
        return null;
    }
}
