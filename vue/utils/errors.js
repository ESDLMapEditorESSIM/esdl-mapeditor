
/**
 * A generic error handler, for in case an API request goes wrong. Log the error and
 * tell something to the user.
 * 
 * @param {*} e 
 */
export function genericErrorHandler(e) {
    alert("An error has occurred: " + e);
    console.error(e);
}