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

import unittest
from pprint import pprint

from esdl.patch import patch_esdl
from esdlproject import Add, DetailedChange
from esdlproject.ChangeSerializer import filterDoubleConnectedTo


class TestFilterChanges(unittest.TestCase):
    
    data = [
         Add(feature="connectedTo", ownerFragment="//@instance.0/@area/@asset.237/@port.0", objectFragment="//@instance.0/@area/@asset.30/@port.0"),
         Add(feature="connectedTo", ownerFragment="//@instance.0/@area/@asset.30/@port.0", objectFragment="//@instance.0/@area/@asset.237/@port.0"),
         Add(feature="connectedTo", ownerFragment="//@instance.0/@area/@asset.30/@port.0", objectFragment="//@instance.0/@area/@asset.238/@port.0"),
         Add(feature="connectedTo", ownerFragment="//@instance.0/@area/@asset.238/@port.0", objectFragment="//@instance.0/@area/@asset.30/@port.0"),
         Add(feature="connectedTo", ownerFragment="//@instance.0/@area/@asset.238/@port.0", objectFragment="//@instance.0/@area/@asset.30/@port.0"),
         Add(feature="connectedTo", ownerFragment="//@instance.0/@area/@asset.30/@port.0", objectFragment="//@instance.0/@area/@asset.238/@port.0"),
         Add(feature="connectedTo", ownerFragment="//@instance.0/@area/@asset.97/@port.0", objectFragment="//@instance.0/@area/@asset.239/@port.0"),
         Add(feature="connectedTo", ownerFragment="//@instance.0/@area/@asset.239/@port.0", objectFragment="//@instance.0/@area/@asset.97/@port.0"),
         Add(feature="connectedTo", ownerFragment="//@instance.0/@area/@asset.239/@port.0", objectFragment="//@instance.0/@area/@asset.97/@port.0"),
         Add(feature="connectedTo", ownerFragment="//@instance.0/@area/@asset.97/@port.0", objectFragment="//@instance.0/@area/@asset.239/@port.0"),
         Add(feature="connectedTo", ownerFragment="//@instance.0/@area/@asset.111/@port.0", objectFragment="//@instance.0/@area/@asset.240/@port.0"),
         Add(feature="connectedTo", ownerFragment="//@instance.0/@area/@asset.240/@port.0", objectFragment="//@instance.0/@area/@asset.111/@port.0"),
         Add(feature="connectedTo", ownerFragment="//@instance.0/@area/@asset.240/@port.0", objectFragment="//@instance.0/@area/@asset.111/@port.0"),
         Add(feature="connectedTo", ownerFragment="//@instance.0/@area/@asset.111/@port.0", objectFragment="//@instance.0/@area/@asset.240/@port.0")
    ]
    def test_filter_double_connectedTo(self):
        patch_esdl()
        print(len(self.data))

        result = filterDoubleConnectedTo(self.data)
        print(len(result))
        pprint(result)

        original_hash = getattr(Add, "__hash__", None)
        original_eq = Add.__eq__
        try:
            Add.__hash__ = lambda x: hash((x.feature, x.ownerFragment, x.objectFragment))
            Add.__eq__ = lambda x, y: y is not None and (
                (x.objectFragment == y.objectFragment and x.ownerFragment == y.ownerFragment) or
                (x.objectFragment == y.ownerFragment and x.ownerFragment == y.objectFragment)
            )
            result = set(self.data)
            print(len(result))
            pprint(result)
        finally:
            Add.__eq__ = original_eq
            Add.__hash__ = original_hash



if __name__ == '__main__':
    unittest.main()
