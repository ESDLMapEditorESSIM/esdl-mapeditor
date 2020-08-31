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

// -------------------------------------------------------------------------------------------------------------------
//  Sizes of edit boxes in the tables
// -------------------------------------------------------------------------------------------------------------------
let edit_size_small_number = '6';
let edit_size_large_number = '14';
let edit_size_string = '40';

let edit_size = {
    'name': edit_size_string,
    'power': edit_size_large_number,
    'capacity': edit_size_large_number,
    'efficiency': edit_size_small_number,
    'COP': edit_size_small_number,
    'heatEfficiency': edit_size_small_number,
    'electricalEfficiency': edit_size_small_number
}

// -------------------------------------------------------------------------------------------------------------------
//  Some helper functions
// -------------------------------------------------------------------------------------------------------------------
function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function isEmpty(obj) {
    return Object.keys(obj).length === 0;
}

function is_upper_case(ch)
{
    return (ch >= 'A') && (ch <= 'Z');
}

function capitalize(s) {
    if (typeof s !== 'string') return '';
    return s.charAt(0).toUpperCase() + s.slice(1);
}

function break_capital(s) {
    let r = '';
    for (let i=0; i<s.length; i++) {
        if (i>0 && is_upper_case(s.charAt(i))) {
            if (i<s.length-1 && !is_upper_case(s.charAt(i+1))) {
                r += '<br>';
            }
        }
        r += s.charAt(i);
    }
    return r;
}

// -------------------------------------------------------------------------------------------------------------------
//  Marginal Costs
// -------------------------------------------------------------------------------------------------------------------
function set_marginal_costs_value(asset_id, mc) {
    socket.emit('command', {cmd: 'set_marg_costs', asset_id: asset_id, marg_costs: mc});
}

function change_mc(obj) {
    let asset_id = $(obj).attr('assetid');
    let mc = obj.value;
    set_marginal_costs_value(asset_id, mc);
}

function generate_table_row_info_for_mc(asset_id, asset_mc) {
    let idgen = uuidv4();
    if (asset_mc == null) { asset_mc = ''; } else { asset_mc = asset_mc.toString(); }
    return '<td><input type="text" size="'+edit_size_small_number+'" id="marg_costs_'+idgen.toString()+'" assetid="' + asset_id +
        '" value="' + asset_mc + '" onchange="change_mc(this);"></td>';
}
// -------------------------------------------------------------------------------------------------------------------
//  Control Strategies
// -------------------------------------------------------------------------------------------------------------------
function change_cs(obj, asset_id) {
    opt_value = obj.options[obj.selectedIndex].value;
    opt_value_parts = opt_value.split('_');

    if (opt_value_parts[0] == 'DbD' || opt_value_parts[0] == 'DbS') {
        let cs = opt_value_parts[0];
        let port_id = opt_value_parts[2];

        if (cs == 'DbD') {
            set_driven_by_demand(asset_id, port_id);
        } else if (cs == 'DbS') {
            set_driven_by_supply(asset_id, port_id);
        }
    } else if (opt_value_parts[0] == 'removecsfor') {
        socket.emit('command', {cmd: 'remove_control_strategy', asset_id: asset_id});
    }
}

