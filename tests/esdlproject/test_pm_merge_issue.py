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
import uuid

from pyecore.ecore import EObject

from esdl import esdl
from src.esdl_integration.processing import ESDLGeometry
from esdlproject.ProjectManager import ProjectManager
from esdlproject.variant_api import create_new_variant
from src.log import get_logger

logger = get_logger(__name__)


class ProjectManagerMergeTests(unittest.TestCase):
    def test_merge_issue(self):
        EObject.__repr__ = lambda x: f"<{x.eClass.name} name='{x.name if hasattr(x, 'name') else ''}'>"
        pm = ProjectManager()
        v = pm.get_active_variant()
        v.name = "Nu"
        v2030 = create_new_variant(v, "2030")
        es = pm.get_active_energy_system()
        ct1 = pm.get_change_tracker_for_variant(v)
        ct1.stack.start_recording(label="add Pipe")
        pipe = esdl.Pipe(name="Pipe1", length=39878.3, id="abcdefg")
        line1 = esdl.Line(CRS="WGS84")
        line1.point.append(esdl.Point(lat=52.06006076854822, lon=4.747467041015625, elevation=0.0))
        line1.point.append(esdl.Point(lat=52.2109090072155, lon=5.277557373046875, elevation=0.0))
        pipe.geometry = line1
        pipe.port.append(esdl.InPort(name="pipe1_ip"))
        pipe.port.append(esdl.OutPort(name="pipe1_op"))
        es.instance[0].area.asset.append(pipe)
        ct1.stack.stop_recording()

        pm.set_active_variant(v2030)
        es2030 = pm.get_active_energy_system()
        ct2 = pm.get_change_tracker_for_variant(v2030)
        ct2.stack.start_recording(label="add PV")
        pv = esdl.PVPark(name="PV1")
        pv.port.append(esdl.OutPort(name="pv_op"))
        pv.port.append(esdl.InPort(name="pv_ip"))
        es2030.instance[0].area.asset.append(pv)
        ct2.stack.stop_recording()

        pm.set_active_variant(v)
        es = pm.get_active_energy_system()
        ct1.stack.start_recording(label="split")
        location = {"lat": 52.14435975538461, "lng": 5.04140477061156}
        split_conductor(pipe, location, "add_joint", pipe.eContainer())
        ct1.stack.stop_recording()

        # this triggers merge issues:
        # because split_conductor() remove the initial Pipe and then splits it into two Pipes, the order in the
        # area.asset[] list, will change and URI fragments in Changes are not correct anymore.
        # Initial Nu        [Pipe1]
        # Inititial V2030   [Pipe1, PVPark]
        # Then split_conductor
        # Nu:               [Pipe1a, Pipe1b, Joint] with connection from Pipe1a to Joint and and Pipe1b to Joint
        # V2030:            [PVPark, Pipe1a, Pipe1b, Joint]
        # Note: changes are applied by date order, therefore PVPark comes first in V2023, and not the
        # split_conductor result.
        pm.set_active_variant(v2030)
        es = pm.get_active_energy_system()
        for asset in es.instance[0].area.asset:
            print(f"{asset}:")
            for port in asset.port:
                print(f"-- {port} connectedTo:  {port.connectedTo}")
                print(f"-- {port.eURIFragment()} connectedTo:  {[p.eURIFragment() for p in port.connectedTo]}")
                # for op in port.connectedTo:
                #     print(f"==== {op} ({op.energyasset})")

        # validate connections
        # Pipe1_a - OutPort -connectedTo-> InPort - Joint - OutPort -connectedTo-> Pipe1_b
        assets = es.instance[0].area.asset
        self.assertEqual(len(assets), 4)
        self.assertEqual(assets[0].eClass.name, "PVPark")
        self.assertEqual(assets[1].name, "Pipe1_a")
        self.assertEqual(assets[2].name, "Pipe1_b")
        self.assertEqual(assets[3].eClass.name, "Joint")
        self.assertEqual(len(assets[1].port[0].connectedTo), 0)
        self.assertEqual(len(assets[1].port[1].connectedTo), 1)
        self.assertEqual(len(assets[2].port[0].connectedTo), 1)
        self.assertEqual(len(assets[2].port[1].connectedTo), 0)
        self.assertEqual(len(assets[3].port[0].connectedTo), 1)
        self.assertEqual(len(assets[3].port[1].connectedTo), 1)
        self.assertEqual(assets[3].port[1].connectedTo[0], assets[2].port[0])
        self.assertEqual(assets[3].port[0].connectedTo[0], assets[1].port[1])




