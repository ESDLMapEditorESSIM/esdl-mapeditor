var esdl_services_information

function set_esdl_services_information(info) {
    esdl_services_information = info;
}

function query_esdl_service(index) {
    params = {};

    params['service_id'] = esdl_services_information[index]['id'];
    params['area_scope'] = document.getElementById('area_scope').options[document.getElementById('area_scope').selectedIndex].value;
    params['area_id'] = document.getElementById('area_id').value;

    params['query_params'] = {}
    q_params = esdl_services_information[index]['query_parameters'];
    for (i=0; i<q_params.length; i++) {
        parameter_name = q_params[i]['parameter_name'];
        ptype = q_params[i]['type'];
        if (ptype == 'integer') {
            parameter_value = document.getElementById(parameter_name+'_integer').value;
        }
        else if (ptype == 'boolean') {
            parameter_value = document.getElementById(parameter_name+'_boolean').options[document.getElementById(parameter_name+'_boolean').selectedIndex].value;
        }
        else if (ptype == 'multi-selection') {
            parameter_value = document.getElementById(parameter_name+'_select').options[document.getElementById(parameter_name+'_select').selectedIndex].value;
        }
        params['query_params'][parameter_name] = parameter_value;
    }

    console.log(params);

    socket.emit('command', {cmd: 'query_esdl_service', params: params});
}

function show_service_settings(index) {
    service_settings_div = document.getElementById('service_settings_div');

    service_settings_div.innerHTML += '<h1>' + esdl_services_information[index]['name'] + '</h1>';
    service_settings_div.innerHTML += '<h3>Geographical selection</h3>';

    gs_info = esdl_services_information[index]['geographical_scope'];
    scopes = gs_info['area_scopes'];

    table = '<table>';
    table += '<tr><td width=180>Scope</td><td><select id="area_scope">';
    for (i=0; i<scopes.length; i++) {
        table += '<option value="'+scopes[i]['url_value']+'">'+scopes[i]['scope']+'</option>';
    }
    table += '</select></td></tr>';
    table += '<tr><td width=180>Area id</td><td><input id="area_id" type="text"></input></td></tr>';
    table += '</table>';
    service_settings_div.innerHTML += table;

    service_settings_div.innerHTML += '<h3>Service parameters</h3>';

    q_params = esdl_services_information[index]['query_parameters'];

    table = '<table>';
    for (i=0; i<q_params.length; i++) {
        table += '<tr><td width=180>'+q_params[i]['name']+'</td><td>';

        ptype = q_params[i]['type'];
        if (ptype == 'integer') {
            table += '<input id="'+q_params[i]['parameter_name']+'_integer" type="text"></input>';
        }
        else if (ptype == 'boolean') {
            table += '<select id="'+q_params[i]['parameter_name']+'_boolean"><option value="true">TRUE</value><option value="false">FALSE</value></select>';
        }
        else if (ptype == 'multi-selection') {
            table += '<select id="'+q_params[i]['parameter_name']+'_select" multiple>';
            pos_values = q_params[i]['possible_values'];
            for (j=0; j<pos_values.length; j++) {
                table += '<option value="'+pos_values[j]+'">'+pos_values[j]+'</option>';
            }
            table += '</select>'
        }
        table += '</td></tr>'
        // table += '<option value="'++'">'++'</option>';
    }

    table += '</table>';
    service_settings_div.innerHTML += table;

    service_settings_div.innerHTML += '<button id="query_service_button" onclick="query_esdl_service('+index+');sidebar.hide();">Query ESDL Service</button>';
}

function esdl_services_info() {
    sidebar_ctr = sidebar.getContainer();

    sidebar_ctr.innerHTML = '<h1>ESDL services:</h1>';

    if (esdl_services_information) {
        table = '<table>';
        for (i=0; i<esdl_services_information.length; i++) {
            // id, name
            table += '<tr><td><button onclick="show_service_settings('+i+');">Run</button></td><td>' + esdl_services_information[i]['name']  + '</td></tr>';
        }
        table += '</table>';
        sidebar_ctr.innerHTML += table;
    } else {
        sidebar_ctr.innerHTML += 'No external ESDL services defined yet';
    }

    sidebar_ctr.innerHTML += '<div id="service_settings_div"></div>'

    sidebar.show();
}
