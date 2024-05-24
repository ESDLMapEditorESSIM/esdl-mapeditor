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
from pyecore.ecore import EStructuralFeature, EAttribute, EObject, EClass, EReference

from esdl.resources.xmlresource import XMLResource
from esdlproject import Set, Add, Remove, Delete


def applyChange(change, resource: XMLResource):
    """
    Process a change and apply it to the given resource.

    :param change: the change to apply
    :param resource: the resource to apply the change to
    """
    print(
        f"Processing {change.eClass.name}, owner={change.ownerFragment}, feature={change.feature} applying it to {resource.uri}"
    )
    if isinstance(change, Set):
        if change.objectValue is not None:
            print(f"\- Set change applied to {change.ownerFragment}")
            owner = resource.resolve(change.ownerFragment)
            owner.eSet(change.feature, change.objectValue.deepcopy())
        elif change.stringValue is not None:
            owner = resource.resolve(change.ownerFragment)
            feature: EStructuralFeature = owner.eClass.findEStructuralFeature(change.feature)
            if isinstance(feature, EAttribute):
                owner.eSet(change.feature, feature.eType.from_string(change.stringValue))
            else:  # eReference and not many
                if change.stringValue == "":
                    owner.eSet(change.feature, None)
                else:
                    target = resource.resolve(change.stringValue)
                    owner.eSet(change.feature, target)

    elif isinstance(change, Add):
        if change.objectValue is not None:
            print(f"\- Add change applied to {change.ownerFragment} using objectValue")
            owner = resource.resolve(change.ownerFragment)
            abstractList = owner.eGet(change.feature)
            abstractList.append(change.objectValue.deepcopy())
        elif change.objectFragment:
            print(f"\- Add change applied to {change.ownerFragment} using objectFragment")
            owner = resource.resolve(change.ownerFragment)
            abstractList = owner.eGet(change.feature)
            target_reference = resource.resolve(change.objectFragment)
            abstractList.append(target_reference)
        elif change.stringValue:
            print(f"\- Add change applied to {change.ownerFragment} using stringValue")
            owner: EObject = resource.resolve(change.ownerFragment)
            abstractList = owner.eGet(change.feature)
            eClass: EClass = owner.eClass
            feature: EStructuralFeature = eClass.findEStructuralFeature(change.feature)
            if isinstance(feature, EReference):
                eReference: EReference = feature
                if eReference.containment:
                    print("processChange(): Not handled reference.containment")
                else:
                    print(f"\- Add change reference {change.stringValue} applied to {change.ownerFragment}")
                    ref = resource.resolve(change.stringValue)
                    abstractList.append(ref)
            else:
                print(f"\- Add change attribute value {change.stringValue} applied to {change.ownerFragment}")
                abstractList.append(change.stringValue)
    elif isinstance(change, Remove):
        # remove a value or reference from a list
        try:
            owner: EObject = resource.resolve(change.ownerFragment)
        except ValueError:
            print(f"\- ###: Cannot execute change, resolving of {change.ownerFragment} failed")
            return
        feature: EStructuralFeature = owner.eClass.findEStructuralFeature(change.feature)
        abstractList = owner.eGet(change.feature)
        if isinstance(feature, EReference):
            try:
                ref = resource.resolve(change.stringValue)
                abstractList.remove(ref)
            except Exception:
                print(f"\- ###: Cannot execute change, resolving of {change.stringValue} failed")
        else:
            # stringvalue is a value (enum, string, int, etc)
            abstractList.remove(feature.eType.from_string(change.stringValue))
    elif isinstance(change, Delete):
        obj: EObject = resource.resolve(change.objectFragment)
        obj.delete()