function generate_table_row_info_for_cs(cap_type, asset_id, asset_ct, asset_cs) {
    // console.log(asset_cs.type);

    let select = '<td><select id="selcsfor_'+asset_id+'" onchange="change_cs(this, \''+asset_id+'\');">';

    let no_strategy_selected = isEmpty(asset_cs);
    if (no_strategy_selected) {
        select += '<option value="nocsfor_'+asset_id+'" selected>No strategy</option>';
    } else {
        select += '<option value="removecsfor_'+asset_id+'">Remove strategy</option>';
    }

    if (cap_type == 'storage') {
        let selected = '';
        if (!no_strategy_selected) {
            selected = ' selected';
        }
        select += '<option value="addssfor_'+asset_id+'"'+selected+'>Add storage strategy</option>'
    } else if (cap_type == 'conversion') {
        for (let p=0; p<asset_ct.length; p++) {
            port = asset_ct[p];
            pid = port['pid'];
            pname = port['pname'];
            ptype = port['ptype'];

            let selected = '';
            let cs_title = '';
            if (ptype == 'OutPort') {
                if (!no_strategy_selected) {
                    if (asset_cs['out_port_id'] == pid) {
                        selected = ' selected';
                    }
                }
                cs_title = 'DrivenByDemand for OutPort: '+pname;
                cs_value = 'DbD_'+asset_id+'_'+pid;
            } else if (ptype == 'InPort') {
                if (!no_strategy_selected) {
                    if (asset_cs['in_port_id'] == pid) {
                        selected = ' selected';
                    }
                }
                cs_title = 'DrivenBySupply for InPort: '+pname;
                cs_value = 'DbS_'+asset_id+'_'+pid;
            }

            select += '<option value="'+cs_value+'"'+selected+'>'+cs_title+'</option>'
        }
        console.log(asset_cs);
        if (asset_cs['type'] == 'DrivenByProfile') {
            select += '<option value="DrivenByProfile" selected>DrivenByProfile</option>';
        }
    }

    select += '</select></td>';
    return select;
}

// -------------------------------------------------------------------------------------------------------------------
//  Profiles
// -------------------------------------------------------------------------------------------------------------------
function change_prof(obj, asset_id) {
    let value = obj.value;

    if (value.substring(0,10) == 'setproffor') {
        let parts = value.split('_');
        let port_id = parts[2];
        setPortProfile(null, asset_id, port_id);
    }
}

function generate_table_row_info_for_profile(asset_id, asset_prof) {
    let select = '<td><select id="selproffor_'+asset_id+'" onchange="change_prof(this, \''+asset_id+'\');">';

    num_profs = 0;
    for (let p=0; p<asset_prof.length; p++) {
        prof = asset_prof[p];
        if (!isEmpty(prof['profiles'])) { num_profs += 1; }
    }

    if (num_profs == 0) {
        select += '<option value="noproffor_'+asset_id+'" selected>No profiles</option>';

        for (let p=0; p<asset_prof.length; p++) {
            prof = asset_prof[p];
            port_id = prof['port_id']
            port_name = prof['port_name']
            select += '<option value="setproffor_'+asset_id+'_'+port_id+'">'+
                'Set profile for '+port_name+'</option>';
        }
    } else if (num_profs == 1) {
        for (let p=0; p<asset_prof.length; p++) {
            prof = asset_prof[p];
            if (!isEmpty(prof['profiles'])) {
                // console.log(prof['profiles']);
                select += '<option value="proffor_'+asset_id+'_'+prof['port_id']+'" selected>'+prof['port_name']+
                    ': '+ prof['profiles'][0]['uiname'] + ': ' + prof['profiles'][0]['multiplier'] + ' (' +
                    prof['profiles'][0]['type'] + ')</option>';
            }
        }
    } else {
        select += '<option value="multproffor_'+asset_id+'" selected>Multiple profiles</option>';
    }

    select += '</select></td>';
    return select;
}

