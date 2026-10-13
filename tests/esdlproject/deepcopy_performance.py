#  This work is based on original code developed and copyrighted by TNO 2026.
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
import os
import time
from uuid import uuid4

from pyecore.resources import URI

from esdl.processing.string_uri import StringURI
from esdl.resources.resource_type import ProjectManagerResourceType
from esdl.resources.xmlresource import XMLResource
from esdl.support_functions import get_all_references_for_class, get_all_attributes_for_class
from esdl.project.ProjectManager import ProjectManager, get_variant_collection

"""
Test the performance of EObject.deepcopy() 
"""
class DeepCopyPerformanceMain():
    def test_deepcopy_performance(self):
        pm = ProjectManager()
        pm.load(URI('../resources/Drenthe_huidig_met_IIS.project'))
        pm.debug(dump_project=False)

        variant = pm.get_active_variant()
        variant_collection = get_variant_collection(variant)
        es = variant_collection.energysystemRef

        # noinspection PyTypeChecker
        snapshot_resource: XMLResource = pm.rset.create_resource(
            StringURI(f"Snapshot_{variant.name}_{str(uuid4())[:4]}.esdl"))
        snapshot_resource.type = ProjectManagerResourceType.SNAPSHOT
        print(f'Saving variant snapshot for "{variant.name}" (in {variant.eResource}) to {snapshot_resource.uri}')

        runtimes = []
        for i in range(15):
            start = time.time()
            snapshot_resource.set_content(es.deepcopy(uuid_dict=snapshot_resource.uuid_dict))
            end = time.time()
            runtime = round(end - start, 2)
            print(f"Runtime {i}: " + str(runtime) + "s")
            runtimes.append(runtime)

        print(f"Average: {sum(runtimes) / len(runtimes)}")

        # average without optimization: 3.1 seconds for deepcopy Drenthe
        # improvement with eIsSet check: 2.23 seconds
        # improvement with cached eAllStructuralFeatures(): 1.75 seconds  (with profiler: 5.5s)
        # improvement with internal cached eAllStructuralFeatures 1.7 s  (with profiler: 4.8s)
        print(get_all_attributes_for_class.cache_info())
        print(get_all_references_for_class.cache_info())



        # snapshot = snapshot_resource.contents[0]  # link to snapshot resource energy system
        # variant.snapshotRef = snapshot

if __name__ == '__main__':
    cwd = os.getcwd()
    print('Current working directory:', cwd)
    m = DeepCopyPerformanceMain()
    m.test_deepcopy_performance()