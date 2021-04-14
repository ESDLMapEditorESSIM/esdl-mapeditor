"""
This work is based on original code copyrighted by TNO.

Licensed to TNO under one or more contributer license agreements.

TNO licenses this work to you under the Apache License, Version 2.0 
You may obtain a copy of the license at http://www.apache.org/licenses/LICENSE-2.0

Contributors:
	TNO 		- Initial implementation

:license: Apache License, Version 2.0
"""

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
from extensions.merge import ESDLMerge


def test():
    esh = EnergySystemHandler()
    #left = esh.load_file('Right1_with_ESI.esdl')
    left = esh.load_file('Left.esdl')

    #right = esh.import_file('Right1_with_ESI.esdl')
    right = esh.import_file('Right1_with_ESI_and_connectedTo_and_carrier.esdl')
    #right = esh.import_file('Left.esdl')

    merge = ESDLMerge()
    merge.config(forceCombineMainArea=True)

    es = merge.merge(left,right)
    print(esh.to_string())


if __name__ == '__main__':
    test()