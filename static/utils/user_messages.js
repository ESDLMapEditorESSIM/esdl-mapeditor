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

// Edwin: This generates error, TODO: fix
// document.body.addEventListener('animationend', removeElement);
// document.body.addEventListener('webkitAnimationEnd', removeElement);

function removeElement(event) {
    if (event.animationName === 'disapear') {
        event.target.parentNode.removeChild(event.target);
        checkHeightContainer();
        checkIfLogIsEmpty();
    }
}

function deleteLogItems() {
    for (var i = 0, len = document.getElementById('messages').children.length; i < len; i++) {
        if (document.getElementById('messages').children[i]) {
            document.getElementById('messages').children[i].classList.add('removed');
        }
    }
}

function checkIfLogIsEmpty() {
    messageList = document.getElementById('messages');
    messageContainer = document.getElementById('messagesContainer')
    if (messageList.children.length > 0) {
        messageContainer.classList.remove('messages-hidden');
    } else {
        messageContainer.classList.add('remove-messages');
    }
}

function AddErrorMessage(MessageText, MessageType, MessageTimeOut) {
    if (MessageText.length === 0)
        return

    messageContainer = document.getElementById('messagesContainer');
    messageContainer.classList.remove('messages-hidden');
    messageContainer.classList.remove('remove-messages');
    messageList = document.getElementById('messages');

    var message = document.createElement('div');
    message.classList.add('message');

    var bl = document.createElement('span');
    bl.classList.add('bl');
    var status = document.createElement('span');
    status.classList.add('logStatus');
    var logText = document.createElement('span');
    logText.classList.add('logText');
    var deleteItem = document.createElement('span');
    deleteItem.classList.add('delete');
    deleteItem.innerHTML = 'x';
    deleteItem.id = messageList.children.length++;
    deleteItem.onclick = function () {
        // this.parentElement.remove();
        this.parentElement.classList.add('removed');

        if (messageList.children.length === 0) {
            messageContainer.classList.add('messages-hidden');
            checkHeightContainer();
        }
    }

    if (typeof (MessageTimeOut) === 'number') {
        selectedTime = MessageTimeOut;
    } else if (typeof (MeasgeTimeOut) === 'undefined') {
        selectedTime = 60000; // show for 1 minute
    } else {
        selectedTime = 15000; // default 15 seconds
    }

    if (selectedTime) {
        setTimeout(function () {
            // deleteItem.parentElement.remove();
            deleteItem.parentElement.classList.add('removed');
            if (messageList.children.length === 0) {
                messageContainer.classList.add('remove-messages');
            }
        }, selectedTime);
    }

    if (MessageText) {
        logText.innerHTML = MessageText;
    }

    var found = false;
    if (MessageType) {
        switch (MessageType) {
            case 'succes':
                found = true;
                break;
            case 'warning':
                found = true;
                break;
            case 'error':
                found = true;
                break;
            default:
                found = false;
                break;
        }
        if (found) {
            message.classList.add(MessageType);
            status.innerHTML = MessageType + ': ';
        }
    }
    message.appendChild(bl); // add borderLeft to messageItem
    message.appendChild(status); // add status text to messageItem
    message.appendChild(logText); // add Logtext span to messageItem
    message.appendChild(deleteItem); // add delete button to messageItem

    // adding item to container
    if (messageList.children.length > 0) { // check if have items
        messageList.insertBefore(message, messageList.firstChild);
    } else {
        messageList.appendChild(message);
    }

    checkHeightContainer();
}

function checkHeightContainer() {
    if (document.getElementById('messagesContainer').getBoundingClientRect().bottom > document.body.getBoundingClientRect().bottom) {
        document.getElementById('messagesContainer').style.bottom = '0px';
        document.getElementById('messagesContainer').style.overflowY = 'auto';
    } else {
        document.getElementById('messagesContainer').style.bottom = 'auto';
        document.getElementById('messagesContainer').style.overflowY = 'auto';
    }
}
