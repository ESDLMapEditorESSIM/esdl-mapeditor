#  This work is based on original code developed and copyrighted by TNO 2020.
#  Subsequent contributions are licensed to you by the developers of such code and are
#  made available to the Project under one or several contributor license agreements.
#
#  This work is licensed to you under the Apache License, Version 2.0.
#  You may obtain a copy of the license at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Contributors:
#      TNO         - Initial implementation
#  Manager:
#      TNO
 
from uuid import uuid4
from pyecore.ecore import EDate
from esdl import esdl
from esdl.processing.ESDLEcore import instantiate_type
from extensions.session_manager import get_handler, get_session
from extensions.profiles import Profiles
from utils.utils import str2float
from utils.datetime_utils import parse_date


def get_control_strategy_info(asset):
    """
    Builds up a dictionary with information about the control strategy for the asset

    :param EnergyAsset asset: the asset for which the control strategy info must be built
    :return dict: the control strategy information
    """
    control_strategy = asset.controlStrategy
    cs_info = dict()
    if control_strategy:
        cs_info = {
            'id': control_strategy.id,
            'name': control_strategy.name,
            'type': type(control_strategy).__name__
        }
        if isinstance(control_strategy, esdl.DrivenByDemand):
            if control_strategy.outPort:
                cs_info['port_id'] = control_strategy.outPort.id
        if isinstance(control_strategy, esdl.DrivenBySupply):
            if control_strategy.inPort:
                cs_info['port_id'] = control_strategy.inPort.id
        if isinstance(control_strategy, esdl.DrivenByProfile):
            if control_strategy.port:
                cs_info['port_id'] = control_strategy.port.id

            # EDate.to_string = lambda d: d.isoformat()
            profile_info = dict()
            if isinstance(control_strategy.profile, esdl.DateTimeProfile):
                profile_info['type'] = 'datetime'
                pe_list = list()
                for pe in control_strategy.profile.element:
                    pe_list.append({
                        'key': str(uuid4()),
                        'datetime': pe.from_.strftime("%Y-%m-%d %H:%M:%S"),
                        'profilevalue': pe.value
                    })
                profile_info['list'] = pe_list
            if isinstance(control_strategy.profile, esdl.InfluxDBProfile):
                profiles = Profiles.get_instance().get_profiles()['profiles']
                for pkey in profiles:
                    std_p = profiles[pkey]
                    p = control_strategy.profile
                    if p.database == std_p['database'] and p.measurement == std_p['measurement'] and p.field == std_p['field']:
                        profile_info['id'] = pkey
                        profile_info['type'] = 'database'
                # TODO: support external profiles 

            cs_info['profile'] = profile_info

        if isinstance(control_strategy, esdl.StorageStrategy):
            mcc_sv = control_strategy.marginalChargeCosts
            if isinstance(mcc_sv, esdl.SingleValue):
                mcc = mcc_sv.value
            else:
                mcc = 0
            mdc_sv = control_strategy.marginalDischargeCosts
            if isinstance(mdc_sv, esdl.SingleValue):
                mdc = mdc_sv.value
            else:
                mdc = 0
            cs_info['marginal_charge_costs'] = mcc
            cs_info['marginal_discharge_costs'] = mdc
        if isinstance(control_strategy, esdl.CurtailmentStrategy):
            cs_info['max_power'] = control_strategy.maxPower
        if isinstance(control_strategy, esdl.PIDController):
            cs_info['kp'] = control_strategy.Kp
            cs_info['ki'] = control_strategy.Ki
            cs_info['kd'] = control_strategy.Kd
            if control_strategy.sensor:
                cs_info['sensor_id'] = control_strategy.sensor.id
            else:
                cs_info['sensor_id'] = None
            if control_strategy.setPoint:
                cs_info['pid_setpoint'] = control_strategy.setPoint.value
            else:
                cs_info['pid_setpoint'] = None

    return cs_info


