from esdl.esdl_handler import EnergySystemHandler
from esdl import esdl


def deepcopy_conductor_bug():
    esh = EnergySystemHandler()
    esdl.Port.__repr__ = lambda x: '{}: ({})'.format(x.eClass.name, x.name)
    esdl.Pipe.__repr__ = lambda x: '{}: ({})'.format(x.eClass.name, x.name)
    esdl.Import.__repr__ = lambda x: '{}: ({})'.format(x.eClass.name, x.name)

    imp = esdl.Import(name="Import", id="Import")
    imp_outport = esdl.OutPort(id="import_outport", name="import_outport")
    imp.port.append(imp_outport)

    pipe = esdl.Pipe(id="pipe1", name="pipe1")
    pipe_inport = esdl.InPort(id="pipe_inport", name="pipe_inport")
    pipe_outport = esdl.OutPort(id="pipe_outport", name="pipe_outport")
    pipe.port.extend([pipe_inport, pipe_outport])

    imp_outport.connectedTo.append(pipe_inport)

    pipe_a = pipe.deepcopy()
    pipe_a.name = pipe.name + "_A"
    pipe_a.id = pipe.id + "_A"
    pipe_a.port[0].name = pipe_a.port[0].name + '_A'
    pipe_a.port[1].name = pipe_a.port[1].name + '_A'
    pipe_b = pipe.deepcopy()
    pipe_b.name = pipe.name + "_B"
    pipe_b.id = pipe.id + "_B"
    pipe_b.port[0].name = pipe_b.port[0].name + '_B'
    pipe_b.port[1].name = pipe_b.port[1].name + '_B'

    print("Import ports", imp.port)
    print("Import outport connectedTo", imp.port[0].connectedTo)
    print("Pipe ports", pipe.port)
    print("Pipe inport connectedTo", pipe.port[0].connectedTo)
    print("Pipe outport connectedTo", pipe.port[1].connectedTo)

    print("Pipe A ports", pipe_a.port)
    print("Pipe A inport connectedTo", pipe_a.port[0].connectedTo)
    print("Pipe A outport connectedTo", pipe_a.port[1].connectedTo)

    print("Pipe B ports", pipe_b.port)
    print("Pipe B inport connectedTo", pipe_b.port[0].connectedTo)
    print("Pipe B outport connectedTo", pipe_b.port[1].connectedTo)

    pipe_a.port.clear()
    pipe_b.port.clear()

    pass


def no_deepcopy_conductor_bug():
    esh = EnergySystemHandler()
    esdl.Port.__repr__ = lambda x: '{}: ({})'.format(x.eClass.name, x.name)
    esdl.Pipe.__repr__ = lambda x: '{}: ({})'.format(x.eClass.name, x.name)
    esdl.Import.__repr__ = lambda x: '{}: ({})'.format(x.eClass.name, x.name)

    imp = esdl.Import(name="Import", id="Import")
    imp_outport = esdl.OutPort(id="import_outport", name="import_outport")
    imp.port.append(imp_outport)

    pipe = esdl.Pipe(id="pipe1", name="pipe1")
    pipe_inport = esdl.InPort(id="pipe_inport", name="pipe_inport")
    pipe_outport = esdl.OutPort(id="pipe_outport", name="pipe_outport")
    pipe.port.extend([pipe_inport, pipe_outport])

    imp_outport.connectedTo.append(pipe_inport)


    pipe_a = esdl.Pipe()
    pipe_a.name = pipe.name + "_A"
    pipe_a.id = pipe.id + "_A"
    pipe_a_inport = esdl.InPort(id="pipe_inport_A", name="pipe_inport_A")
    pipe_a_outport = esdl.OutPort(id="pipe_outport_A", name="pipe_outport_A")
    pipe_a.port.extend([pipe_a_inport, pipe_a_outport])
    pipe_a_inport.connectedTo.append(imp_outport)



    pipe_b = esdl.Pipe()
    pipe_b.name = pipe.name + "_B"
    pipe_b.id = pipe.id + "_B"
    pipe_b_inport = esdl.InPort(id="pipe_inport_B", name="pipe_inport_B")
    pipe_b_outport = esdl.OutPort(id="pipe_outport_B", name="pipe_outport_B")
    pipe_b.port.extend([pipe_b_inport, pipe_b_outport])
    pipe_b_inport.connectedTo.append(imp_outport)

    print("Import ports", imp.port)
    print("Import outport connectedTo", imp.port[0].connectedTo)
    print("Pipe ports", pipe.port)
    print("Pipe inport connectedTo", pipe.port[0].connectedTo)
    print("Pipe outport connectedTo", pipe.port[1].connectedTo)

    print("Pipe A ports", pipe_a.port)
    print("Pipe A inport connectedTo", pipe_a.port[0].connectedTo)
    print("Pipe A outport connectedTo", pipe_a.port[1].connectedTo)

    print("Pipe B ports", pipe_b.port)
    print("Pipe B inport connectedTo", pipe_b.port[0].connectedTo)
    print("Pipe B outport connectedTo", pipe_b.port[1].connectedTo)

    #pipe_a.port.clear()
    #pipe_b.port.clear()
    # pipe_a_inport.delete()
    # pipe_a_outport.delete()
    # pipe_b_inport.delete()
    # pipe_b_outport.delete()
    for p in list(pipe_a.port):
        p.delete()
    for p in list(pipe_b.port):
        p.delete()

    print("Import ports", imp.port)
    print("Import outport connectedTo", imp.port[0].connectedTo)
    print("Pipe ports", pipe.port)
    print("Pipe inport connectedTo", pipe.port[0].connectedTo)
    print("Pipe outport connectedTo", pipe.port[1].connectedTo)

    print("Pipe A ports", pipe_a.port)
    print("Pipe A inport connectedTo", pipe_a.port[0].connectedTo if len(pipe_a.port)>0 else None)
    print("Pipe A outport connectedTo", pipe_a.port[1].connectedTo if len(pipe_a.port)>1 else None)

    print("Pipe B ports", pipe_b.port)
    print("Pipe B inport connectedTo", pipe_b.port[0].connectedTo if len(pipe_b.port)>0 else None)
    print("Pipe B outport connectedTo", pipe_b.port[1].connectedTo if len(pipe_b.port)>1 else None)

    pass

if __name__ == '__main__':
    no_deepcopy_conductor_bug()