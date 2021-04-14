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

from esdl.processing.EcoreDocumentation import EcoreDocumentation
from esdl import GenericProducer, GenericConsumer
from pyecore.ecore import EClass, EAttribute

if __name__ == '__main__':
    doc = EcoreDocumentation(esdlEcoreFile='c:\data\git\esdl\esdl\model\esdl.ecore')
    p = GenericProducer()
    attribute = 'power'
    #powerAttribute: EAttribute = p.eClass.findEStructuralFeature('power2')
    unit = doc.get_unit(p.eClass.name, attribute)
    print("Unit of {} is in {}".format(attribute, unit if unit else '[not defined]'))
    attribute = 'maxTemperature'
    unit = doc.get_unit('HeatProducer', attribute)
    print("Unit of {} is in {}".format(attribute, unit if unit else '[not defined]'))
    print(doc.get_esdl_version())