def set_control_strategy(asset, cs_info):
    """
    Sets or updates the control strategy for the asset 

    :param EnergyAsset asset: the asset for which the control strategy info must be set or updated
    :param dict cs_info: dictionairy with the control strategy information
    """
    print(cs_info)

    active_es_id = get_session('active_es_id')
    esh = get_handler()
    
    control_strategy = asset.controlStrategy
    # If no control strategy yet or change of type
    if not control_strategy or type(control_strategy).__name__ != cs_info['type']:
        if control_strategy:
            # remove current strategy
            services = control_strategy.eContainer()
            services.service.remove(control_strategy)
            esh.remove_object_from_dict(active_es_id, control_strategy, True)
        # create new control strategy
        if cs_info['type'] != 'None':  # strategy is removed, and a new one is configured
            control_strategy = instantiate_type(cs_info['type'])
            control_strategy.id = str(uuid4())
            control_strategy.name = cs_info['type'] + ' for ' + asset.name
            control_strategy.energyAsset = asset

            es = esh.get_energy_system(active_es_id)
            services = es.services
            if not services:
                services = esdl.Services(id=str(uuid4()))
                es.services = services
                esh.add_object_to_dict(active_es_id, services)

            services.service.append(control_strategy)
            esh.add_object_to_dict(active_es_id, control_strategy)

    if isinstance(control_strategy, esdl.DrivenByDemand):
        control_strategy.outPort = esh.get_by_id(active_es_id, cs_info['port_id']) 
    if isinstance(control_strategy, esdl.DrivenBySupply):
        control_strategy.inPort = esh.get_by_id(active_es_id, cs_info['port_id']) 
    if isinstance(control_strategy, esdl.StorageStrategy):
        control_strategy.marginalChargeCosts = esdl.SingleValue(
            id=str(uuid4()),
            name='marginalChargeCosts for ' + asset.name,
            value=str2float(cs_info['marginal_charge_costs'])
        )
        control_strategy.marginalDischargeCosts = esdl.SingleValue(
            id=str(uuid4()),
            name='marginalChargeCosts for ' + asset.name,
            value=str2float(cs_info['marginal_discharge_costs'])
        )
        esh.add_object_to_dict(active_es_id, control_strategy.marginalChargeCosts)
        esh.add_object_to_dict(active_es_id, control_strategy.marginalDischargeCosts)
    if isinstance(control_strategy, esdl.CurtailmentStrategy):
        control_strategy.maxPower = str2float(cs_info['max_power'])
    if isinstance(control_strategy, esdl.PIDController):
        control_strategy.Kp = str2float(cs_info['kp'])
        control_strategy.Ki = str2float(cs_info['ki'])
        control_strategy.Kd = str2float(cs_info['kd'])

        if cs_info['sensor_id'] != 'Select sensor...':
            control_strategy.sensor = esh.get_by_id(active_es_id, cs_info['sensor_id'])
        control_strategy.setPoint = esdl.SingleValue(
            id=str(uuid4()),
            name='PID setPoint for ' + asset.name,
            value=str2float(cs_info['pid_setpoint'])
        )
        esh.add_object_to_dict(active_es_id, control_strategy.setPoint)
    if isinstance(control_strategy, esdl.DrivenByProfile):
        control_strategy.port = esh.get_by_id(active_es_id, cs_info['port_id']) 
        if cs_info['profile']['type'] == 'database':
            pid = cs_info['profile']['id']

            profiles = Profiles.get_instance().get_profiles()['profiles']
            for pkey in profiles:
                if pkey == pid:
                    p = profiles[pkey]
                    profile = esdl.InfluxDBProfile(
                        id=str(uuid4()),
                        name=p['profile_uiname'],
                        startDate=EDate.from_string(p['start_datetime']),
                        endDate=EDate.from_string(p['end_datetime']),
                        database=p['database'], 
                        measurement=p['measurement'],
                        field=p['field']
                    )        
                    control_strategy.profile = profile
                    esh.add_object_to_dict(active_es_id, profile)
        if cs_info['profile']['type'] == 'datetime':
            list = cs_info['profile']['list']

            control_strategy.profile = esdl.DateTimeProfile(
                id=str(uuid4()),
                name="Profile for DrivenByProfile strategy"
            )
            for pe in list:
                profile_element = esdl.ProfileElement(
                    from_=EDate.from_string(str(parse_date(pe['datetime']))),
                    value=str2float(pe['profilevalue'])
                )
                control_strategy.profile.element.append(profile_element)
            esh.add_object_to_dict(active_es_id, control_strategy.profile)
