import unittest

from pyecore.resources.json import JsonResource

from esdl import esdl, EnergySystem, GenericProducer, InPort, OutPort, GenericConsumer, Instance, HeatCommodity
from esdl.processing.string_uri import StringURI
from esdlproject.ChangeSerializer import deepcopy_eobject_change
from esdlproject.ProjectManager import ProjectManager, convertActionToVariantChanges, resource_as_string, \
    actionToHighlevelChange
from esdlproject.variant_api import create_new_variant



import json
import datetime


class DateTimeEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()

        return super(DateTimeEncoder, self).default(obj)

class EventTest(unittest.TestCase):


    def test_track_changes(self):
        pm = ProjectManager()
        es = pm.get_active_energy_system()



        stack = pm.get_undo_redo_stack()
        stack.start_recording(label="Add pipe1")
        pipe1 = esdl.Pipe(name="pipe1")
        es.instance[0].area.asset.append(pipe1)
        stack.stop_recording()
        print(f'pipe1 resource: {pipe1.eResource}, {pipe1.eURIFragment()}')

        hlc = actionToHighlevelChange(stack.top)

        print(hlc)

        pm.rset.resource_factory['json'] = lambda uri: JsonResource(uri, indent=2)

        uri = StringURI("test.json")
        resource = pm.rset.create_resource(uri)
        resource.append(hlc)
        options = dict()
        options['encoder'] = DateTimeEncoder
        resource.save(options=options)
        print(uri.getvalue())




        # print(pm.to_debug_string())
        # print("active es:")
        # print(resource_as_string(es.eResource))











if __name__ == '__main__':
    unittest.main()
