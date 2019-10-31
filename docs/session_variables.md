# Session variables

### Generic data
store_item_metadata     The metadata from the item loaded from the store
es_simid                Simulation ID that ESSIM creates after starting a new simulation
user-role               Role of logged in user
simulationRun           End result id of ESSIM simulation
adding_edr_assets       The ESDL asset template from EDR

### Energysystem data
port_to_asset_mapping   Mapping from port IDs to assets
conn_list               Connection list
carrier_list            Carrier list

### Energysystem metadata
es_title                ES Title
es_id                   ES ID
es_descr                ES description
es_filename             ES filename (when loaded from filesystem)
es_email                Email of the ES 'owner'


# Detailed information per session variable

## store_item_metadata
The metadata from the item loaded from the store
- If an ESDL item is loaded from the store, the metadata (a.o. the store ID) is stored and can be used when an item must be stored again

## es_simid
Simulation ID that ESSIM creates after starting a new simulation

## user-role
Role of logged in user

Used for:
- ESDL store vs Mondaine Hub
- ESSIM functionality

## simulationRun
End result id of ESSIM simulation

## port_to_asset_mapping
Mapping from port IDs to assets

## conn_list
Connection list

## color_method [removed]
Determines how buildings are colored

## adding_edr_assets
the ESDL asset template from EDR

## es_title
## es_id
## es_descr
## carrier_list
## es_filename
## es_email


 variable | get_session | set_session |
--- | ---: | ---: |
es_title | 2 | 1 |
es_id | 4 | 2 |
es_descr | 0 | 1 |
es_filename | 0 | 3 |
es_email | 0 | 1 |
port_to_asset_mapping | 7 | 6 |
conn_list | 5 | 6 |
carrier_list | 0 | 1 -> 0 | 