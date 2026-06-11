import unittest

from pyecore.resources import ResourceSet
from pyecore.resources.json import JsonResource

from esdl import esdl
from esdl.processing.string_uri import StringURI
from esdlproject.ProjectManager import ProjectManager, resource_as_string
from esdlproject.change_handler import applyChange

import json
import datetime


class DateTimeEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()

        return super(DateTimeEncoder, self).default(obj)


class SerializeHLCTest(unittest.TestCase):

    def test_track_changes(self):
        pm = ProjectManager()
        es = pm.get_active_energy_system()

        stack = pm.get_undo_redo_stack()
        stack.start_recording(label="Add pipe1")
        pipe1 = esdl.Pipe(name="pipe1")
        es.instance[0].area.asset.append(pipe1)
        stack.stop_recording()

        print(f'pipe1 resource: {pipe1.eResource}, {pipe1.eURIFragment()}')

        hlc = stack.top
        print(hlc)

        pm.rset.resource_factory['json'] = lambda uri: JsonResource(uri, indent=2)
        uri = StringURI("test.json")
        resource = pm.rset.create_resource(uri)
        resource.append(hlc)
        options = dict()
        options['encoder'] = DateTimeEncoder
        resource.save(options=options)
        hlc_string = uri.getvalue()
        print(hlc_string)

        pm2 = ProjectManager()
        es2 = pm2.get_active_energy_system()
        resource2 = es2.eResource
        tracker2 = pm2.active_tracker

        # TODO deserialize back to a change

        uri = StringURI("hlc.json", hlc_string)
        external_rset = ResourceSet()
        external_resource = external_rset.create_resource(uri)
        external_resource.load()
        external_hlc = external_resource.contents[0]
        print(external_hlc)

        tracker2.stack.start_recording(label=external_hlc.label)
        print(f"Handling High level change {external_hlc.label}")
        for change in external_hlc.change:
            applyChange(change, resource2, pm2.active_variant)
        tracker2.stack.stop_recording()

        print(es2)
        for a in es2.instance[0].area.asset:
            print(a)


if __name__ == '__main__':
    unittest.main()
