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
from pyecore.valuecontainer import ECollection

from esdl.resources.xmlresource import XMLResource
from esdlproject import Set, Add, Remove, Delete, Variant, DetailedChange
from esdlproject.MergeConflictHandler import MergeConflictHandler, ConflictResolution, get_variant, \
    update_fragment_list_index
from src.log import get_logger

logger = get_logger(__name__)

"""
Implements undo and redo based on a change.

Applies a change or undos a change to a specific resource
"""

def applyChange(change: DetailedChange, resource: XMLResource, target_variant: Variant,
                merge_conflict_handler: MergeConflictHandler = None):
    """
    Process a change and apply it to the given resource.

    :param change: the change to apply
    :param resource: the resource to apply the change to
    :param target_variant: used to check for merge conflicts and analyse changes that are not in the same variant as the change
    """
    # logger.debug(
    #     f"Processing {change.eClass.name}, owner={change.ownerFragment}, feature={change.feature}, objectFragment={change.objectFragment} applying it to {resource.uri}"
    # )

    # check if there are conflict resolutions for this change, if so, apply them first
    if merge_conflict_handler:
        conflict_resolution = merge_conflict_handler.get_resolution_for_change(target_variant, change)
        if conflict_resolution:
            logger.debug(f" \\- Found conflict resolution for {change} in {target_variant.name}: {conflict_resolution}")
            change = merge_conflict_handler.apply(target_variant, change, conflict_resolution)

    if isinstance(change, Set):
        if change.objectValue is not None:
            #print(f"\\- Set change applied to {change.ownerFragment}")
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
                    # todo, this case is handled with objectFragment nowadays instead of stringValue...
                    target = resource.resolve(change.stringValue)
                    owner.eSet(change.feature, target)
        elif change.objectFragment is not None:
            owner = resource.resolve(change.ownerFragment)
            #feature: EStructuralFeature = owner.eClass.findEStructuralFeature(change.feature)
            target = resource.resolve(change.objectFragment)
            owner.eSet(change.feature, target)
        elif change.ownerFragment and change.previousObjectValue and not change.objectValue:
            # unset of attribute to None
            owner = resource.resolve(change.ownerFragment)
            owner.eSet(change.feature, change.objectValue)  # set to None
        else:
            logger.warning(f"Missing case for SET {change}")

    elif isinstance(change, Add):
        if change.objectValue is not None:
            #print(f"\\- Add change applied to {change.ownerFragment} using objectValue")
            owner = resource.resolve(change.ownerFragment)
            abstractList = owner.eGet(change.feature)
            if change.objectFragment:
                try:
                    # check if there is already an object at that index in the list. If so, there is a potential merge conflict
                    target = resource.resolve(change.objectFragment)
                    # or this object had to be inserted at this index, or it is a conflict by merging two variants
                    # check if the target is from the same variant, if so, it should be inserted (and rewrite change list)
                    # if not, it is a merge conflict and we have to rewrite the objectFragment in the rest of the changes
                    # in the change list from the variant that this change belongs to
                    logger.info(f"Merge conflict when applying {change} to {change.objectFragment}, target exists: {target}")
                    source_variant = get_variant(change)
                    if source_variant.id != target_variant.id:
                        # this change is from a different variant, so we have to rewrite the fragment of the object
                        # in the change list of the source variant to match the index at which this object is added
                        # to the list
                        index = len(abstractList)
                        abstractList.append(change.objectValue.deepcopy())
                        new_fragment = update_fragment_list_index(change.objectFragment, index)
                        logger.info(f"  \\- Rewriting objectFragment {change.objectFragment} to {new_fragment}, new index={index}")
                        resolution = ConflictResolution(change.objectFragment, new_fragment, change.changedAt)
                        #merge_conflict_handler.add_resolution(target_variant, change, resolution)
                        # look for changes in the changelog that have the same uri fragment as this change
                        merge_conflict_handler.update_future_changes(target_variant, change, resolution)
                        #-- make sure to also handle the xrefs of this change. WARING: this rewrites the change to a new one
                        change = merge_conflict_handler.apply(target_variant, change, resolution)
                        # update_change_uri_fragment(change, change.objectFragment, new_fragment)
                    else:
                        index = int(change.objectFragment.rfind('.'))
                        logger.debug(
                            f"  \\- Adding objectValue {change.objectValue} to {change.ownerFragment}/{change.feature} at index {index}")
                        abstractList.insert(index, change.objectValue.deepcopy())

                except (IndexError, ValueError) as e:
                    # can't resolve the objectFragment, so we can just append it
                    abstractList.append(change.objectValue.deepcopy())
                    #raise e
            else:
                # no objectFragment, so just append the objectValue to the list
                logger.debug(f"  \\- Adding objectValue {change.objectValue} to {change.ownerFragment}/{change.feature}")
                abstractList.append(change.objectValue.deepcopy())

        elif change.objectFragment:
            #print(f"\\- Add change applied to {change.ownerFragment} using objectFragment {change.objectFragment}")
            owner = resource.resolve(change.ownerFragment)
            abstractList = owner.eGet(change.feature)
            target_reference = resource.resolve(change.objectFragment)
            abstractList.append(target_reference)
        elif change.stringValue:
            #print(f"\\- Add change applied to {change.ownerFragment} using stringValue")
            owner: EObject = resource.resolve(change.ownerFragment)
            abstractList = owner.eGet(change.feature)
            eClass: EClass = owner.eClass
            feature: EStructuralFeature = eClass.findEStructuralFeature(change.feature)
            if isinstance(feature, EReference):
                eReference: EReference = feature
                if eReference.containment:
                    logger.warning(f"  \\- processChange(): Not handled reference.containment for {change}")
                else:
                    #print(f"  \\- Add reference {change.stringValue} applied to {change.ownerFragment}")
                    ref = resource.resolve(change.stringValue)
                    abstractList.append(ref)
            else:
                #print(f"   \\- Add change attribute value {change.stringValue} applied to {change.ownerFragment}")
                abstractList.append(change.stringValue)
    elif isinstance(change, Remove):
        # remove a value or reference from a list
        try:
            owner: EObject = resource.resolve(change.ownerFragment)
        except ValueError as e:
            logger.error(f"\\- ###: Cannot execute change, resolving of {change.ownerFragment} failed: {e}")
            return
        feature: EStructuralFeature = owner.eClass.findEStructuralFeature(change.feature)
        abstractList = owner.eGet(change.feature)
        if isinstance(feature, EReference):
            try:
                ref = resource.resolve(change.objectFragment)
                abstractList.remove(ref)
            except Exception as e:
                logger.error(f"\\- ###: Cannot execute change, resolving of {change.objectFragment} failed: {e}")
        else:
            # stringvalue is a value (enum, string, int, etc)
            abstractList.remove(feature.eType.from_string(change.stringValue))
    elif isinstance(change, Delete):
        try:
            obj: EObject = resource.resolve(change.objectFragment)
            obj.delete()
        except Exception as e:
            logger.error(f"\\- ###: Cannot execute change, resolving of {change.objectFragment} failed: {e}")

    if len(change.objectValue_xrefs) > 0:
        for ref_change in change.objectValue_xrefs:
            #print("\\- Undo: Applying x-ref ", ref_change)
            applyChange(ref_change, resource, target_variant, merge_conflict_handler)  # recreate cross-references