// -------------------------------------------------------------------------------------------------------------------
//  Generate a row for a table
// -------------------------------------------------------------------------------------------------------------------
function generate_table_row_for_asset(cap_type, asset, field_list) {
    let asset_type = asset['type'];
    let asset_attrs = asset['attrs'];
    let asset_id = asset['id'];
    let asset_cs = asset['control_strategy'];
    let asset_mc = asset['marginal_costs'];
    let asset_ct = asset['connected_to_info'];
    let asset_prof = asset['profile_info'];

//    let mc_available = false;
//    if (cap_type != 'storage' && cap_type != 'transport') {
//        mc_available = true;
//    }
//
//    let cs_available = false;

    let params_edit = {};

    for (i=0; i<asset_attrs.length; i++) {
        idgen = uuidv4();
        if (field_list.includes(asset_attrs[i]['name'])) {
            if (asset_attrs[i]['value'] == null) {
                value = '';
            } else {
                value = asset_attrs[i]['value'];
            }
            let title = 'data-html="true" title="';
            if (asset_attrs[i]['doc'] != null) {
                title += asset_attrs[i]['doc'];
            }
            if (asset_attrs[i]['type'] != null) {
                title += '<br/>Data type:  ';
                title += asset_attrs[i]['type'];
                title += ' ';
            }
            if (asset_attrs[i]['default'] != null) {
                title += '<br/>Default value: ';
                title += asset_attrs[i]['default'];
            }
            title += '"';
            let edate = "";
            if (asset_attrs[i]['type'] == 'EDate') {
                edate = ' edate="true" ';
            }

            if (asset_attrs[i]['type'] == 'EEnum' || asset_attrs[i]['type'] == 'EBoolean') {
                options = asset_attrs[i]['options'];
                param_edit = '<td><select width="60" style="width:145px" id="'+ asset_attrs[i]['name']+idgen.toString()+'" assetid="' + asset_id + '" name="' +
                    asset_attrs[i]['name'] + '" onchange="change_param(this);">';
                    for (let o=0; o<options.length; o++) {
                        selected = "";
                        if (options[o] == value) selected=" selected";
                        caption = options[o].charAt(0).toUpperCase() + options[o].slice(1).toLowerCase();
                        caption = caption.replace(/_/g, ' '); // replace _ with space to render nicely
                        param_edit += '<option value="' + options[o] + '" '+selected+'>' + caption + '</option>';
                    }
                param_edit += '</select></td>';
            } else {
                param_edit_size = edit_size[asset_attrs[i]['name']];
                param_edit = '<td><input type="text" size="'+param_edit_size+'" id="'+ asset_attrs[i]['name']+idgen.toString()+'" assetid="' + asset_id + '" name="' +
                    asset_attrs[i]['name'] + '" value="' + value +'" onchange="change_param(this);" ' + edate + '></td>';
            }
            params_edit[asset_attrs[i]['name']] = param_edit;
        }
    }

    let tr = '<tr>';
    tr += '<td>' + asset_type + '</td>';       // Asset type
    for (let i=0; i<field_list.length; i++) {
        let field = field_list[i];
        if (field in params_edit) {
            tr += params_edit[field];
        } else {
            tr += '<td>&nbsp;</td>';
        }
    }

    // Control Strategies
    if (cap_type == 'conversion' || cap_type == 'storage') {
        tr += generate_table_row_info_for_cs(cap_type, asset_id, asset_ct, asset_cs);
    }
    // Marginal Costs
    if (cap_type != 'storage' && cap_type != 'transport') {
        tr += generate_table_row_info_for_mc(asset_id, asset_mc);
    }
    // Profiles
    if (cap_type == 'consumer' || cap_type == 'producer') {
        tr += generate_table_row_info_for_profile(asset_id, asset_prof);
    }

    tr += '</tr>';
    return tr;
}

