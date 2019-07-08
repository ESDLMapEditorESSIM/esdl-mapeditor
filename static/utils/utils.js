
var camelCaseToWords = function(str){
    return str.match(/^[a-z]+|[A-Z][a-z]*/g).map(function(x){
        return x[0].toUpperCase() + x.substr(1).toLowerCase();
    }).join(' ');
};