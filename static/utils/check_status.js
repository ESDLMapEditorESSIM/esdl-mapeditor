/**
 *  This work is based on original code developed and copyrighted by TNO 2020.
 *  Subsequent contributions are licensed to you by the developers of such code and are
 *  made available to the Project under one or several contributor license agreements.
 *
 *  This work is licensed to you under the Apache License, Version 2.0.
 *  You may obtain a copy of the license at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Contributors:
 *      TNO         - Initial implementation
 *  Manager:
 *      TNO
 */

// Keeps polling the auth_status endpoint to check if the authentication is still valid
// every minute
let auth_status = function() {
    $.get('/auth_status')
        .done(function (session) {
            console.log(session);
            setTimeout(auth_status, 60000);
            if (!session.valid) {
                const answer = confirm("Session has expired, reauthentication is necessary.\nPress Ok to go to the login page.");
                if (answer) {
                    window.location = session.redirect_uri
                }
            }
        })
        .fail(function (data) {
            console.log('Failed to check status, reauthentication necessary', data)
            setTimeout(auth_status, 60000);
        });
};
auth_status();
