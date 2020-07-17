# ESDL MapEditor

## Introduction

Map-based ESDL editor, allows loading, editing and saving ESDL EnergySystem files,
as well as integration with various external services (ESSIM, Energy Data
Repository, BAG, ...).

## Installation

1. Clone this repository.

2. Install the dependencies:

```shell
pip install -r requirements.txt
```

## Starting the application

1. Start a local MongoDB:

```shell
make mongo
```

2. Run `python app.py` or `make dev` and open browser on `http://localhost:8111`.

The application serves as a simple webserver and serves index.html and the images.
There is a websocket connection between the python application and browser for
bi-directional communication.

## Deployment

In production the service runs in Docker and uses an external MongoDB. The
production service uses UWSGI.

The deployment scripts are docker-container.redeploy.sh and
beta-docker-container-redeploy.sh. These should be executed from a machine in the
GEIS cluster.

## Documentation

### Session variables

| Variable name         | Type | Meaning
| --------------------- | -----|-------- |
| asset_dict            | Dictionary | Gives the asset using the asset id as a key
| carrier_list          | Array of objects | List of all carriers in the energy system
| color_method          | String | Method to color the building polygons. Can be "buildingyear", "floor area" or "type"
| conn_list             | Array of objects | List of all connections between assets (port id, asset id, location)
| es_descr              | String | The description of the energy system (Meta information for ESDL store)
| es_edit               | String | The energy system that is currently being editted
| es_email              | String | The email of the editor of the energy system (Meta information for ESDL store)
| es_id                 | String | The id of the energy system (Meta information for ESDL store)
| es_title              | String | The title of the energy system (Meta information for ESDL store)
| es_start              | String | currently not used. Can be "new", "load_file" or "load_store"
| port_to_asset_mapping | Dictionary | Gives the asset id and coordinate using the port id as a key

### Python functions

write_energysystem_to_file(filename, es)
create_ESDL_store_item(id, es, title, description, email)
load_ESDL_EnergySystem(id)
store_ESDL_EnergySystem(id, es)
send_ESDL_as_file(es, name)
get_boundary_from_service(scope, id)
get_subboundaries_from_service(scope, subscope, id)
_parse_esdl_subpolygon(subpol)
create_boundary_from_contour(contour)
create_boundary_from_geometry(geometry)
_convert_coordinates_into_subpolygon(coord_list)
_convert_pcoordinates_into_polygon(coord_list)
_convert_mpcoordinates_into_multipolygon(coord_list)
create_geometry_from_geom(geom)
_determine_color(asset, color_method)
_find_more_area_boundaries(this_area)
find_boundaries_in_ESDL(top_area)
add_header(r)
index()
serve_static(path)
send_html(path)
parse_esdl_config()
send_alert(message)
find_area(area, area_id)
_find_asset_in_building(building, asset_id)
find_asset(area, asset_id)
find_potential(area, pot_id)
_find_asset_in_building_and_container(building, asset_id)
find_asset_and_container(area, asset_id)
add_asset_to_area(es, asset, area_id)
add_asset_to_building(es, asset, building_id)
_remove_port_references(port)
_remove_object_from_building(building, object_id)
_recursively_remove_object_from_area(area, object_id)
remove_object_from_energysystem(es, object_id)
get_asset_capability_type(asset)
get_carrier_list(es)
_set_carrier_for_connected_transport_assets(asset_id, carrier_id, processed_assets)
set_carrier_for_connected_transport_assets(asset_id, carrier_id)
initialize()
_create_building_asset_dict(asset_dict, building)
_create_area_asset_dict(asset_dict, area)
create_asset_dict(area)
create_building_port_to_asset_mapping(building, mapping)
create_port_to_asset_mapping(area, mapping)
generate_point_in_area(boundary)
update_building_asset_geometries(building, avail_locations)
update_area_asset_geometries(area, avail_locations)
count_building_assets_and_potentials(building)
count_assets_and_potentials(area)
calculate_triangle_center(triangle)
update_asset_geometries(area, boundary)
update_asset_geometries2(area, boundary)
generate_profile_info(profile)
process_building(asset_list, area_bld_list, conn_list, port_asset_mapping, building, level)
process_area(asset_list, area_bld_list, conn_list, port_asset_mapping, area, level)
add_connection_to_list(conn_list, from_port_id, from_asset_id, from_asset_coord, to_port_id, to_asset_id, to_asset_coord)
update_asset_connection_locations(ass_id, lat, lon)
update_transport_connection_locations(ass_id, asset, coords)
distance(origin, destination)
get_connected_to_info(asset)
connect_ports(port1, port2)
connect_asset_with_conductor(asset, conductor)
connect_asset_with_asset(asset1, asset2)
connect_conductor_with_conductor(conductor1, conductor2)
get_asset_attributes(asset)
get_potential_attributes(potential)
distance_point_to_line(p, p1, p2)
split_conductor(conductor, location, mode, conductor_container)
process_command(message)
process_file_command(message)
load_esdl_file(message)
update_coordinates(message)
update_line_coordinates(message)
get_boundary_info(info)
initialize_app()
on_connect()
on_disconnect()


