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
// set  dont_reschedule to true to disable rescheduling this function.
let auth_status = function(dont_reschedule) {
    $.get('/auth_status')
        .done(function (session) {
            console.log('Session status:', session);
            let uri = session.redirect_uri;
            if (!dont_reschedule) {
                setTimeout(auth_status, 60000);
            } else {
                uri = window.location; // use different uri when manually invoked, as the /editor should be loaded first when restarting the mapeditor code
            }
            if (!session.valid) {
                const answer = confirm("Session has expired, re-authentication is necessary.\nPress Ok to go to the login page.");
                if (answer) {
                    console.log('Redirecting to', uri)
                    window.location = uri;
                }
            }
        })
        .fail(function (data) {
            console.log('Failed to check status, reauthentication necessary', data)
            if (!dont_reschedule) setTimeout(auth_status, 60000);
        });
};
auth_status();