def undoChange(change, resource: XMLResource, target_variant: Variant, merge_conflict_handler: MergeConflictHandler = None):
    """
    Undo the change to the given resource.
    So Add -> Remove
    Remove -> Add
    Set -> UnSet to previous value
    Delete -> ReAdd

    :param change: the change to apply
    :param resource: the resource to apply the change to
    :param target_variant: used to check for merge conflicts and analyse changes that are not in the same variant as the change
    """



    # apply objectValue_xrefs first, as this might be references to object that get removed
    if len(change.objectValue_xrefs) > 0:
        for xref_change in change.objectValue_xrefs:
            undoChange(xref_change, resource, target_variant, merge_conflict_handler)

    logger.debug(
        f"Undo - Processing {change.eClass.name}, owner={change.ownerFragment}, feature={change.feature} applying it to {resource.uri}"
    )

    if isinstance(change, Set):
        if change.previousObjectValue is not None and isinstance(change.previousObjectValue, EObject):
            #print(f"\\- Undo Set change applied to {change.ownerFragment}")
            owner = resource.resolve(change.ownerFragment)
            owner.eSet(change.feature, change.previousObjectValue.deepcopy())
        # elif change.previousValue is not None and isinstance(change.previousValue, str):
        #     print(f"\- Undo Set reference change applied to {change.ownerFragment}")
        #     # originally an unset, so when undoing, we need to set it to previous_value as reference
        #     owner = resource.resolve(change.ownerFragment)
        #     feature: EStructuralFeature = owner.eClass.findEStructuralFeature(change.feature)
        #     if isinstance(feature, EReference) and not feature.containment:
        #         target = target = resource.resolve(change.previousValue)
        #         owner.eSet(change.feature, target)

        elif change.objectFragment or change.stringValue or change.previousValue:
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
            logger.warning(f"Undo Set: NOT HANDLED {change}")

    elif isinstance(change, Add):
        # undo this Add
        if change.objectValue is not None:
            #print(f"\\- Undo Add change applied to {change.ownerFragment}")
            owner = resource.resolve(change.ownerFragment)
            abstractList = owner.eGet(change.feature)
            #abstractList.remove(change.objectValue)
            current_value = resource.resolve(change.objectFragment)
            abstractList.remove(current_value)
        elif change.objectFragment:
            owner = resource.resolve(change.ownerFragment)
            abstractList = owner.eGet(change.feature)
            current_value = resource.resolve(change.objectFragment)
            try:
                logger.debug(f'Removing {current_value} from {owner.eClass.name}.{change.feature}')
                abstractList.remove(current_value)
            except KeyError as e:
                logger.error("Can't delete from list")
                #breakpoint()
        elif change.stringValue:
            owner: EObject = resource.resolve(change.ownerFragment)
            abstractList = owner.eGet(change.feature)
            eClass: EClass = owner.eClass
            feature: EStructuralFeature = eClass.findEStructuralFeature(change.feature)
            if isinstance(feature, EReference):
                eReference: EReference = feature
                if eReference.containment:
                    logger.warning("\\- Undo processChange(): Not handled reference.containment")
                else:
                    #print(f"\\- Undo Add change reference {change.stringValue} applied to {change.ownerFragment}")
                    ref = resource.resolve(change.stringValue)
                    abstractList.remove(ref)
            else:
                #print(f"\\- Undo Add change attribute value {change.stringValue} applied to {change.ownerFragment}")
                abstractList.remove(change.stringValue)
    elif isinstance(change, Remove):
        # remove a value or reference from a list
        try:
            owner: EObject = resource.resolve(change.ownerFragment)
        except ValueError:
            logger.error(f"\\- ###: Undo Cannot execute change, resolving of {change.ownerFragment} failed")
            return
        feature: EStructuralFeature = owner.eClass.findEStructuralFeature(change.feature)
        abstractList = owner.eGet(change.feature)
        if isinstance(feature, EReference):
            try:
                ref = resource.resolve(change.objectFragment)
                abstractList.append(ref)
            except Exception:
                logger.error(f"\\- ###: Undo Cannot execute change, resolving of {change.objectFragment} failed")
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
                abstractList: ECollection = owner.eGet(feature)
                index_loc = change.objectFragment.rfind('.')  # find index in collection
                if index_loc > 0:
                    index = int(change.objectFragment[change.objectFragment.rfind('.')+1:])
                    #print("\\ - Found index! ", index)
                    abstractList.insert(index, change.objectValue.deepcopy())
                else:
                    abstractList.append(change.objectValue.deepcopy())
                # todo handle added x-refs
            else:
                owner.eSet(feature, change.objectValue.deepcopy())
        else:
            logger.warning("\\- Undo Delete: no reference feature but attribute...")

    if len(change.previousValue_xrefs) > 0:
        for ref_change in change.previousValue_xrefs:
            #print("\\- Undo: Applying prev x-ref ", ref_change)
            applyChange(ref_change, resource, target_variant)  # recreate cross-references


