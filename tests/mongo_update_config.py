from extensions.settings_storage import SettingsStorage, SettingType
from bson.objectid import ObjectId

# Database: esdl_mapeditor_settings
# Collection: settings
# Document: per USER, per PROJECT, SYSTEM

store = SettingsStorage(database_uri='mongodb://10.30.2.1:27018/', database='esdl_mapeditor_settings')

val_srvc = None
for doc in store.db.settings.find({'type': SettingType.USER.value}, {'type':1, 'name':1, 'ESDL_SERVICES_CONFIG':1}):
    if doc['_id'] == ObjectId('5ea7e32a4d6cf3c602c69d1f'):        # Edwin
        for ext_svc in doc['ESDL_SERVICES_CONFIG']:
            if ext_svc['id'] == '912c4a2b-8eee-46f7-a225-87c5f85e645f':          # ESDL Validator
                val_srvc = ext_svc
    else:
        if val_srvc and 'ESDL_SERVICES_CONFIG' in doc and doc['ESDL_SERVICES_CONFIG'][-1]['id'] != '912c4a2b-8eee-46f7-a225-87c5f85e645f':
            ext_svc = doc['ESDL_SERVICES_CONFIG']
            ext_svc.append(val_srvc)
            store.db.settings.update_one({'_id': doc['_id']}, {'$set': {'ESDL_SERVICES_CONFIG':ext_svc}}, upsert=False)
        else:
            print(f"Could not update services config for {doc['name']}")
