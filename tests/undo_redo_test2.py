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
from pprint import pprint

import esdl
from esdl.esdl_handler import EnergySystemHandler
from pyecore.commands import Delete


def main():
    esh = EnergySystemHandler()
    es, _ = esh.load_file('esdl/Left.esdl')
    tracker = esh.change_tracker
    stack = tracker.get_tracker_stack(es)

    es: esdl.EnergySystem = esh.energy_system

    stack.start_recording(combineCommands=True, label="add pipes")
    pipe1 = esdl.Pipe(name="TestPipe1", id='TestPipe1')
    pipe2 = esdl.Pipe(name="TestPipe2", id='TestPipe2')
    ip1 = esdl.InPort(name="TestIP1", id="Pipe1IP1")
    op1 = esdl.OutPort(name="TestOP1", id="Pipe2OP1")
    pipe1.port.append(ip1)
    pipe2.port.append(op1)
    es.instance[0].area.asset.append(pipe1)
    es.instance[0].area.asset.append(pipe2)
    stack.add_undo_step("add connected to")
    ip1.connectedTo.append(op1)
    print('Inport 1 connected to:', ip1.connectedTo)
    stack.stop_recording()
    pprint(stack.stack)
    stack.undo()
    print('Inport 1 connected to after undo:', ip1.connectedTo)
    stack.redo()
    print('Inport 1 connected to after redo:', ip1.connectedTo)


    print("\n====================================== TEST 2: delete InPort 1 of Pipe1 ===========================")

    stack.start_recording(combineCommands=True, label="Delete Port1")
    print("Ports of Pipe1 before port delete:", pipe1.port)
    print("Ports of Pipe1 before connectedTo:", pipe1.port[0].connectedTo)
    ip1.delete(recursive=True)
    print("Ports of Pipe1 after port delete:", pipe1.port)
    stack.stop_recording()
    stack.undo()
    print("Ports of Pipe1 after undo:", pipe1.port)
    #print("Pipe1 after undo connectedTo:", pipe1.port[0].connectedTo)

    print("\n====================================== TEST 3: delete all of Pipe1 ===========================")
    stack.start_recording(combineCommands=True, label="Delete Pipe1")
    print('Before deletion assets:', [a.name for a in es.instance[0].area.asset])
    pipe1.delete(recursive=True)
    print('After deletion assets:', [a.name for a in es.instance[0].area.asset])
    stack.stop_recording()

    stack.undo()
    print('After undo deletion of Pipe1 assets:', [a.name for a in es.instance[0].area.asset])

    stack.stop_recording()



    """
      
self.references = {<esdl.esdl.Pipe object at 0x000000000469FE08>: [(<EReference area: <class 'esdl.esdl.Area'>>, <esdl.esdl.Area object at 0x000000000469F2C8>), (<EReference controlStrategy: <class 'esdl.esdl.ControlStrategy'>>, None), (<EReference behaviour: <class 'esdl.esdl.AbstractBehaviour'>>, EOrderedSet()), (<EReference isOwnedBy: <class 'esdl.esdl.Party'>>, None), (<EReference containingBuilding: <class 'esdl.esdl.AbstractBuilding'>>, None), (<EReference geometry: <class 'esdl.esdl.Geometry'>>, None), (<EReference costInformation: <class 'esdl.esdl.CostInformation'>>, None), (<EReference KPIs: <class 'esdl.esdl.KPIs'>>, None), (<EReference material: <class 'esdl.esdl.AbstractMatter'>>, None), (<EReference dataSource: <class 'esdl.esdl.AbstractDataSource'>>, None), (<EReference port: <class 'esdl.esdl.Port'>>, EOrderedSet()), (<EReference sector: <class 'esdl.esdl.Sector'>>, None)], <esdl.esdl.OutPort object at 0x000000000469FA88>: [(<EReference energyasset: <class 'esdl.esdl.EnergyAsset'>>, <esdl.esdl.Pipe object at 0x000000000469FE08>), (<EReference connectedTo: <class 'esdl.esdl.InPort'>>, EOrderedSet()), (<EReference carrier: <class 'esdl.esdl.Carrier'>>, None), (<EReference profile: <class 'esdl.esdl.GenericProfile'>>, EOrderedSet())]}
self.inverse_references = {<esdl.esdl.Pipe object at 0x000000000469FE08>: [], <esdl.esdl.OutPort object at 0x000000000469FA88>: []}
    """
    ip1.connectedTo.append(op1)
    d = Delete(owner=pipe2)
    print('Before delete Pipe2:', [a.name for a in es.instance[0].area.asset])
    if d.can_execute: d.do_execute()
    print('After delete Pipe2:', [a.name for a in es.instance[0].area.asset])
    print(d.references)
    print(d.inverse_references)
    d.undo()
    print('After undo delete Pipe2:', [a.name for a in es.instance[0].area.asset])
    print('ports of Pipe2: ', [p.name for p in d.owner.port])

    print('ports connectedTo of Pipe2: ', [[q.name +'-'+p.name for p in q.connectedTo] for q in d.owner.port])




if __name__ == '__main__':
    main()