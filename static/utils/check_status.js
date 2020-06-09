// Keeps polling the auth_status endpoint to check if the authentication is still valid
// every minute
let auth_status = function() {
    $.get('/auth_status').done(function (data) {
        console.log(data);
        setTimeout(auth_status, 60000);
    });
};
auth_status();