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