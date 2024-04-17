#  This work is based on original code developed and copyrighted by TNO 2023.
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

from collections import UserList
from datetime import datetime
from typing import Optional

from pyecore.commands import Command
from pyecore.ecore import EObject
from pyecore import commands as pyecore_commands

from esdlproject import Variant, HighLevelChange, Add, Set, Delete, Remove
from esdlproject.ChangeSerializer import deepcopy_eobject_change, filterDoubleConnectedTo


class LabelledAction(Command, UserList):
    """
    A list of commands that are executed as one action. The label is used to describe the action.

    Maps to a HighLevelChange in the ESDLProject model.
    """
    def __init__(self, label=None, *commands):
        self.label = label
        super().__init__(commands)

    @property
    def can_execute(self):
        return all(command.can_execute for command in self)

    def execute(self):
        for command in self:
            command.execute()

    @property
    def can_undo(self):
        return all(command.can_undo for command in self)

    def undo(self):
        for command in reversed(self):
            print("undo action:", command)
            command.undo()

    def redo(self):
        for command in self:
            command.redo()

    def unwrap(self):
        return self[0] if len(self) == 1 else self

    def __repr__(self):
        return '{}(label={}: {})'.format(self.__class__.__name__, self.label, self.data)

def convertActionToVariantChanges(action: LabelledAction, variant: Variant):
    """
    Convert an action, retrieved from the tracker stack, to a high level change containing the detailed changes which can be stored and serialized with projects.

    :param action: the action to convert
    :param variant: the variant to store the changes in

    :return: a list of changes
    """
    print(f"Converting LabelledAction {action.label} to changes in variant {variant.name} ({variant.eURIFragment()})")
    hlc = actionToHighlevelChange(action, variant.lastChanged)
    if hlc:
        variant.change.append(hlc)
    variant.lastChanged = datetime.now()


def actionToHighlevelChange(action: LabelledAction, last_changed: datetime = None) -> Optional[HighLevelChange]:
    """
    Convert an action, retrieved from the tracker stack, to a high level change containing the detailed changes which can be stored and serialized with projects.

    :param action: the action to convert
    :param last_changed: time to test if this action is already processed

    :return: a list of changes
    """
    if last_changed is not None and action.created < last_changed:
        print(f"Action  {action.label} already part of changes according to last_changed value, ignoring")
        return None
    print(f"Converting LabelledAction {action.label} )")
    hlc = HighLevelChange(label=action.label, changedAt=datetime.now())  # EDate.from_string("2021-10-27T12:00:00")
    change_list = []

    for command in action:
        command: pyecore_commands.AbstractCommand
        change = None
        print(f"------ Handling {command}")
        if isinstance(command, pyecore_commands.Add):
            if isinstance(command.value, EObject):  # could also be a numeric change or string change
                if command.feature.containment:  # isinstance(command.feature, EReference):
                    # value = command.value.serialized_deepcopy(resource=self.active_resource) #clone()
                    value, x_ref_changes = deepcopy_eobject_change(command.value)
                    # TODO make deepcopy() work
                    change = Add(
                        ownerFragment=command.owner.eURIFragment(),
                        feature=command.feature.name,
                        objectValue=value,
                    )
                    change_list.extend(x_ref_changes)
                else:
                    # this is a x-reference, zo add it to the changeList, to add it as last, otherwise
                    # some x-ref targets might not be available when deserializing
                    try:
                        print(f"convertActionToVariantChanges(): using ref for {command.value} to "
                              f"{command.value.eURIFragment()} ")
                        change = Add(
                            ownerFragment=command.owner.eURIFragment(),
                            feature=command.feature.name,
                            stringValue=command.value.eURIFragment(),
                        )
                        change_list.append(change)
                        change = None
                    except KeyError as e:
                        # TODO: when doing split_conductor, here things go wrong:
                        # this inport can not be found in the port list of its container, which is very strange
                        # but some magic is happening in app.py split_conductor with port reuse, which might
                        # be problematic here.
                        # throwing an error here will at least continue the process (split conductor works,
                        # but changing it into a highlevel change not...
                        print(f"Ewoud fix: KeyError converting ActionToVariantChanges {command}")
            else:
                # TODO add numbers/enums to list
                print(f"TODO Add: convert {command.value} to something")

        # variant.changes.append(change)
        if isinstance(command, pyecore_commands.Set):
            if isinstance(command.value, EObject) or \
                    isinstance(command.previous_value, EObject):  # could also be a numeric change or string change
                if command.feature.containment:
                    value, x_ref_changes = deepcopy_eobject_change(command.value)
                    change = Set(
                        ownerFragment=command.owner.eURIFragment(),
                        feature=command.feature.name,
                        objectValue=value,
                    )
                    change_list.extend(x_ref_changes)
                else:
                    if command.value:
                        print(
                            f"convertActionToVariantChanges(): using ref for {command.value} to {command.value.eURIFragment()} ")
                        refValue = command.valueURIFragment  # command.value.eURIFragment() -> See undo.py:243
                    else:
                        refValue = ""
                    change = Set(
                        ownerFragment=command.owner.eURIFragment(),
                        feature=command.feature.name,
                        stringValue=refValue,
                    )
            else:  # enums / strings / numbers
                previousValue = None
                if command.value is None:
                    stringValue = ""
                else:
                    stringValue = command.feature.eType.to_string(command.value)
                if command.previous_value:
                    previousValue = command.feature.eType.to_string(command.previous_value)
                change = Set(
                    ownerFragment=command.owner.eURIFragment(),
                    feature=command.feature.name,
                    stringValue=stringValue,
                    previousValue=previousValue,
                )

        if isinstance(command, pyecore_commands.Remove):
            if isinstance(command.value, EObject):  # could also be a numeric change or string change
                if command.feature.containment:
                    change = Delete(ownerFragment=command.refURIFragment)  # see undo.py:289
                else:
                    # owner = command.owner.eURIFragment()
                    owner = command.ownerFragment
                    ref = command.refURIFragment
                    change = Remove(
                        ownerFragment=owner,
                        feature=command.feature.name,
                        stringValue=ref,
                    )

        if change:  # in case of x-ref: add it to the changeList instead directly in this list
            hlc.change.append(change)

    if len(change_list) > 0:  # add last, to make sure that x-ref targets are present
        cleanedChangeList = filterDoubleConnectedTo(change_list)
        print(f"------ Adding cross-references of size {len(cleanedChangeList)}, "
            f"(removed {len(change_list) - len(cleanedChangeList)} duplicates)")
        hlc.change.extend(cleanedChangeList)  # add x-references from deepcopy()

    return hlc