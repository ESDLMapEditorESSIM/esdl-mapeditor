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

from pyecore.ecore import EReference
from extensions.session_manager import get_session, set_session
from esdl import esdl
import src.log as log
from uuid import uuid4

logger = log.get_logger(__name__)


def get_cost_information(obj):
    """
    Builds up a dictionary with cost information about the object

    :param EObject obj: the object for which the cost information must be collected
    :return dict: the dictionary with all required information
    """
    result = list()
    # for x in esdl.costInformation.eAllStructuralFeatures:
    #     if isinstance(x, EReference):
    #         result[x.name] = dict()
    # result['investmentCosts'] = dict()
    # result['installationCosts'] = dict()
    # result['fixedOperationalAndMaintenanceCosts'] = dict()
    # result['variableOperationalAndMaintenanceCosts'] = dict()
    # result['marginalCosts'] = dict()

    ci = obj.costInformation
    for x in esdl.CostInformation.eClass.eAllStructuralFeatures():
        if isinstance(x, EReference):
            ci_instance = dict()
            ci_instance['key'] = str(uuid4())
            ci_instance['name'] = x.name

            if ci:
                profile = ci.eGet(x)
                if profile:
                    if isinstance(profile, esdl.SingleValue):
                        ci_instance['value'] = profile.value
                        # TODO: support for QaU
                    else:
                        logger.warn('Cost information profiles other than SingleValue are not supported')
                        ci_instance['value'] = 0
                else:
                    ci_instance['value'] = 0
            else:
                ci_instance['value'] = 0

            result.append(ci_instance)
 
    return result

