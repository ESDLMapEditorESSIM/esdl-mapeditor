
function build_asset_menu(asset_menu_id, add_nea, cap_pot_list) {
    $('#'+asset_menu_id).empty();

    if (add_nea) {
        let optgroup = $('<optgroup>');
        optgroup.attr('label', 'Non EnergyAssets');
        optgroup.style = 'font-face: bold; font-size: 10px';
        let non_energyassets = ['Area', 'Building', 'AggregatedBuilding'];
        for (let nea in non_energyassets) {
            let option = $("<option></option>");
            option.val(non_energyassets[nea]);
            option.text(non_energyassets[nea]);
            optgroup.append(option);
            // TODO EWOUD: I've generated icons for both buildings. Why have you added this code?
            //  genIconDataURL = drawTextImage(getAbbrevation(non_energyassets[nea]));
            //          window[non_energyassets[nea] +'Marker'] = L.Icon.extend({options: {shadowUrl: null, iconAnchor: new L.Point(12, 12),
            //              iconSize: new L.Point(30, 30), iconUrl: genIconDataURL}});
        }
        $('#'+asset_menu_id).append(optgroup);
    }

    cap_list = cap_pot_list["capabilities"];
    for (let key in cap_list) {
        //console.log(key + ' --> ' + cap_list[key])
        let optgroup = $('<optgroup>');
        optgroup.attr('label', key);
        optgroup.style = 'font-face: bold; font-size: 10px';
        for (let i in cap_list[key]) {
             let option = $("<option></option>");
             option.val(cap_list[key][i]);
             option.text(cap_list[key][i]);
             optgroup.append(option);
             // generate icons for markers that do not have an static image png
             if (!assets_for_icons.includes(cap_list[key][i])){
                //console.log("Generating marker for" + cap_list[key][i] + ", abbr = " + getAbbrevation(cap_list[key][i]));
                genIconDataURL = drawTextImage(getAbbrevation(cap_list[key][i]));
                window[cap_list[key][i] +'Marker'] = L.Icon.extend({options: {shadowUrl: null, iconAnchor: new L.Point(12, 12),
                    iconSize: new L.Point(30, 30), iconUrl: genIconDataURL}});
             }
        }
        $('#'+asset_menu_id).append(optgroup);
    }

    pot_list = cap_pot_list["potentials"];
    let optgroup = $('<optgroup>');
    optgroup.attr('label', 'Potentials');
    optgroup.style = 'font-face: bold; font-size: 10px';
    for (let i in pot_list) {
         let option = $("<option></option>");
         option.val(pot_list[i]);
         option.text(pot_list[i]);
         optgroup.append(option);
         // generate icons for markers that do not have an static image png
         if (!assets_for_icons.includes(pot_list[i])){
            //console.log("Generating marker for" + cap_list[key][i] + ", abbr = " + getAbbrevation(cap_list[key][i]));
            genIconDataURL = drawTextImage(getAbbrevation(pot_list[i]));
            window[pot_list[i] +'Marker'] = L.Icon.extend({options: {shadowUrl: null, iconAnchor: new L.Point(12, 12),
                iconSize: new L.Point(30, 30), iconUrl: genIconDataURL}});
         }
    }
    $('#'+asset_menu_id).append(optgroup);

    $('#'+asset_menu_id).attr("size", "15");
    //$('#'+asset_menu_id+'-menu').css({'max-height': '600px' });
    $('#'+asset_menu_id).selectmenu("refresh");

    //$( "#asset_menu" ).addClass( "overflow" );
}