#### Commented out
download_esdl(path)
download_esdl(path)
send_image(path)
send_plugin(path)
send_icon(path)


### Python sockets

#### Incoming

@socketio.on('command', namespace='/esdl')
@socketio.on('file_command', namespace='/esdl')
@socketio.on('load_esdl_file', namespace='/esdl')
@socketio.on('update-coord', namespace='/esdl')
@socketio.on('update-line-coord', namespace='/esdl')
@socketio.on('get_boundary_info', namespace='/esdl')
@socketio.on('connect', namespace='/esdl')
@socketio.on('disconnect', namespace='/esdl')

#### Outgoing

emit('area_boundary', {'info-type': 'P-WGS84', 'crs': 'WGS84', 'boundary': boundary, 'color': AREA_LINECOLOR, 'fillcolor': AREA_FILLCOLOR})
emit('area_boundary', {'info-type': 'MP-WGS84', 'crs': 'WGS84', 'boundary': boundary, 'color': AREA_LINECOLOR, 'fillcolor': AREA_FILLCOLOR})
emit('area_boundary', {'info-type': 'MP-RD', 'crs': 'RD', 'boundary': boundary, 'color': AREA_LINECOLOR, 'fillcolor': AREA_FILLCOLOR})
emit('area_boundary', {'info-type': 'P-WGS84', 'crs': 'WGS84', 'boundary': boundary, 'color': building_color, 'name': name, 'boundary_type': 'building'})
emit('alert', message)
emit('clear_connections')
emit('add_connections', conn_list)
emit('clear_connections')
emit('add_connections', conn_list)
emit('add_new_conn', [[asset_geom.get_lat(),asset_geom.get_lon()],[first_point.get_lat(),first_point.get_lon()]])
emit('add_new_conn',
emit('add_new_conn',
emit('add_new_conn',
emit('add_new_conn',
emit('add_new_conn',
emit('add_new_conn',
emit('add_esdl_objects', {'list': esdl_assets_to_be_added, 'zoom': False})
emit('clear_connections')
emit('add_connections', conn_list)
emit('add_esdl_objects', {'list': asset_to_be_added_list, 'zoom': False})
emit('portlist', port_list)
emit('add_new_conn',
emit('asset_info', {'id': object_id, 'name': name, 'attrs': attrs_sorted, 'connected_to_info': connected_to_info})
emit('asset_info', {'id': asset_id, 'name': name, 'latlng': latlng, 'attrs': attrs_sorted, 'connected_to_info': connected_to_info})
emit('port_profile_info', profile_info)
emit('port_profile_info', {'class': 'SingleValue', 'value': 1, 'type': 'ENERGY_IN_TJ'})
emit('carrier_list', carrier_list)
emit('clear_ui', {'layer': 'buildings'})
emit('clear_ui', {'layer': 'areas'})
emit('clear_ui')
emit('add_esdl_objects', {'list': asset_list, 'zoom': True})
emit('area_bld_list', area_bld_list)
emit('add_connections', conn_list)
emit('carrier_list', carrier_list)
emit('es_title', title)
emit('store_list', store_list)
emit('clear_ui')
emit('add_esdl_objects', {'list': asset_list, 'zoom': True})
emit('area_bld_list', area_bld_list)
emit('add_connections', conn_list)
emit('es_title', es_title)
emit('carrier_list', carrier_list)
emit('and_now_press_download_file')
emit('clear_ui')
emit('add_esdl_objects', {'list': asset_list, 'zoom': True})
emit('area_bld_list', area_bld_list)
emit('add_connections', conn_list)
emit('es_title', es_title)
emit('carrier_list', carrier_list)
emit('area_boundary', {'info-type': 'MP-WGS84', 'crs': 'WGS84', 'boundary': geom, 'color': AREA_LINECOLOR, 'fillcolor': AREA_FILLCOLOR})
emit('clear_ui')
emit('es_title', es_title)
emit('add_esdl_objects', {'list': asset_list, 'zoom': True})
emit('area_bld_list', area_bld_list)
emit('add_connections', conn_list)
emit('carrier_list', carrier_list)
emit('profile_info', esdl_config.esdl_config['influxdb_profile_data'])

### Javascript functions

function uuidv4()
function calculate_length(layer)
splitConductorCallback = function(e)
splitConductorConnectCallback = function(e)
splitConductorAddJointCallback = function(e)
addProfileToPort = function(e)
setCarrier = function(e)
function connectAssets(object)
function set_marker_handlers(marker)
function set_line_handlers(line)
function conn_assets_window()
function conn_disconn_assets()
function new_ESDL()
function click_new_ESDL_button(obj)
function boundary_info_window()
function get_boundary_info(obj)
function add_carrier()
function select_other_carrier()
function energy_carrier_info()
function open_ESDL(event)
function send_cmd_load_ESDL()
function click_load_ESDL_button(obj)
function save_ESDL()
function send_cmd_store_ESDL()
function send_download_ESDL()
function add_profile_to_port()
function add_port(direction, asset_id)
function remove_port(pid)
function change_param(obj)
function ClickMarker(e)
function connectAsset(e)
function connectConductor(e)
function splitConductor(id, location, mode)

### Javascript sockets

#### Incoming

socket.on('connect', function() 
socket.on('log', function(msg) 
socket.on('clear_ui', function(msg) 
socket.on('add_marker', function(point_coords) 
socket.on('add_esdl_objects', function(options) 
socket.on('esdltxt', function(esdl_text) 
socket.on('area_bld_list', function(areas_buildings) 
socket.on('clear_connections', function() 
socket.on('add_connections', function(connections) 
socket.on('add_new_conn', function(connection) 
socket.on('store_list', function(store_items) 
socket.on('asset_info', function(asset_info) 
socket.on('conductor_info', function(asset_info) 
socket.on('port_profile_info', function(profile_info) 
socket.on('es_title', function(title) 
socket.on('alert', function(message) 
socket.on('area_boundary', function(area_boundary) 
socket.on('profile_info', function(pa) 
socket.on('carrier_list', function(carr_list) 
socket.on('and_now_press_download_file', function() 

#### Outgoing 

socket.emit('command', {cmd: 'set_carrier', asset_id: asset_id, carrier_id: carrier_id});
socket.emit('command', {cmd: 'connect_assets', id1: first_clicked_id, id2: object.id});
socket.emit('update-coord', {id: marker.id, lat: pos.lat, lng: pos.lng, asspot: marker.asspot});
socket.emit('command', {cmd: 'remove_object', id: marker.id, asspot: marker.asspot});
socket.emit('command', {cmd: 'get_object_info', id: id, asspot: marker.asspot});
socket.emit('command', {cmd: 'remove_object', id: line.id});
socket.emit('command', {cmd: 'get_conductor_info', id: line.id, latlng: e.latlng});
socket.emit('file_command', {cmd: 'new_esdl', title: new_title, description: new_description,
socket.emit('get_boundary_info', {identifier: identifier, scope: scope, subscope: subscope,
socket.emit('command', {cmd: 'add_carrier', type: carr_type, name: carr_name, emission: carr_emission,
socket.emit('command', {cmd: 'add_carrier', type: carr_type, name: carr_name, voltage: carr_voltage});
socket.emit('command', {cmd: 'add_carrier', type: carr_type, name: carr_name, pressure: carr_pressure});
socket.emit('command', {cmd: 'add_carrier', type: carr_type, name: carr_name, suptemp: carr_suptemp,
socket.emit('command', {cmd: 'add_carrier', type: carr_type, name: carr_name});
socket.emit('load_esdl_file', content);
socket.emit('file_command', {cmd: 'get_list_from_store'});
socket.emit('file_command', {cmd: 'load_esdl_from_store', id: es_id});
socket.emit('file_command', {cmd: 'save_esdl'});
socket.emit('file_command', {cmd: 'store_esdl'});
socket.emit('file_command', {cmd: 'download_esdl'});
socket.emit('command', {cmd: 'add_profile_to_port', port_id: port_id, multiplier: multiplier,
socket.emit('command', {cmd: 'add_port', direction: direction, asset_id: asset_id, pname: pname});
socket.emit('command', {cmd: 'remove_port', port_id: pid});
socket.emit('command', {cmd: 'set_asset_param', id: asset_id, param_name: asset_param_name, param_value: asset_param_value});
socket.emit('command', {cmd: 'split_conductor', id: id, location: location, mode: mode});
socket.emit('mngmnt', {data: 'I\'m connected!'});
socket.emit('command', {cmd: 'set_building_color_method', method: selected_method});
socket.emit('update-line-coord', {id: layer.id, polyline: layer.getLatLngs(), length: polyline_length});
socket.emit('command', {'cmd': 'get_port_profile_info', 'port_id': port_id});
socket.emit('command', {'cmd': 'connect_ports', port1id: connect_ports, port2id: port_id});
socket.emit('command', {cmd: 'add_asset', area_bld_id: selected_area_bld_id, asset: selected_asset, asset_name: layer.name, asset_id: layer.id, lat: layer.getLatLng().lat, lng: layer.getLatLng().lng});
socket.emit('command', {cmd: 'add_asset', area_bld_id: selected_area_bld_id, asset: line_type, asset_name: layer.name, asset_id: layer.id, polyline: layer.getLatLngs(), length: polyline_length});
socket.emit('command', {cmd: 'set_area_bld_polygon', area_bld_id: selected_area_bld_id, polygon: layer.getLatLngs()});
