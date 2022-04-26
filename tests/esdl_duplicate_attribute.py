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
from typing import List

from pyecore.ecore import EClass, EEnum

import esdl


class ESDLDuplicateAttributeTest(unittest.TestCase):
    def test_attributes(self):
        """
        List all attributes of a class in ESDL that have the same attribute name when its length is cut at 10 characters
        e.g. temperatureMin and temperatureMax of HeatNetwork.
        Shapefiles' attributes can only have a max of 10 characters is seems.


        """
        print(len(esdl.eClassifiers), "classes in ESDL")
        classes: List[EClass] = esdl.eClassifiers
        for eclass in classes.values():
            attr_dict = {}
            #print(f'Handling {eclass}')
            if isinstance(eclass, EEnum):
                pass # ignore EEnums
            else:
                for attr in eclass.eClass.eAllAttributes():
                    if attr.name[:10] in attr_dict:
                        print(f"Duplicate found in {eclass.eClass.name}: {attr.name[:10]} = {attr.name} and {attr_dict[attr.name[:10]]}")
                    else:
                        attr_dict[attr.name[:10]] = attr.name

    def test_enum(self):
        e = esdl.getEClassifier("EnergyLabelEnum")
        print(e.eClass.eAllAttributes())


if __name__ == '__main__':
    unittest.main()
