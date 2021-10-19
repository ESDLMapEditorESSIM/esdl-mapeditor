/**
 * Checks if we are still logged in and if possible refreshes the auth token. If the user is logged out, shows a confirm dialog confirming the logout.
 *
 * This is a similar implementation to check_status.js in the legacy codebase, but built using async / await so it can be awaited.
 *
 * @returns {Promise<boolean>}
 */
export async function checkAndRefreshAuthStatus() {
    const response = await fetch('/auth_status')
    if (response.ok) {
        const session = await response.json();
        if (!session.valid) {
            const answer = confirm("Session has expired, reauthentication is necessary.\nPress Ok to go to the login page.");
            if (answer) {
                window.location = session.redirect_uri
            }
            return false;
        }
        return true;
    }
    return false;
}
