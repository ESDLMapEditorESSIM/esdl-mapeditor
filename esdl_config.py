esdl_config = {
    "profile_database": {
        "host": "http://10.30.2.1",
        "port": "8086",
        "database": "energy_profiles",
        "filters": ""
    },
    "influxdb_profile_data": [
        {
            "profile_uiname": "Solar",
            "multiplier": 1,
            "measurement": "solar_relative_2011-2016",
            "field": "value",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Electricity households (E1A)",
            "multiplier": 1,
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E1A",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Electricity shops, office, education (E3A)",
            "multiplier": 1,
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E3A",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Electricity prison (E3B)",
            "multiplier": 1,
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E3B",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Electricity hotel, hospital (E3C)",
            "multiplier": 1,
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E3C",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Electricity greenhouses (E3D)",
            "multiplier": 1,
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E3D",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Heating households (G1A)",
            "multiplier": 1,
            "measurement": "nedu_aardgas_2015-2018",
            "field": "G1A",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Heating ... (G2A)",
            "multiplier": 1,
            "measurement": "nedu_aardgas_2015-2018",
            "field": "G2A",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Heating ... (G2C)",
            "multiplier": 1,
            "measurement": "nedu_aardgas_2015-2018",
            "field": "G2C",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Constant",
            "multiplier": 1,
            "measurement": "constant",
            "field": "value",
            "profileType": "ENERGY_IN_TJ"
        }
    ],
    "energy_carriers": [
    ],
    "control_strategies": [
        {
            "name": "DrivenByDemand",
            "applies_to": "Conversion",
            "connect_to": "OutPort"
        },
        {
            "name": "DrivenBySupply",
            "applies_to": "Conversion",
            "connect_to": "InPort"
        },
        {
            "name": "StorageStrategy",
            "applies_to": "Storage",
            "parameters": [
                {
                    "name": "marginalChargeCosts",
                    "type": "SingleValue"
                },
                {
                    "name": "marginalDischargeCosts",
                    "type": "SingleValue"
                }
            ]
        },
    ],
    "ESSIM": {
        "ESSIM_host": "http://10.30.2.1:8112",
        "ESSIM_path": "/essim/simulation",
        "influxURL": "http://10.30.2.1:8086",
        "grafanaURL": "http://geis.hesi.energy:3000",
        "user": "essim"
    }
}