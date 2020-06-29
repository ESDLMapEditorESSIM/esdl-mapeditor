// Keeps polling the auth_status endpoint to check if the authentication is still valid
// every minute
let auth_status = function() {
    $.get('/auth_status')
        .done(function (session) {
            console.log(session);
            setTimeout(auth_status, 60000);
            if (!session.valid) {
                answer = confirm("Session has expired, reauthentication is necessary.\nPress Ok to go to the login page.");
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