function open_es_table_editor(dialog, asset_info_list) {

    var contents = [
//        "  <div class=\"dropdown-container\">",
//        "    <div class=\"dropdown-button noselect\">",
//        "        <div class=\"dropdown-label\">Asset types</div>",
//        "        <div class=\"dropdown-quantity\">(<span class=\"quantity\">Any</span>)</div>",
//        "        <i class=\"fa fa-filter\"></i>",
//        "    </div>",
//        "    <div class=\"dropdown-list\" style=\"display: none;\">",
//        "        <ul id=\"assetlist\">",
//        "          <li><input name=\"asset_producer\" type=\"checkbox\"><label for=\"asset_producer\">Producer</label></li>",
//        "          <li><input name=\"asset_consumer\" type=\"checkbox\"><label for=\"asset_consumer\">Consumer</label></li>",
//        "          <li><input name=\"asset_transport\" type=\"checkbox\"><label for=\"asset_transport\">Transport</label></li>",
//        "          <li><input name=\"asset_conversion\" type=\"checkbox\"><label for=\"asset_conversion\">Conversion</label></li>",
//        "          <li><input name=\"asset_storage\" type=\"checkbox\"><label for=\"asset_storage\">Storage</label></li>",
//        "        </ul>",
//        "    </div>",
//        "  </div>",
//        "  <div class=\"dropdown-container\">",
//        "    <div class=\"dropdown-button noselect\">",
//        "        <div class=\"dropdown-label\">Fields</div>",
//        "        <div class=\"dropdown-quantity\">(<span class=\"quantity\">Any</span>)</div>",
//        "        <i class=\"fa fa-filter\"></i>",
//        "    </div>",
//        "    <div class=\"dropdown-list\" style=\"display: none;\">",
//        "        <input type=\"search\" placeholder=\"Search states\" class=\"dropdown-search\"/>",
//        "        <ul id=\"fieldlist\"></ul>",
//        "    </div>",
//        "</div>",
        "<div class=\"asset-info-list\" id=\"asset-info-list\">",
        "</div>"
    ].join('');

    dialog.setContent(contents);
    dialog.setTitle('ESDL Table editor')

   // Events
//    $('.dropdown-container')
//        .on('click', '.dropdown-button', function() {
//            $(this).siblings('.dropdown-list').toggle();
//        })
//        .on('input', '.dropdown-search', function() {
//            var target = $(this);
//            var dropdownList = target.closest('.dropdown-list');
//            var search = target.val().toLowerCase();
//
//            if (!search) {
//                dropdownList.find('li').show();
//                return false;
//            }
//
//            dropdownList.find('li').each(function() {
//                var text = $(this).text().toLowerCase();
//                var match = text.indexOf(search) > -1;
//                $(this).toggle(match);
//            });
//        })
//        .on('change', '[type="checkbox"]', function() {
//            var container = $(this).closest('.dropdown-container');
//            var numChecked = container. find('[type="checkbox"]:checked').length;
//            container.find('.quantity').text(numChecked || 'Any');
//        });

    // Populate list with states
//    _.each(usStates, function(s) {
//        s.capName = _.startCase(s.name.toLowerCase());
//        element = document.getElementById('ullist');
//        li = stateTemplate(s);
//        $('#fieldlist').append(stateTemplate(s));
//    });

    capabilities = ['producer', 'consumer', 'transport', 'storage', 'conversion']
    field_list = {
        'producer': ['name', 'power'],
        'consumer': ['name', 'power'],
        'transport': ['name', 'capacity'],
        'storage': ['name', 'capacity'],
        'conversion': ['name', 'power', 'efficiency', 'COP', 'heatEfficiency', 'electricalEfficiency' ]
    }
    document.getElementById('asset-info-list').innerHTML = '';

    for (let c=0; c<capabilities.length; c++) {

        if (asset_info_list[capabilities[c]].length > 0) {
            document.getElementById('asset-info-list').innerHTML += '<h1>'+capitalize(capabilities[c])+'</h1>';

            table = '<table class="pure-table pure-table-striped">';
            table += '<thead><tr><th>Type</th>'
            for (let th=0; th<field_list[capabilities[c]].length; th++) {
                table += '<th>' + break_capital(capitalize(field_list[capabilities[c]][th])) + '</th>';
            }
            if (capabilities[c] == 'conversion' || capabilities[c] == 'storage') {
                table += '<th>Control<br>Strategy</th>';
            }
            if (capabilities[c] != 'transport' && capabilities[c] != 'storage') {
                table += '<th>Marginal<br>Costs</th>';
            }
            if (capabilities[c] == 'consumer' || capabilities[c] == 'producer') {
                table += '<th>Profiles</th>';
            }

            table += '</tr></thead><tbody>';
            for (let i=0; i<asset_info_list[capabilities[c]].length; i++) {
                asset = asset_info_list[capabilities[c]][i];
                table += generate_table_row_for_asset(capabilities[c], asset, field_list[capabilities[c]]);
            }

            table += '</tbody></table>';
            document.getElementById('asset-info-list').innerHTML += table;
        }
    }
    dialog.open();
}

function send_table_editor_request() {
    socket.emit('command', {'cmd': 'get_table_editor_info'});
}
