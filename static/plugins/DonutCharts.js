function createDonutCharts() {
    $("<style type='text/css' id='dynamic' />").appendTo("head");
    $("div[chart-type*=donut]").each(function () {
        console.log('YEAH');
        var d = $(this);
        var id = $(this).attr('id');
        var max = $(this).data('chart-max');
        if ($(this).data('chart-text')) {
            var text = $(this).data('chart-text');
        } else {
            var text = "";
        }
        if ($(this).data('chart-caption')) {
            var caption = $(this).data('chart-caption');
        } else {
            var caption = "";
        }
        if ($(this).data('chart-initial-rotate')) {
            var rotate = $(this).data('chart-initial-rotate');
        } else {
            var rotate = 0;
        }
        var segments = $(this).data('chart-segments');

        for (var i = 0; i < Object.keys(segments).length; i++) {
            var s = segments[i];
            var start = ((s[0] / max) * 360) + rotate;
            var deg = ((s[1] / max) * 360);
            if (s[1] >= (max / 2)) {
                d.append('<div class="large donut-bite" data-segment-index="' + i + '"> ');
            } else {
                d.append('<div class="donut-bite" data-segment-index="' + i + '"> ');
            }
            var style = $("#dynamic").text() + "#" + id + " .donut-bite[data-segment-index=\"" + i + "\"]{-moz-transform:rotate(" + start + "deg);-ms-transform:rotate(" + start + "deg);-webkit-transform:rotate(" + start + "deg);-o-transform:rotate(" + start + "deg);transform:rotate(" + start + "deg);}#" + id + " .donut-bite[data-segment-index=\"" + i + "\"]:BEFORE{-moz-transform:rotate(" + deg + "deg);-ms-transform:rotate(" + deg + "deg);-webkit-transform:rotate(" + deg + "deg);-o-transform:rotate(" + deg + "deg);transform:rotate(" + deg + "deg); background-color: " + s[2] + ";}#" + id + " .donut-bite[data-segment-index=\"" + i + "\"]:BEFORE{ background-color: " + s[2] + ";}#" + id + " .donut-bite[data-segment-index=\"" + i + "\"].large:AFTER{ background-color: " + s[2] + ";}";
            $("#dynamic").text(style);
        }

        d.children().first().before("<div class='donut-hole'><span class='donut-filling'>" + text + "</span></div>");
        d.append("<div class='donut-caption-wrapper'><span class='donut-caption'>" + caption + "</span></div>");
    });
}

$(document).ready(function() {
    // $("<style type='text/css' id='dynamic' />").appendTo("head");
    createDonutCharts();
});

function makeDonutCharts(chart) {
    var d = $(chart);
    var id = $(chart).attr('id');
    var max = $(chart).data('chart-max');
    if ($(chart).data('chart-text')) {
        var text = $(chart).data('chart-text');
    } else {
        var text = "";
    }
    if ($(chart).data('chart-caption')) {
        var caption = $(chart).data('chart-caption');
    } else {
        var caption = "";
    }
    if ($(chart).data('chart-initial-rotate')) {
        var rotate = $(chart).data('chart-initial-rotate');
    } else {
        var rotate = 0;
    }
    var segments = $(chart).data('chart-segments');

    for (var i = 0; i < Object.keys(segments).length; i++) {
        var s = segments[i];
        var start = ((s[0] / max) * 360) + rotate;
        var deg = ((s[1] / max) * 360);
        if (s[1] >= (max / 2)) {
            d.append('<div class="large donut-bite" data-segment-index="' + i + '"> ');
        } else {
            d.append('<div class="donut-bite" data-segment-index="' + i + '"> ');
        }
        var style = $("#dynamic").text() + "#" + id + " .donut-bite[data-segment-index=\"" + i + "\"]{-moz-transform:rotate(" + start + "deg);-ms-transform:rotate(" + start + "deg);-webkit-transform:rotate(" + start + "deg);-o-transform:rotate(" + start + "deg);transform:rotate(" + start + "deg);}#" + id + " .donut-bite[data-segment-index=\"" + i + "\"]:BEFORE{-moz-transform:rotate(" + deg + "deg);-ms-transform:rotate(" + deg + "deg);-webkit-transform:rotate(" + deg + "deg);-o-transform:rotate(" + deg + "deg);transform:rotate(" + deg + "deg); background-color: " + s[2] + ";}#" + id + " .donut-bite[data-segment-index=\"" + i + "\"]:BEFORE{ background-color: " + s[2] + ";}#" + id + " .donut-bite[data-segment-index=\"" + i + "\"].large:AFTER{ background-color: " + s[2] + ";}";
        $("#dynamic").text(style);
    }

    d.children().first().before("<div class='donut-hole'><span class='donut-filling'>" + text + "</span></div>");
    d.append("<div class='donut-caption-wrapper'><span class='donut-caption'>" + caption + "</span></div>");
}