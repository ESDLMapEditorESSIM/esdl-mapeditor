import uuid
from datetime import datetime
from typing import List

from pyecore.ecore import EDate, EObject
from pyecore.resources import Resource, ResourceSet, URI

from esdl import EnergySystem
from esdl.esdl_handler import StringURI
from esdl.resources.xmlresource import XMLResource
from esdl.undo import UndoRedoCommandStack, LabelledAction
from esdlproject import HighLevelChange, Variant, Add, Set, EnergySystemProxy
from pyecore import commands as pyecore_commands


class ChangeHandler:
    def __init__(self, resource: Resource):
        self.resource = resource
        # , project:ESDLProject, stack: UndoRedoCommandStack):
        # self.project = project
        # self.stack = stack

    def covertActionToVariantChanges(self, action: LabelledAction, variant: Variant):
        print(f'Converting LabelledAction {action.label} to changes in variant {variant.name} ({variant.eURIFragment()})')
        hlc = HighLevelChange(label=action.label,
                              changedAt=datetime.now())  # EDate.from_string("2021-10-27T12:00:00")
        variant.change.append(hlc)
        for command in action:
            command: pyecore_commands.AbstractCommand
            if isinstance(command, pyecore_commands.Add):
                change = Add(ownerFragment=command.owner.eURIFragment(), feature=command.feature.name, objectValue=command.value)
            # variant.changes.append(change)
            if isinstance(command, pyecore_commands.Set):
                # change = Set(feature=command.feature, value=command.value , oldValue=command.previous_value)
                change = Set(ownerFragment=command.owner.eURIFragment(), feature=command.feature.name, objectValue=command.value)
            hlc.change.append(change)


    # def createSnapshot(self, variant: Variant) -> EnergySystem:
    #     print(f'Creating snapshot for Variant \'{variant.name}\' ({variant.eURIFragment()})')
    #     # TODO add multiple levels of variants here, now it assumes only 1st level
    #     # find closest snapshot and baseVariant (that contains main ES)
    #     es: EnergySystem
    #     if variant.baseVariant:
    #         es = variant.baseVariant.energysystemRef
    #         baseVariant = variant.baseVariant
    #     else:
    #         variant_list: List[Variant] = []
    #         v = variant.parentVariant
    #         while not v.baseVariant:
    #             if v.snapshotRef:
    #                 es = v.snapshotRef
    #                 v = v.parentVariant
    #                 while v.baseVariant is None:
    #                     v = v.parentVariant
    #                 baseVariant = v.baseVariant
    #                 break
    #             else:
    #                 variant_list.append(v.parentVariant)
    #                 v = v.parentVariant
    #         if v.baseVariant:
    #             if v.snapshot:
    #                 es = v.snapshotRef
    #             else:
    #                 es = v.baseVariant.energysystemRef
    #             baseVariant = v.baseVariant
    #         # replay all changes for the list of (parent) variants that have not been replayed yet
    #         for x in variant_list:
    #             snapshot = self.createSnapshot(x)
    #             x.snapshotRef = snapshot
    #
    #     if baseVariant.energysystemRef is not None and len(variant.change) > 0:
    #         es_original_base = baseVariant.energysystemRef.deepcopy()
    #         baseVariant.energysystemRef = es.deepcopy()  # assign snapshot to baseVariant es, as all changes are applied to that ES.
    #
    #         print(f'Using Basevariant {baseVariant.name}, replaying any tracked changes in variant {variant.name} ({variant.eURIFragment()})' )
    #         for highlevelchange in variant.change:
    #             if isinstance(highlevelchange, HighLevelChange):
    #                 print(f'Handling High level change {highlevelchange.label}')
    #                 for change in highlevelchange.change:
    #                     print(f'Processing {change.eClass.name}')
    #                     if isinstance(change, Set):
    #                         if change.objectValue is not None:
    #                             print(f'\- Set change applied to {change.ownerFragment}')
    #                             owner = self.resource.resolve(change.ownerFragment)
    #                             owner.eSet(change.feature, change.objectValue.deepcopy())
    #                         elif change.objectReference:
    #                             # todo
    #                             pass
    #                     elif isinstance(change, Add):
    #                         if change.objectValue is not None:
    #                             print(f'\- Add change applied to {change.ownerFragment}')
    #                             owner = self.resource.resolve(change.ownerFragment)
    #                             abstractList = owner.eGet(change.feature)
    #                             abstractList.append(change.objectValue.deepcopy())
    #                         elif change.objectReference:
    #                             pass  # TODO
    #             else:
    #                 print(f'Fixme: ignoring DetailedChanges at this level')
    #         replayed_es = baseVariant.energysystemRef
    #         variant.snapshotRef = replayed_es.deepcopy()
    #         baseVariant.energysystemRef = es_original_base
    #         print(f'---  Adding snapshot to variant {variant.name} ({variant.eURIFragment()})')
    #         return variant.snapshot

    def createSnapshot2(self, variant: Variant, rset: ResourceSet) -> EnergySystem:
        print(f'Creating snapshot for Variant \'{variant.name}\' ({variant.eURIFragment()})')

        # find closest snapshot and baseVariant (that contains main ES)
        es: EnergySystem
        if variant.energySystemProxy:
            es = variant.energySystemProxy.energysystemRef
            proxy = variant.energySystemProxy
        else:
            variant_list: List[Variant] = []
            v: Variant = variant.parentVariant
            while not v.energySystemProxy:
                if v.snapshotRef:
                    es = v.snapshotRef
                    v = v.parentVariant
                    while v.energySystemProxy is None:
                        v = v.parentVariant
                    proxy = v.energySystemProxy
                    break
                else:
                    variant_list.append(v.parentVariant)
                    v = v.parentVariant
            if v.energySystemProxy:
                if v.snapshotRef:
                    es = v.snapshotRef
                else:
                    es = v.energySystemProxy.energysystemRef
                proxy = v.energySystemProxy
            # replay all changes for the list of (parent) variants that have not been replayed yet
            for x in variant_list:
                snapshot = self.createSnapshot(x)
                x.snapshotRef = snapshot



        if proxy.energysystemRef is not None and len(variant.change) > 0:

            active_es_resource: XMLResource = self.get_or_create_resource(rset, StringURI('active.esdl'))
            new_snapshot_resource: XMLResource = self.get_or_create_resource(rset, self.get_variant_URI(variant))
            base_variant_resource: XMLResource = self.get_or_create_resource(rset, self.get_variant_URI(proxy))



            if len(new_snapshot_resource.contents) != 0:
                print(f'Snapshot already present at {new_snapshot_resource.uri}, returning')
                return new_snapshot_resource.contents[0]

            if len(base_variant_resource.contents) == 0:
                print(f'Creating new base variant (based on current active resource {proxy.energysystemRef.eResource.uri}')
                # no base variant resource yet, copy it from the source
                es_original_base = proxy.energysystemRef.deepcopy()
                es_original_base.name = "Original base"
                base_variant_resource.set_content(es_original_base)


            #baseVariant.energysystemRef = es.deepcopy()  # assign snapshot to baseVariant es, as all changes are applied to that ES.
            resource: XMLResource = proxy.energysystemRef.eResource
            print(f'Assigning base variant / snapshot as active ES: {resource.uri}')
            if es is not None:
                resource.set_content(es.deepcopy())
                resource.contents[0].name = "Active ES = " + es.name
            else:
                resource.set_content(base_variant_resource.contents[0].deepcopy())
                resource.contents[0].name = "Active ES = " + base_variant_resource.contents[0].name
            proxy.energysystemRef = resource.contents[0]

            print(f'Using Basevariant {proxy.name}({proxy.energysystemRef.eResource.uri}), replaying any tracked changes in variant {variant.name} ({variant.eURIFragment()})' )
            for highlevelchange in variant.change:
                if isinstance(highlevelchange, HighLevelChange):
                    print(f'Handling High level change {highlevelchange.label}')
                    for change in highlevelchange.change:
                        self.processChange(change, resource)

                else:
                    print(f'Fixme: ignoring DetailedChanges at this level')
            replayed_es = resource.contents[0]
            replayed_es.name = replayed_es.name + " with changes from " + variant.name
            print(f'Assigning generated ES to {new_snapshot_resource.uri}')
            new_snapshot_resource.set_content(replayed_es)
            new_snapshot_resource.contents[0].name = new_snapshot_resource.contents[0].name + ", snapshot for " + variant.name
            variant.snapshotRef = new_snapshot_resource.contents[0]
            print(f'Reset active es to base variant again')
            active_es_resource.set_content(base_variant_resource.contents[0])
            base_variant_resource.contents[0].name = base_variant_resource.contents[0].name + " reset to base variant"
            proxy.energysystemRef = base_variant_resource.contents[0]
            print(f'---  Adding snapshot to variant {variant.name} ({variant.eURIFragment()})')
            return variant.snapshotRef

    def processChange(self, change, resource):
        print(f'Processing {change.eClass.name}')
        if isinstance(change, Set):
            if change.objectValue is not None:
                print(f'\- Set change applied to {change.ownerFragment}')
                owner = resource.resolve(change.ownerFragment)
                owner.eSet(change.feature, change.objectValue.deepcopy())
            elif change.objectReference:
                # todo
                pass
        elif isinstance(change, Add):
            if change.objectValue is not None:
                print(f'\- Add change applied to {change.ownerFragment}')
                owner = resource.resolve(change.ownerFragment)
                abstractList = owner.eGet(change.feature)
                abstractList.append(change.objectValue.deepcopy())
            elif change.objectReference:
                pass  # TODO

    def get_variant_URI(self, v: Variant):
        if isinstance(v, EnergySystemProxy):
            return StringURI(f'base_{v.name.replace(" ", "_")}.esdl')
        return StringURI(f'{v.name.replace(" ", "_")}.esdl')

    def get_or_create_resource(self, rset: ResourceSet, uri: URI):
        if uri.normalize() in rset.resources:
            return rset.resources[uri.normalize()]
        return rset.create_resource(uri)


    def eobject_tree_to_string(self, eobject: EObject):
        print(f'Converting to string: {eobject.name if hasattr(eobject, "name") else eobject.eClass.name}')
        deepcopy = eobject.deepcopy()
        string_uri = StringURI(f'variant1_output_shapshot-{uuid.uuid4()}.esdl')
        resource = XMLResource(string_uri)
        resource.append(deepcopy)
        resource.save()
        return string_uri.getvalue()