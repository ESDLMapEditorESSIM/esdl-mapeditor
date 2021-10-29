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
from pyecore.notification import EObserver, Notification, Kind
from pyecore.ecore import EObject
from esdl.undo import UndoRedoCommandStack, monitor_esdl_changes

import esdl




def test():
    stack = UndoRedoCommandStack()  # keep track of all undo-redo stuff using notifications

    #monitor_esdl_changes(stack)

    esh = EnergySystemHandler()
    esdl.EnergySystem.__repr__ = lambda x: '{}(name={})'.format(x.eClass.name, x.name)
    es, _ = esh.load_file('esdl\Left.esdl')
    es: esdl.EnergySystem = es
    es2, _ = esh.import_file('esdl\Right1.esdl')
    print(esh.rset.resources)
    resource = esh.get_resource(es.id)
    print(resource.uri.plain)
    from esdl.undo import ResourceObserver
    ro = ResourceObserver(command_stack=stack)

    ro.observe(resource)

    stack.start_recording(combineCommands=True)
    #changeESName = Set(owner=es, feature='name', value="Please undo me!")
    #stack.execute(changeESName)
    print('Initial value:', es.name, es.description)
    #stack.undo()
    es.name = "Please undo me!"
    print('Updated value:', es.name, es.description)
    stack.add_undo_step()
    es.description = "cool"
    stack.stop_recording()
    print('Updated value2:', es.name, es.description)
    stack.undo()
    print('Undone:', es.name, es.description)

    stack.redo()
    print('Redo:', es.name, es.description)
    print(stack.stack)

    stack.undo()
    print('Undo again:', es.name, es.description)
    print(stack.stack)

    stack.undo()
    print('Undo again:', es.name, es.description)
    print(stack.stack)

    print("---- next test ----")

    stack.start_recording(combineCommands=True)
    area: esdl.Area = es.instance[0].area
    #observer.observe(area)
    #addAsset = Add(owner=area, feature='asset', value=chp)
    #stack.execute(addAsset)
    print('Area name:' + area.name)
    area.name = 'test area'
    print('Area name after change:' + area.name)
    #stack.undo()
    #print('Area name after undo:' + area.name)
    #print('Area assets', area.asset)
    chp = esdl.CHP(id="CHP", name="CHP", fuelType=esdl.PowerPlantFuelEnum.NATURAL_GAS)
    area.asset.append(chp)
    print('Area assets after adding CHP', area.asset)
    stack.stop_recording()
    stack.undo()
    print('Area assets after undo', area.asset)
    print('Area name after undo:' + area.name)

    r2Stack = UndoRedoCommandStack()
    ResourceObserver(r2Stack).observe(esh.get_resource(es_id=es2.id))
    r2Stack.start_recording()
    stack.start_recording(combineCommands=True)
    es2.name = 'test'
    stack.stop_recording()
    r2Stack.stop_recording()
    r2Stack.undo()
    print(es2.name)


    # print(stack.stack)
    # if stack.can_redo():
    #     stack.redo()
    # if stack.can_redo():
    #     stack.redo()
    # if stack.can_redo():
    #     stack.redo()
    # if stack.can_redo():
    #     stack.redo()
    # else:
    #     print("cant redo")
    # print(stack.stack)
    # print(esh.to_string())
    #
    # #while stack.can_undo():
    # #   stack.undo()
    # #
    # print(esh.to_string())

if __name__ == '__main__':
    test()


