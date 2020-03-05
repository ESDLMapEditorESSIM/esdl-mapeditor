
"""
    "ESSIM": {
        "ESSIM_host": "http://geis.hesi.energy:8112",
        "ESSIM_path": "/essim/simulation",
        "influxURL": "http://geis.hesi.energy:8086",
        "grafanaURL": "http://geis.hesi.energy:3000",
        "user": "essim",
        "start_datetime": "2015-01-01T00:00:00.000000+0100",
        "end_datetime": "2016-01-01T00:00:00.000000+0100"
    }
}
"""








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
            "database": "energy_profiles",
            "measurement": "solar_relative_2011-2016",
            "field": "value",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/u4uAX3PZk/solar?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Electricity households (E1A)",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E1A",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/INOZu3PWz/elektriciteit-huishoudens-2015-nedu-e1a?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Electricity NEDU (E1B)",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E1B",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/yCTWWalZz/nedu-electricity-e1b?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Electricity NEDU (E1C)",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E1C",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/lsiMW-_Zz/nedu-electricity-e1c?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Electricity NEDU (E2A)",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E2A",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/quVnZa_Zk/nedu-electricity-e2a?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Electricity NEDU (E2B)",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E2B",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/BkC7Z-_Wz/nedu-electricity-e2b?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Electricity shops, office, education (E3A)",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E3A",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/wEXMX3EWk/electricity-shops-office-education-e3a?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Electricity prison (E3B)",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E3B",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/44-vX3EZk/electricity-prison-e3b?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Electricity hotel, hospital (E3C)",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E3C",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/iRXduqEZz/electricity-hotel-hospital-e3c?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Electricity greenhouses (E3D)",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E3D",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/G4HpXqEWz/electricity-greenhouses-e3d?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Electricity NEDU (E4A)",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E4A",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/EU5iZ-lWk/nedu-electricity-e4a?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Heating households (G1A)",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "nedu_aardgas_2015-2018",
            "field": "G1A",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/Dw5-u3EWz/heating-households-g1a?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Heating ... (G2A)",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "nedu_aardgas_2015-2018",
            "field": "G2A",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/6IQBuqPWz/heating-g2a?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Heating ... (G2C)",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "nedu_aardgas_2015-2018",
            "field": "G2C",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/GI_Yu3PZz/heating-g2c?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Constant",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "constant",
            "field": "value",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/ZJn5rqPWk/constant?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Wind op land",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "wind-2015",
            "field": "Wind-op-land",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/eeD2r3PWk/wind-op-land?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Wind op zee",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "wind-2015",
            "field": "Wind-op-zee",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/2C-A93EWk/wind-op-zee?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Biomassa",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "biomassa-2015",
            "field": "value",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/dyab9qPWz/biomassa?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Elektriciteit Curacao",
            "required_role": "curacao",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "elektr-curacao-2015",
            "field": "elektr",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/r8oLrqPWz/elektriciteit-curacao?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "Wind Curacao",
            "required_role": "curacao",
            "multiplier": 1,
            "database": "energy_profiles",
            "measurement": "wind-curacao-2015",
            "field": "value",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/KM5U93EZz/wind-curacao?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "NZKG - Industrie (cont)",
            "required_role": "nzkg",
            "multiplier": 1,
            "database": "nzkg_profiles",
            "measurement": "tno_industrie_2015",
            "field": "INDUSTRY_CONT",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/VYfbZ-_Wk/nzkg-industrie-cont?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "NZKG - Industrie (day)",
            "required_role": "nzkg",
            "multiplier": 1,
            "database": "nzkg_profiles",
            "measurement": "tno_industrie_2015",
            "field": "INDUSTRY_DAY",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/AbIaW-_Zk/nzkg-industrie-day?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "NZKG - Industrie (datacenter)",
            "required_role": "nzkg",
            "multiplier": 1,
            "database": "nzkg_profiles",
            "measurement": "tno_industrie_2015",
            "field": "INDUSTRY_DATACENTER",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/u4q-Z-lWk/nzkg-industrie-datacenter?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "NZKG - Industrie (total)",
            "required_role": "nzkg",
            "multiplier": 1,
            "database": "nzkg_profiles",
            "measurement": "tno_industrie_2015",
            "field": "INDUSTRY_TOTAL",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2015-01-01T00:00:00.000000+0100",
            "end_datetime": "2016-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/DiAfZalWz/nzkg-industrie-total?panelId=1&from=1420066800000&to=1451606400000&theme=light"
        },
        {
            "profile_uiname": "GM - Betap_Elektra_Sisalstraat66",
            "required_role": "genemuiden",
            "multiplier": 1,
            "database": "genemuiden",
            "measurement": "genemuiden-GV-2019",
            "field": "Betap_Elektra_Sisalstraat66",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2019-01-01T00:00:00.000000+0100",
            "end_datetime": "2020-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/XDQhsH_Zk/betap_elektra_sisalstraat66?panelId=1&from=1546297200000&to=1577836800000&theme=light"
        },
        {
            "profile_uiname": "GM - Betap_Elektra_Sisalstraat87",
            "required_role": "genemuiden",
            "multiplier": 1,
            "database": "genemuiden",
            "measurement": "genemuiden-GV-2019",
            "field": "Betap_Elektra_Sisalstraat87",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2019-01-01T00:00:00.000000+0100",
            "end_datetime": "2020-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/bDBoyN_Zz/betap_elektra_sisalstraat87?panelId=1&from=1546297200000&to=1577836800000&theme=light"
        },
        {
            "profile_uiname": "GM - Hamat_Elektra_Spoelstraat16",
            "required_role": "genemuiden",
            "multiplier": 1,
            "database": "genemuiden",
            "measurement": "genemuiden-GV-2019",
            "field": "Hamat_Elektra_Spoelstraat16",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2019-01-01T00:00:00.000000+0100",
            "end_datetime": "2020-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/yQgtsNlWz/hamat_elektra_spoelstraat16?panelId=1&from=1546297200000&to=1577836800000&theme=light"
        },
        {
            "profile_uiname": "GM - Hamat_Elektra_Jutestraat7",
            "required_role": "genemuiden",
            "multiplier": 1,
            "database": "genemuiden",
            "measurement": "genemuiden-GV-2019",
            "field": "Hamat_Elektra_Jutestraat7",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2019-01-01T00:00:00.000000+0100",
            "end_datetime": "2020-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/sOUpyHlZz/hamat_elektra_jutestraat7?panelId=1&from=1546297200000&to=1577836800000&theme=light"
        },
        {
            "profile_uiname": "GM - Avimat_Elektra_Sisalstraat36",
            "required_role": "genemuiden",
            "multiplier": 1,
            "database": "genemuiden",
            "measurement": "genemuiden-GV-2019",
            "field": "Avimat_Elektra_Sisalstraat36",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2019-01-01T00:00:00.000000+0100",
            "end_datetime": "2020-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/VdN5yNlWk/avimat_elektra_sisalstraat36?panelId=1&from=1546297200000&to=1577836800000&theme=light"
        },
        {
            "profile_uiname": "GM - Cotap_Elektra_Biezenstraat2",
            "required_role": "genemuiden",
            "multiplier": 1,
            "database": "genemuiden",
            "measurement": "genemuiden-GV-2019",
            "field": "Cotap_Elektra_Biezenstraat2",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2019-01-01T00:00:00.000000+0100",
            "end_datetime": "2020-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/IRcFsNlZk/cotap_elektra_biezenstraat2?panelId=1&from=1546297200000&to=1577836800000&theme=light"
        },
        {
            "profile_uiname": "GM - Cotap_Elektra_Oosterburgstr27",
            "required_role": "genemuiden",
            "multiplier": 1,
            "database": "genemuiden",
            "measurement": "genemuiden-GV-2019",
            "field": "Cotap_Elektra_Oosterburgstr27",
            "profileType": "ENERGY_IN_TJ",
            "start_datetime": "2019-01-01T00:00:00.000000+0100",
            "end_datetime": "2020-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/tZ1OyHlWz/cotap_elektra_oosterburgstr27?panelId=1&from=1546297200000&to=1577836800000&theme=light"
        },
        {
            "profile_uiname": "GM - Cotap_Elektra_Oosterburgstr38",
            "required_role": "genemuiden",
            "multiplier": 1,
            "database": "genemuiden",
            "measurement": "genemuiden-GV-2019",
            "field": "Cotap_Elektra_Oosterburgstr38",
            "profileType": "ENERGY_IN_KWH",
            "start_datetime": "2019-01-01T00:00:00.000000+0100",
            "end_datetime": "2020-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/kLdNyH_Zz/cotap_elektra_oosterburgstr38?panelId=1&from=1546297200000&to=1577836800000&theme=light"
        },
        {
            "profile_uiname": "GM - Rinos_Elektra_KlaasFuitestr11",
            "required_role": "genemuiden",
            "multiplier": 1,
            "database": "genemuiden",
            "measurement": "genemuiden-GV-2019",
            "field": "Rinos_Elektra_KlaasFuitestr11",
            "profileType": "ENERGY_IN_KWH",
            "start_datetime": "2019-01-01T00:00:00.000000+0100",
            "end_datetime": "2020-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/X1xAsNlZz/rinos_elektra_klaasfuitestr11?panelId=1&from=1546297200000&to=1577836800000&theme=light"
        },
        {
            "profile_uiname": "GM - Rinos_Elektra_KlaasFuitestr12",
            "required_role": "genemuiden",
            "multiplier": 1,
            "database": "genemuiden",
            "measurement": "genemuiden-GV-2019",
            "field": "Rinos_Elektra_KlaasFuitestr12",
            "profileType": "ENERGY_IN_KWH",
            "start_datetime": "2019-01-01T00:00:00.000000+0100",
            "end_datetime": "2020-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/IJ51sNlZk/rinos_elektra_klaasfuitestr12?panelId=1&from=1546297200000&to=1577836800000&theme=light"
        },
        {
            "profile_uiname": "GM - Rinos_Elektra_KlaasFuitestr11",
            "required_role": "genemuiden",
            "multiplier": 1,
            "database": "genemuiden",
            "measurement": "genemuiden-GV-2019",
            "field": "Rinos_Elektra_KlaasFuitestr11",
            "profileType": "ENERGY_IN_KWH",
            "start_datetime": "2019-01-01T00:00:00.000000+0100",
            "end_datetime": "2020-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/X1xAsNlZz/rinos_elektra_klaasfuitestr11?panelId=1&from=1546297200000&to=1577836800000&theme=light"
        },
        {
            "profile_uiname": "GM - Rinos_Elektra_KlaasFuitestr12",
            "required_role": "genemuiden",
            "multiplier": 1,
            "database": "genemuiden",
            "measurement": "genemuiden-GV-2019",
            "field": "Rinos_Elektra_KlaasFuitestr12",
            "profileType": "ENERGY_IN_KWH",
            "start_datetime": "2019-01-01T00:00:00.000000+0100",
            "end_datetime": "2020-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/IJ51sNlZk/rinos_elektra_klaasfuitestr12?panelId=1&from=1546297200000&to=1577836800000&theme=light"
        },
        {
            "profile_uiname": "GM - Condor_Elektra_Sasdijk17",
            "required_role": "genemuiden",
            "multiplier": 1,
            "database": "genemuiden",
            "measurement": "genemuiden-GV-2019",
            "field": "Condor_Elektra_Sasdijk17",
            "profileType": "ENERGY_IN_KWH",
            "start_datetime": "2019-01-01T00:00:00.000000+0100",
            "end_datetime": "2020-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/sdZSW1lZk/condor_elektra_sasdijk17?panelId=1&from=1546297200000&to=1577836800000&theme=light"
        },
        {
            "profile_uiname": "GM - Condor_Elektra_Sisalstraat30",
            "required_role": "genemuiden",
            "multiplier": 1,
            "database": "genemuiden",
            "measurement": "genemuiden-GV-2019",
            "field": "Condor_Elektra_Sisalstraat30",
            "profileType": "ENERGY_IN_KWH",
            "start_datetime": "2019-01-01T00:00:00.000000+0100",
            "end_datetime": "2020-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/KczGW1lWk/condor_elektra_sisalstraat30?panelId=1&from=1546297200000&to=1577836800000&theme=light"
        },
        {
            "profile_uiname": "GM - Condor_Elektra_Spoelstraat1",
            "required_role": "genemuiden",
            "multiplier": 1,
            "database": "genemuiden",
            "measurement": "genemuiden-GV-2019",
            "field": "Condor_Elektra_Spoelstraat1",
            "profileType": "ENERGY_IN_KWH",
            "start_datetime": "2019-01-01T00:00:00.000000+0100",
            "end_datetime": "2020-01-01T00:00:00.000000+0100",
            "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/61IiW1_Wk/condor_elektra_spoelstraat1?panelId=1&from=1546297200000&to=1577836800000&theme=light"
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
    "predefined_quantity_and_units": [
        {
            "id": "eb07bccb-203f-407e-af98-e687656a221d",
            "description": "Energy in GJ",
            "physicalQuantity": "ENERGY",
            "multiplier": "GIGA",
            "unit": "JOULE"
        },
        {
            "id": "cc224fa0-4c45-46c0-9c6c-2dba44aaaacc",
            "description": "Energy in TJ",
            "physicalQuantity": "ENERGY",
            "multiplier": "TERRA",
            "unit": "JOULE"
        },
        {
            "id": "e9405fc8-5e57-4df5-8584-4babee7cdf1c",
            "description": "Power in VA",
            "physicalQuantity": "POWER",
            "unit": "VOLT_AMPERE"
        },
        {
            "id": "6279c72a-228b-4c2c-8924-6b794c81778c",
            "description": "Reactive power in VAR",
            "physicalQuantity": "POWER",
            "unit": "VOLT_AMPERE_REACTIVE"
        }
    ],
    "predefined_esdl_services": [
        {
            "id": "18d106cf-2af1-407d-8697-0dae23a0ac3e",
            "name": "Get PICO wind potential",
            "explanation": "This queries the Geodan wind potential service for a certain area",
            "url": "https://pico.geodan.nl/pico/api/v1/<area_scope>/<area_id>/windturbinegebied",
            "http_method": "get",
            "headers": {
                "Accept": "application/esdl+xml",
                "User-Agent": "ESDL Mapeditor/0.1"
            },
            "type": "geo_query",
            "result": [
                {
                    "code": 200,
                    "action": "esdl"
                }
            ],
            "geographical_scope": {
                "url_area_scope": "<area_scope>",
                "url_area_id": "<area_id>",
                "area_scopes": [
                    {"scope": "PROVINCE", "url_value": "provincies"},
                    {"scope": "REGION", "url_value": "resgebieden"},
                    {"scope": "MUNICIPALITY", "url_value": "gemeenten"}
                ]
            },
            "query_parameters": [
                {
                    "name": "Distance to buildings",
                    "description": "Minimum distance to the built environment (in meters)",
                    "parameter_name": "bebouwingsafstand",
                    "type": "integer"
                },
                {
                    "name": "Restriction",
                    "description": "",
                    "parameter_name": "restrictie",
                    "type": "multi-selection",
                    "possible_values": ["natuur", "vliegveld", "infrastructuur", "agrarisch", "turbines"]
                },
                {
                    "name": "Preference",
                    "description": "",
                    "parameter_name": "preferentie",
                    "type": "multi-selection",
                    "possible_values": ["natuur", "vliegveld", "infrastructuur", "agrarisch", "turbines"]
                },
                {
                    "name": "Include geometry in ESDL",
                    "description": "",
                    "parameter_name": "geometrie",
                    "type": "boolean"
                }
            ]
        },
        {
            "id": "50fa716f-f3b0-464c-bf9f-1acffb24f76a",
            "name": "Get PICO solar field potential",
            "explanation": "This queries the Geodan solar field potential service for a certain area",
            "url": "https://pico.geodan.nl/pico/api/v1/<area_scope>/<area_id>/zonneveldgebied",
            "http_method": "get",
            "headers": {
                "Accept": "application/esdl+xml",
                "User-Agent": "ESDL Mapeditor/0.1"
            },
            "type": "geo_query",
            "result": [
                {
                    "code": 200,
                    "action": "esdl"
                }
            ],
            "geographical_scope": {
                "url_area_scope": "<area_scope>",
                "url_area_id": "<area_id>",
                "area_scopes": [
                    {"scope": "PROVINCE", "url_value": "provincies"},
                    {"scope": "REGION", "url_value": "resgebieden"},
                    {"scope": "MUNICIPALITY", "url_value": "gemeenten"}
                ]
            },
            "query_parameters": [
                {
                    "name": "Distance to buildings",
                    "description": "Minimum distance to the built environment (in meters)",
                    "parameter_name": "bebouwingsafstand",
                    "type": "integer"
                },
                {
                    "name": "Restriction",
                    "description": "",
                    "parameter_name": "restrictie",
                    "type": "multi-selection",
                    "possible_values": ["natuur", "vliegveld", "infrastructuur", "agrarisch", "turbines"]
                },
                {
                    "name": "Preference",
                    "description": "",
                    "parameter_name": "preferentie",
                    "type": "multi-selection",
                    "possible_values": ["natuur", "vliegveld", "infrastructuur", "agrarisch", "turbines"]
                },
                {
                    "name": "Include geometry in ESDL",
                    "description": "",
                    "parameter_name": "geometrie",
                    "type": "boolean"
                }
            ]
        },
        {
            "id": "7f8722a9-669c-499d-8d75-4a1960e0429f",
            "name": "Create ETM scenario",
            "explanation": "This service sends the ESDL information to the ETM and tries to generate an ETM scenario out of it.",
            "url": "http://10.30.2.1:7001/api/v1/EnergySystem/",
            # "url": "http://localhost:5000/api/v1/EnergySystem/",
            "http_method": "post",
            "headers": {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            "type": "send_esdl",
            "body": "url_encoded",
            "query_parameters": [],
            "result": [
                {
                    "code": 200,
                    "action": "print"
                }
            ]
        },
        {
            "id": "3e3f3d4d-5600-4f1b-875d-4b630f2f8d01",
            "required_role": "geis",
            "name": "Query Energy Information Base service",
            "explanation": "This service queries multiple (open) energy data sources for a certain area",
            "url": "http://10.30.2.1:2000/api/EnergySystemBuilder/<area_scope>/<area_id>",
            "http_method": "get",
            "headers": {
                "Accept": "test/xml",
                "User-Agent": "ESDL Mapeditor/0.1"
            },
            "type": "geo_query",
            "result": [
                {
                    "code": 200,
                    "action": "esdl"
                }
            ],
            "geographical_scope": {
                "url_area_scope": "<area_scope>",
                # "url_area_subscope": "<area_subscope>",
                "url_area_id": "<area_id>",
                "area_scopes": [
                    {"scope": "PROVINCE", "url_value": "province"},
                    {"scope": "REGION", "url_value": "region"},
                    {"scope": "MUNICIPALITY", "url_value": "municipality"},
                    {"scope": "DISTRICT", "url_value": "district"},
                    {"scope": "NEIGHBOURHOOD", "url_value": "neighbourhood"}
                ],
                "area_subscopes": [
                    {"scope": "PROVINCE", "url_value": "province"},
                    {"scope": "REGION", "url_value": "region"},
                    {"scope": "MUNICIPALITY", "url_value": "municipality"},
                    {"scope": "DISTRICT", "url_value": "districts"},
                    {"scope": "NEIGHBOURHOOD", "url_value": "neighbourhood"}
                ]
            },
            "query_parameters": []
        },
        {
            "id": "193182ba-6805-4555-9f63-a0b2d5bb3d48",
            "required_role": "loadflow",
            "name": "Loadflow Calculation",
            "explanation": "This service runs a specific kind of loadflow calculation on the energysystem (DC loadflow, DC optimal loadflow, AC loadflow, AC optimal loadflow)",
            "url": "http://10.30.2.1:7002/api/v1/PandapowerLoadflow/<method>",
            "http_method": "post",
            "headers": {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "ESDL Mapeditor/0.1"
            },
            "type": "simulation",
            "body": "url_encoded",
            "query_parameters": [
                {
                    "name": "Method",
                    "location": "url",
                    "description": "",
                    "parameter_name": "method",
                    "type": "selection",
                    "possible_values": ["dclf", "dcopf", "lf", "opf"]
                }
            ],
            "result": [
                {
                    "code": 200,
                    "action": "print"
                }
            ]
        },
        {
            "id": "d2ecfa3a-f0cd-4091-a78e-2675801dfcb1",
            "required_role": "urban-strategy",
            "name": "Urban Strategy Charging Stations",
            "explanation": "This service queries the US database for Charging Station information",
            "url": "http://10.30.2.1:7003/api/v1/ChargingStations",
#            "url": "http://localhost:5000/api/v1/ChargingStations",
            "http_method": "get",
            "headers": {
                "Accept": "application/json",
                "User-Agent": "ESDL Mapeditor/0.1"
            },
            "type": "",
            "query_parameters": [
            ],
            "result": [
                {
                    "code": 200,
                    "action": "add_assets"
                }
            ]
        },
        {
            "id": "d0239a80-5ec5-4940-b6df-4d431f7746e8",
            "required_role": "businessparks",
            "name": "Business Parks Information",
            "explanation": "This service queries the IBIS database for Business Parks Information",
            "type": "workflow",
            "workflow": [
                {
                    "nr": 1,
                    "name": "Business Parks",
                    "description": "Select business park(s)",
                    "type": "multi-select-with-filter",
                    "get_select_list": {
                        "url": "http://localhost:5000/api/v1/BusinessParks/",
                        "http_method": "get",
                        "headers": {
                            "Accept": "application/json",
                            "User-Agent": "ESDL Mapeditor/0.1"
                        },
                        "result": {
                            "type": "array_of_arrays",
                            "id_index": 0,
                            "option_name_index": 1
                        }
                    },
                    "select_variable": "selected_parks",
                    "next_step": 2
                },
                {
                    "nr": 2,
                    "name": "Area Contour",
                    "description": "Do you want to get the area contours",
                    "type": "choice",
                    "options": [
                        {
                            "id": 1,
                            "name": "Yes",
                            "next_step": 3
                        },
                        {
                            "id": 2,
                            "name": "No",
                            "next_step": 4
                        }
                    ]
                },
                {
                    "nr": 3,
                    "type": "query",
                    "url": "",
                    "http_method": "get",
                    "headers": {
                        "Accept": "application/json",
                        "User-Agent": "ESDL Mapeditor/0.1"
                    },
                    "result": {

                    },
                },
                {
                    "nr": 4,
                    "name": "Building Contours",
                    "description": "Do you want to get the building contours",
                    "type": "choice",
                    "options": [
                        {
                            "id": 1,
                            "name": "Yes",
                            "next_step": 5
                        },
                        {
                            "id": 2,
                            "name": "No",
                            "next_step": 0
                        }
                    ]
                },
                {
                    "nr": 5,
                    "type": "query",
                    "url": "",
                    "http_method": "get",
                    "headers": {
                        "Accept": "application/json",
                        "User-Agent": "ESDL Mapeditor/0.1"
                    },
                    "result": {

                    },
                }
            ]
        }
    ]
}