def undoChange(change, resource: XMLResource):
    """
    Undo the change to the given resource.
    So Add -> Remove
    Remove -> Add
    Set -> UnSet to previous value
    Delete -> ReAdd

    :param change: the change to apply
    :param resource: the resource to apply the change to
    """

    print(
        f"Undo - Processing {change.eClass.name}, owner={change.ownerFragment}, feature={change.feature} applying it to {resource.uri}"
    )
    if isinstance(change, Set):
        if change.previousValue is not None and isinstance(change.previousValue, EObject):
            print(f"\- Undo Set change applied to {change.ownerFragment}")
            owner = resource.resolve(change.ownerFragment)
            #owner.eSet(change.feature, change.objectValue.deepcopy())
            owner.eSet(change.feature, change.previousValue.deepcopy())
        elif change.objectFragment or change.stringValue:
            owner = resource.resolve(change.ownerFragment)
            feature: EStructuralFeature = owner.eClass.findEStructuralFeature(change.feature)
            if isinstance(feature, EAttribute):
                #owner.eSet(change.feature, feature.eType.from_string(change.stringValue))
                owner.eSet(change.feature, feature.eType.from_string(change.previousValue))
            else:  # eReference and not many
                if change.previousValue == "" or change.previousValue is None:
                    owner.eSet(change.feature, None)
                else:
                    target = resource.resolve(change.previousValue)
                    owner.eSet(change.feature, target)
        else:
            print("Set: NOT HANDLED ", change)

    elif isinstance(change, Add):
        # undo this Add
        if change.objectValue is not None:
            print(f"\- Add change applied to {change.ownerFragment}")
            owner = resource.resolve(change.ownerFragment)
            abstractList = owner.eGet(change.feature)
            #abstractList.remove(change.objectValue)
            current_value = resource.resolve(change.objectFragment)
            abstractList.remove(current_value)
        elif change.objectFragment:
            owner = resource.resolve(change.ownerFragment)
            abstractList = owner.eGet(change.feature)
            current_value = resource.resolve(change.objectFragment)
            abstractList.remove(current_value)
        elif change.stringValue:
            owner: EObject = resource.resolve(change.ownerFragment)
            abstractList = owner.eGet(change.feature)
            eClass: EClass = owner.eClass
            feature: EStructuralFeature = eClass.findEStructuralFeature(change.feature)
            if isinstance(feature, EReference):
                eReference: EReference = feature
                if eReference.containment:
                    print("processChange(): Not handled reference.containment")
                else:
                    print(f"\- Add change reference {change.stringValue} applied to {change.ownerFragment}")
                    ref = resource.resolve(change.stringValue)
                    abstractList.remove(ref)
            else:
                print(f"\- Add change attribute value {change.stringValue} applied to {change.ownerFragment}")
                abstractList.remove(change.stringValue)
    elif isinstance(change, Remove):
        # remove a value or reference from a list
        try:
            owner: EObject = resource.resolve(change.ownerFragment)
        except ValueError:
            print(f"\- ###: Cannot execute change, resolving of {change.ownerFragment} failed")
            return
        feature: EStructuralFeature = owner.eClass.findEStructuralFeature(change.feature)
        abstractList = owner.eGet(change.feature)
        if isinstance(feature, EReference):
            try:
                ref = resource.resolve(change.objectFragment)
                abstractList.append(ref)
            except Exception:
                print(f"\- ###: Cannot execute change, resolving of {change.objectFragment} failed")
        else:
            # stringvalue is a value (enum, string, int, etc)
            abstractList.append(feature.eType.from_string(change.stringValue))
    elif isinstance(change, Delete):
        # undelete
        # todo: add context information of this delete so we can undo this
        #urivalue: EObject = resource.resolve(change.objectFragment)
        owner: EObject = resource.resolve(change.ownerFragment)
        feature: EStructuralFeature = owner.eClass.findEStructuralFeature(change.feature)
        # delete of object, so feature could be containment and many
        if isinstance(feature, EReference):
            feature: EReference
            if feature.many:
                abstractList = owner.eGet(feature)
                abstractList.append(change.objectValue.deepcopy())
                # todo handle added x-refs
            else:
                owner.eSet(feature, change.objectValue.deepcopy())
        else:
            print("Undo Delete: no reference feature but attribute...")