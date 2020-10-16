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

// ------------------------------------------------------------------------------------------------------------
//
// ------------------------------------------------------------------------------------------------------------
function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

var camelCaseToWords = function(str){
    // checkif this works
    if (str.match(/^[^a-z]+$/g)) {
        return str;
    } // if no lowercase characters found, just use the word as given, e.g. COP
    return str.match(/^[a-z]+|[A-Z][a-z]*/g).map(function(x){
        return x[0].toUpperCase() + x.substr(1).toLowerCase();
    }).join(' ');
}

function getAbbrevation(assetType) {
    return assetType.match(/[A-Z]/g).join('');
}

function drawTextImage(text) {
    jqcanvas = $('<canvas>', {id:'cvs', style: 'display: none;'}).attr({'width':128,'height':128});
    //$('.doc').prepend(jqcanvas)
    //canvas = $('#cvs').get(0);
    canvas = jqcanvas.get(0);
    ctx = canvas.getContext('2d');
    ctx.fillStyle = '#000000';
    ctx.textAlign = "center";
    // auto size text to fit in box
    let fontface = 'sans-serif';
    let fontsize = 200;
    do {
        ctx.font=fontsize+"px "+fontface;
        fontsize--;
    } while(ctx.measureText(text).width > canvas.width)
    ctx.fillText(text, 64, Math.max(Math.min(fontsize, 128), 80));

    // convert to data url and image
    let url = canvas.toDataURL();
    jqcanvas = null;
    return url;
    //let img = new Image();
    //img.src = url;
    //$('#imgs').append(img)

    //return img;
}

// For todays date;
Date.prototype.today = function () {
    return this.getFullYear() + "-" +(((this.getMonth()+1) < 10)?"0":"") + (this.getMonth()+1) +
        "-" + ((this.getDate() < 10)?"0":"") + this.getDate();
}

// For the time now
Date.prototype.timeNow = function () {
     return ((this.getHours() < 10)?"0":"") + this.getHours() +":"+ ((this.getMinutes() < 10)?"0":"") +
        this.getMinutes() +":"+ ((this.getSeconds() < 10)?"0":"") + this.getSeconds();
}