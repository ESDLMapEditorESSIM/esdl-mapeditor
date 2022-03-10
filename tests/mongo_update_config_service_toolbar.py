from extensions.settings_storage import SettingsStorage, SettingType
from bson.objectid import ObjectId

# Database: esdl_mapeditor_settings
# Collection: settings
# Document: per USER, per PROJECT, SYSTEM

store = SettingsStorage(database_uri='mongodb://10.30.2.1:27018/', database='esdl_mapeditor_settings')

val_srvc = None
for doc in store.db.settings.find({'type': SettingType.USER.value}, {'type': 1, 'name': 1, 'ESDL_SERVICES_CONFIG': 1}):
    pipe_dupl_found = False
    if 'ESDL_SERVICES_CONFIG' in doc:

        for ext_svc in doc['ESDL_SERVICES_CONFIG']:
            if ext_svc['id'] == '64fb5727-119e-46a6-b1b3-7ac42dc3d639':  # Pipe duplicator
                pipe_dupl_found = True
                ext_svc['show_on_toolbar'] = True
                ext_svc['icon'] = {
                    'filename': 'Duplicate.png',
                    'type': 'filename'
                }
        if pipe_dupl_found:
            for ext_svc in doc['ESDL_SERVICES_CONFIG']:
                if ext_svc['id'] == '912c4a2b-8eee-46f7-a225-87c5f85e645f':  # ESDL Validator
                    ext_svc['show_on_toolbar'] = True
                    ext_svc['icon'] = {
                        'filename': 'Validator.png',
                        'type': 'filename'
                    }
            store.db.settings.update_one({'_id': doc['_id']}, {'$set': {'ESDL_SERVICES_CONFIG': doc['ESDL_SERVICES_CONFIG']}}, upsert=False)
    else:
        print(f"User {doc['name']} has no ESDL_SERVICES_CONFIG")

    #     store.db.settings.update_one({'_id': doc['_id']}, {'$set': {'ESDL_SERVICES_CONFIG':ext_svc}}, upsert=False)
    # else:
    #     print(f"Could not update services config for {doc['name']}")