def split_conductor(conductor, location, mode, conductor_container):
    geometry = conductor.geometry
    conductor_id = conductor.id
    middle_point = esdl.Point(lat=location['lat'], lon=location['lng']) #no elevation?

    if isinstance(geometry, esdl.Line):
        #create two seperate line segments
        line1 = esdl.Line()
        line2 = esdl.Line()

        #find piece of line where user clicked
        points = geometry.point
        begin_point = points[0]
        first_point = points[0]  # make an additional copy
        # Ewoud: this code is not so nice since it manipulates the original geometry.point with points.pop(0) later on
        # this should be fixed, but not now (not time)

        # pyEcore: somehow using points[0] does something strange in the serialization to XML
        # instead of <point xsi:type="esdl:Point"> you get <esdl:Point lat=...> which is wrong
        # duplicating this point manually fixes this, probably because there is a reference to this point
        # elsewhere which gets serialized as an <esdl:Point>
        # officially we should duplicate all Point in this code
        line1.point.append(esdl.Point(lat=begin_point.lat, lon=begin_point.lon, elevation=begin_point.elevation))

        points.pop(0)
        min_dist = 1e99
        segm_ctr = 0
        min_dist_segm = 0
        for point in points:
            p1 = {'x': begin_point.lat, 'y': begin_point.lon}
            p2 = {'x': point.lat, 'y': point.lon}
            p = {'x': location['lat'], 'y': location['lng']}
            dist = ESDLGeometry.distance_point_to_line(p, p1, p2)
            if dist < min_dist:
                min_dist = dist
                min_dist_segm = segm_ctr
            begin_point = point
            segm_ctr += 1

        # copy appropriate points in original conductor to either line1 or line2
        points = geometry.point
        segm_ctr = 0
        #logger.debug('segment min = {}'.format(min_dist_segm))
        for point in list(points):
            if segm_ctr == min_dist_segm:
                new_point = esdl.Point(lon=middle_point.lon, lat=middle_point.lat, elevation=middle_point.elevation)
                line1.point.append(new_point)
                line2.point.append(new_point.clone())
            if segm_ctr < min_dist_segm:
                line1.point.append(point)
            else:
                line2.point.append(point)
            segm_ctr += 1

        # find old ports and connections
        ports = conductor.port
        if len(ports) != 2:
            logger.warning('UNSUPPORTED: Conductor doesn\'t have two ports!')
            return
        port1 = ports[0].clone()        # reuse old conductor's ports; TODO: check what happens after deleting conductor
        port2 = ports[1].clone()

        new_cond1_id = str(uuid.uuid4())
        new_cond2_id = str(uuid.uuid4())
        new_port1_id = str(uuid.uuid4())
        new_port2_id = str(uuid.uuid4())

        # create two conductors of same type as conductor that is splitted by duplicating the original
        # e.g. also copy over the pipe material
        new_cond1 = conductor.deepcopy()
        new_cond2 = conductor.deepcopy()
        if new_cond1.name == new_cond1.eClass.name + '_' + new_cond1.id[:4]:
            new_cond1.name = new_cond1.eClass.name + '_' + new_cond1_id[:4]
            new_cond2.name = new_cond2.eClass.name + '_' + new_cond2_id[:4]
        else:
            new_cond2.name = new_cond1.name + '_b'
            new_cond1.name = new_cond1.name + '_a'
        new_cond1.id = new_cond1_id
        # remove existing ports, as we add previous used ports later
        for p in list(new_cond1.port):
            p.delete()
        #new_cond1.port.clear()  #  pyEcore bug when clearing connectedTo references are not correctly updated
        new_cond2.id = new_cond2_id
        for p in list(new_cond2.port):
            p.delete()
        #new_cond2.port.clear()  #  pyEcore bug when clearing connectedTo references are not correctly updated
        # pm.add_object_to_dict(active_es_id, new_cond1)
        # pm.add_object_to_dict(active_es_id, new_cond2)

        if type(port1).__name__ == "InPort":
            new_port2 = esdl.OutPort(id=new_port2_id, name='Out')
        else:
            new_port2 = esdl.InPort(id=new_port2_id, name='In')

        new_cond1.port.append(port1)
        new_cond1.port.append(new_port2)

        if type(port2).__name__ == "InPort":
            new_port1 = esdl.OutPort(id=new_port1_id, name='Out')
        else:
            new_port1 = esdl.InPort(id=new_port1_id, name='In')
        if mode == 'connect':
            new_port1.connectedTo.append(new_port2)
            new_port2.connectedTo.append(new_port1)
        new_cond2.port.append(new_port1)
        new_cond2.port.append(port2)

        # pm.add_object_to_dict(active_es_id, new_port1)
        # pm.add_object_to_dict(active_es_id, new_port2)

        # calculate line lengths
        start = line1.point[0]
        length = 0
        for i in range(1, len(line1.point)):
            length += ESDLGeometry.distance((start.lat, start.lon), (line1.point[i].lat, line1.point[i].lon)) * 1000
            start = line1.point[i]
        new_cond1.length = round(length, 2)

        start = line2.point[0]
        length = 0
        for i in range(1, len(line2.point)):
            length += ESDLGeometry.distance((start.lat, start.lon), (line2.point[i].lat, line2.point[i].lon)) * 1000
            start = line2.point[i]
        new_cond2.length = round(length, 2)

        logger.warning('split-conductor: line1 length={}, line2 length={}'.format(new_cond1.length, new_cond2.length))
        # assign line geometry to the correct conductor
        new_cond1.geometry = line1
        new_cond2.geometry = line2

        # remove conductor from container (area or building) and add new two conductors
        assets = conductor_container.asset
        assets.remove(conductor)
        #pm.remove_object_from_dict(active_es_id, conductor)
        conductor_container.asset.append(new_cond1)
        conductor_container.asset.append(new_cond2)

        # create list of ESDL assets to be added to UI
        esdl_assets_to_be_added = []
        coords1 = []
        for point in line1.point:
            coords1.append([point.lat, point.lon])
        port_list = []
        carrier = None
        if port1.carrier: carrier = port1.carrier
        if port2.carrier: carrier = port2.carrier
        carrier_id = carrier.id if carrier is not None else None
        for p in new_cond1.port:
            p.carrier = carrier
        #     port_list.append(create_port_message(p))
        # state = asset_state_to_ui(new_cond1)
        # tooltip_asset_attrs = get_tooltip_asset_attrs(new_cond1, 'line')
        # add_spatial_attributes(new_cond1, tooltip_asset_attrs)
        # esdl_assets_to_be_added.append(['line', 'asset', new_cond1.name, new_cond1.id, type(new_cond1).__name__,
        #                                 coords1, tooltip_asset_attrs, state, port_list])
        coords2 = []
        for point in line2.point:
            coords2.append([point.lat, point.lon])
        port_list = []

        for p in new_cond2.port:
            p.carrier = carrier
        #     port_list.append(create_port_message(p))
        # state = asset_state_to_ui(new_cond2)
        # tooltip_asset_attrs = get_tooltip_asset_attrs(new_cond2, 'line')
        # add_spatial_attributes(new_cond2, tooltip_asset_attrs)
        # esdl_assets_to_be_added.append(['line', 'asset', new_cond2.name, new_cond2.id, type(new_cond2).__name__,
        #                                 coords2, tooltip_asset_attrs, state, port_list])

        # update asset id's of conductor with new_cond1 and new_cond2 in conn_list
        # for c in conn_list:
        #     if c['from-asset-id'] == conductor_id and c['from-port-id'] == port1.id:
        #         c['from-asset-id'] = new_cond1_id
        #     if c['from-asset-id'] == conductor_id and c['from-port-id'] == port2.id:
        #         c['from-asset-id'] = new_cond2_id
        #     if c['to-asset-id'] == conductor_id and c['to-port-id'] == port1.id:
        #         c['to-asset-id'] = new_cond1_id
        #     if c['to-asset-id'] == conductor_id and c['to-port-id'] == port2.id:
        #         c['to-asset-id'] = new_cond2_id
        #
        # # create list of connections to be added to UI
        # if mode == 'connect':
        #     conn_list.append({'from-port-id': new_port2_id, 'from-port-carrier': carrier_id,
        #                       'from-asset-id': new_cond1_id, 'from-asset-coord': (middle_point.lat, middle_point.lon),
        #                       'to-port-id': new_port1_id, 'to-port-carrier': carrier_id, 'to-asset-id': new_cond2_id,
        #                       'to-asset-coord': (middle_point.lat, middle_point.lon)})

        if mode == 'add_joint':
            joint_id = str(uuid.uuid4())
            joint = esdl.Joint(id=joint_id, name='Joint_'+joint_id[:4])
            inp = esdl.InPort(id=str(uuid.uuid4()), name='In')
            outp = esdl.OutPort(id=str(uuid.uuid4()), name='Out')
            if carrier:
                inp.carrier = carrier
                outp.carrier = carrier

            if type(new_port2).__name__ == "OutPort":
                inp.connectedTo.append(new_port2)
                new_port2_conn_to_id = inp.id
            else:
                outp.connectedTo.append(new_port2)
                new_port2_conn_to_id = outp.id

            if type(new_port1).__name__ == "InPort":
                outp.connectedTo.append(new_port1)
                new_port1_conn_to_id = outp.id
            else:
                inp.connectedTo.append(new_port1)
                new_port1_conn_to_id = inp.id

            joint.port.append(inp)
            joint.port.append(outp)
            joint.geometry = middle_point
            conductor_container.asset.append(joint)
            # pm.add_object_to_dict(active_es_id, joint)
            # pm.add_object_to_dict(active_es_id, inp)
            # pm.add_object_to_dict(active_es_id, outp)

            port_list = []
            for p in joint.port:
                p.carrier = carrier
            #     port_list.append(create_port_message(p))
            # capability_type = ESDLAsset.get_asset_capability_type(joint)
            # state = asset_state_to_ui(joint)
            # tooltip_asset_attrs = get_tooltip_asset_attrs(joint, 'marker')
            # esdl_assets_to_be_added.append(['point', 'asset', joint.name, joint.id, type(joint).__name__,
            #                                 [middle_point.lat, middle_point.lon], tooltip_asset_attrs, state, port_list,
            #                                 capability_type, {}])

            # conn_list.append({'from-port-id': new_port2_id, 'from-port-carrier': carrier_id,
            #                   'from-asset-id': new_cond1_id, 'from-asset-coord': (middle_point.lat, middle_point.lon),
            #                   'to-port-id': new_port2_conn_to_id, 'to-port-carrier': carrier_id,
            #                   'to-asset-id': joint.id, 'to-asset-coord': (middle_point.lat, middle_point.lon)})
            # conn_list.append({'from-port-id': new_port1_conn_to_id, 'from-port-carrier': carrier_id,
            #                   'from-asset-id': joint.id, 'from-asset-coord': (middle_point.lat, middle_point.lon),
            #                   'to-port-id': new_port1_id, 'to-port-carrier': carrier_id,
            #                   'to-asset-id': new_cond2_id, 'to-asset-coord': (middle_point.lat, middle_point.lon)})


if __name__ == '__main__':
    unittest.main()
