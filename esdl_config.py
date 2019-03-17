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
    ]
}