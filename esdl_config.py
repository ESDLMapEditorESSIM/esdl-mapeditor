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
        },
        {
            "profile_uiname": "Wind op land",
            "multiplier": 1,
            "measurement": "wind-2015",
            "field": "Wind-op-land",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Wind op zee",
            "multiplier": 1,
            "measurement": "wind-2015",
            "field": "Wind-op-zee",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Biomassa",
            "multiplier": 1,
            "measurement": "biomassa-2015",
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
        "ESSIM_host": "http://geis.hesi.energy:8112",
        "ESSIM_path": "/essim/simulation",
        "influxURL": "http://geis.hesi.energy:8086",
        "grafanaURL": "http://geis.hesi.energy:3000",
        "user": "essim",
        "start_datetime": "2015-01-01T00:00:00+0100",
        "end_datetime": "2016-01-01T00:00:00+0100"
    }
}