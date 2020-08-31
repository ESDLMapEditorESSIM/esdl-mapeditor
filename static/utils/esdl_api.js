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


function send_accept_esdl() {
    socket.emit('command', {'cmd': 'accept_received_esdl'});
}

function received_esdl_window(message) {
    sender = message["sender"];
    descr = message["descr"];

    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>ESDL received:</h1>';

    sidebar_ctr.innerHTML += '<p>An application ('+sender+') is trying to send an ESDL file to you.</p>';

    if (descr !== "") {
        sidebar_ctr.innerHTML += '<p>The description is: '+descr+'</p>';
    }

    sidebar_ctr.innerHTML += '<p>Would you like to accept this?</p>';
    sidebar_ctr.innerHTML += '<button id="accept_esdl" onclick="sidebar.hide();send_accept_esdl();">Yes</button>';
    sidebar_ctr.innerHTML += '<button id="deny_esdl" onclick="sidebar.hide();">No</button>';

    sidebar.show();
}