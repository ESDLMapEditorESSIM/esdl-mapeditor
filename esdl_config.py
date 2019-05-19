esdl_config = {
    "profile_database": {
        "host": "http://app-iot03.hex.tno.nl",
        "port": "8086",
        "database": "energy_profiles",
        "filters": ""
    },
    "influxdb_profile_data": [
        {
            "profile_uiname": "Relative solar profile",
            "multiplier": 1,
            "measurement": "sun-perc-2015-15min",
            "field": "percentage",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Relative electricity demand",
            "multiplier": 1,
            "measurement": "Edemand-perc-2015-15min",
            "field": "percentage",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Relative heating demand",
            "multiplier": 1,
            "measurement": "EHP-perc-2015-15min",
            "field": "percentage",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Relative constant profile",
            "multiplier": 1,
            "measurement": "const-perc-2015-15min",
            "field": "percentage",
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
        "influxURL": "http://dido.cloud.iplab.tno.nl:8086",
        "grafanaURL": "http://dido.cloud.iplab.tno.nl:3000",
        "user": "essim"
    }
}