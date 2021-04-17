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


if __name__ == '__main__':
    esh = EnergySystemHandler()
    esdl.EnergyAsset.__repr__ = lambda x: '{}(name={})'.format(x.eClass.name, x.name)
    esdl.Carrier.__repr__ = lambda x: '{}(name={})'.format(x.eClass.name, x.name)
    esdl.Port.__repr__ = lambda x: '{}(name={})'.format(x.eClass.name, x.name)
    es, _ = esh.load_file('C:\\Users\\werkmane\\OneDrive - TNO\\Documents\\ESDL\\EnergySystems\\ECW_with_carriers.esdl')
    es: esdl.EnergySystem = es
    pipe13: esdl.Pipe = es.instance[0].area.asset[10]
    print(pipe13, pipe13.port[0], pipe13.port[0].carrier)
    pipe_clone = pipe13.deepcopy()
    print(pipe_clone, pipe_clone.port[0], pipe_clone.port[0].carrier)
