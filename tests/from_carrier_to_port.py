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

from esdl.esdl_handler import EnergySystemHandler
from esdl import esdl
from pyecore.ecore import EStructuralFeature, EReference

if __name__ == '__main__':
    esh = EnergySystemHandler()
    esdl.EnergySystem.__repr__ = lambda x: '{}(name={})'.format(x.eClass.name, x.name)
    es, _ = esh.load_file("C:\\Users\\werkmane\\OneDrive - TNO\\Documents\\ESDL\\EnergySystems\\ECW_with_carriers.esdl")
    es:esdl.EnergySystem = es
    carrier: esdl.Carrier = es.energySystemInformation.carriers.carrier[0]
    print(carrier)
    print(es.instance[0].area.asset[0].port[0].carrier)
    p:esdl.Port = es.instance[0].area.asset[0].port[0]
    r:EReference = p.eClass.findEStructuralFeature('carrier')
    print(r)
    # carrier relatie van port naar carrier moet bi-directional zijn.
