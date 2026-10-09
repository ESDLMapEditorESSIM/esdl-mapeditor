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
import logging
from datetime import datetime
from typing import List
from weakref import WeakKeyDictionary

from esdlproject import Variant, DetailedChange, AbstractChange, HighLevelChange

logger = logging.getLogger(__name__)

class ConflictResolution:
    """
    Represents a merge conflict between two changes.
    If original_uri is present in a change, it should be replaced with merged_uri.
    This is used to indicate that two changes cannot be applied together, because they modify the same resource
    in conflicting ways.
    """
    def __init__(self, original_uri: str, merged_uri: str, apply_from: datetime):
        self.original_uri = original_uri
        self.merged_uri = merged_uri
        self.apply_from = apply_from
        self.apply_till: datetime | None = None

    def __repr__(self):
        return f"MergeConflict(original_uri={self.original_uri} --> merged_uri={self.merged_uri})"


class MergeConflictHandler:
    """
    Handles merge conflicts by keeping track of conflicts in Variants and their resolution.
    """
    def __init__(self):
        """
        Variant -> DetailedChange -> MergeConflict
        """
        #self.resolutions: WeakKeyDictionary[Variant, WeakKeyDictionary[DetailedChange, ConflictResolution]] = WeakKeyDictionary()
        self.resolutions: dict[Variant, WeakKeyDictionary[DetailedChange, list[ConflictResolution]]] = dict()


    def add_resolution(self, variant:Variant, change: DetailedChange, resolution: ConflictResolution):
        if variant not in self.resolutions:
            #self.resolutions[variant]: WeakKeyDictionary[DetailedChange, ConflictResolution] = WeakKeyDictionary()
            self.resolutions[variant]: dict[DetailedChange, list[ConflictResolution]] = dict()
        logger.debug("Adding resolution for change: variant=%s, change=%s, resolution=%s", variant, change, resolution)
        #if change in self.resolutions[variant]:
        #    logger.warning("Resolution already exists for change", change=change)
        if change not in self.resolutions[variant]:
            self.resolutions[variant][change] = list()
        self.resolutions[variant][change].append(resolution)

    def get_resolution(self, variant) -> WeakKeyDictionary[DetailedChange, ConflictResolution] | None:
        return self.resolutions.get(variant, None)

    def get_resolutions_for_change(self, variant:Variant, change:DetailedChange) -> List[ConflictResolution] | None:
        if self.resolutions.get(variant, None):
            return self.resolutions[variant].get(change, None)
        return None

    def clear_resolutions(self, variant: Variant):
        if variant in self.resolutions:
            del self.resolutions[variant]

    def clear(self):
        """
        Clears all conflicts.
        """
        self.resolutions.clear()

    # def update_change(self, variant: Variant, change: DetailedChange, apply_from: datetime = None) -> DetailedChange:
    #     """
    #     Updates a change by replacing the original URI with the merged URI, if needed.
    #     """
    #     variant_conflict_dict = self.get_conflicts(variant)
    #     resolution = self.get_resolution_for_change(variant, change)
    #     if resolution:
    #         new_change = change.deepcopy()
    #         update_change_uri_fragment(new_change, resolution.original_uri, resolution.merged_uri)
    #         return new_change
    #     else:
    #         # No resolution found, return the original change
    #         return change

    def apply(self, variant: Variant, change: DetailedChange, conflict_resolutions: ConflictResolution | List[ConflictResolution]) -> DetailedChange:
        """
        Applies the conflict resolution to a change by updating its URI fragment.
        And deletes the change from the resolution list if it exists.
        Parameters
        ----------
        variant
        change
        conflict_resolutions

        Returns
        -------

        """
        # if a change is merged, it should be removed from the resolution list, as it has been handled
        # and should not be reused when replaying the changes of a variant in future
        if self.resolutions.get(variant, None) and change in self.resolutions[variant]:
            del self.resolutions[variant][change]
        new_change = change.deepcopy()
        logger.debug(" \\- Applying conflict resolution for change: %s, merge_conflict=%s", change, conflict_resolutions)
        if isinstance(conflict_resolutions, List):
            # reverse the list to make sure asset.0 -> asset.1 and asset.2 -> asset.3 are not updated to
            # asset.0 -> asset.3 as that is wrong. If we reverse it, the individual resolutions are applied correctly.
            for conflict_res in reversed(conflict_resolutions):
                update_change_uri_fragment(new_change, conflict_res.original_uri, conflict_res.merged_uri)
        else:
            conflict_res = conflict_resolutions
            update_change_uri_fragment(new_change, conflict_res.original_uri, conflict_res.merged_uri)
        return new_change

    def is_affected(self, change: DetailedChange, resolution: ConflictResolution) -> bool:
        """
        Checks if the change is affected by the resolution.
        A change is affected if its objectFragment or ownerFragment starts with the original URI of the resolution.
        """
        if change.objectFragment and change.objectFragment.startswith(resolution.original_uri):
            return True
        if change.ownerFragment and change.ownerFragment.startswith(resolution.original_uri):
            return True
        for obj_xref in change.objectValue_xrefs:
            affected_obj_xref = self.is_affected(obj_xref, resolution)
            if affected_obj_xref:  # return immediately if affected xref is found
                return affected_obj_xref
        for pref_xref in change.previousValue_xrefs:
            affected_pref_xref = self.is_affected(pref_xref, resolution)
            if affected_pref_xref:
                return affected_pref_xref
        return False



    def update_future_changes(self, target_variant: Variant, change: DetailedChange, change_container: HighLevelChange, resolution: ConflictResolution):
        """
        Updates all future changes in the variant that reference the original URI to use the merged URI.
        """
        # update future changes in variant of the current change
        variant = get_variant(change_container)
        start_change = None
        for c in variant.change:
            if get_high_level_change(c).changedAt >= get_high_level_change(change, change_container).changedAt:
                start_change = c
                break
        if start_change:
            start_index = variant.change.index(start_change)

            for i in range(start_index, len(variant.change)):
                next_change = variant.change[i]  # this should be a HighLevelChange
                if isinstance(next_change, DetailedChange):
                    if self.is_affected(next_change, resolution):
                        # indicate that this change is affected by the resolution
                        self.add_resolution(target_variant, next_change, resolution)
                        if next_change.objectValue_xrefs:
                            for obj_xref in next_change.objectValue_xrefs:
                                if self.is_affected(obj_xref, resolution):
                                    self.add_resolution(target_variant, obj_xref, resolution)
                        if next_change.previousValue_xrefs:
                            for obj_xref in next_change.previousValue_xrefs:
                                if self.is_affected(obj_xref, resolution):
                                    self.add_resolution(target_variant, obj_xref, resolution)
                elif isinstance(next_change, HighLevelChange):
                    for detailed_change in next_change.change:
                        # indicate that this change is affected by the resolution
                        self.add_resolution(target_variant, detailed_change, resolution)
                        if detailed_change.objectValue_xrefs:
                            for obj_xref in detailed_change.objectValue_xrefs:
                                if self.is_affected(obj_xref, resolution):
                                    self.add_resolution(target_variant, obj_xref, resolution)
                        if detailed_change.previousValue_xrefs:
                            for obj_xref in detailed_change.previousValue_xrefs:
                                if self.is_affected(obj_xref, resolution):
                                    self.add_resolution(target_variant, obj_xref, resolution)

        # update changes in the target variant to which the change is applied
        start_change = None
        for c in target_variant.change:
            if get_high_level_change(c).changedAt >= get_high_level_change(change, change_container).changedAt:
                start_change = c
                break
        if start_change:
            start_index = target_variant.change.index(start_change)

            for i in range(start_index, len(target_variant.change)):
                next_change = target_variant.change[i]  # this should be a HighLevelChange
                if isinstance(next_change, DetailedChange):
                    if self.is_affected(next_change, resolution):
                        # indicate that this change is affected by the resolution
                        self.add_resolution(target_variant, next_change, resolution)
                        if next_change.objectValue_xrefs:
                            for obj_xref in next_change.objectValue_xrefs:
                                if self.is_affected(obj_xref, resolution):
                                    self.add_resolution(target_variant, obj_xref, resolution)
                        if next_change.previousValue_xrefs:
                            for obj_xref in next_change.previousValue_xrefs:
                                if self.is_affected(obj_xref, resolution):
                                    self.add_resolution(target_variant, obj_xref, resolution)
                elif isinstance(next_change, HighLevelChange):
                    for detailed_change in next_change.change:
                        # indicate that this change is affected by the resolution
                        self.add_resolution(target_variant, detailed_change, resolution)
                        if detailed_change.objectValue_xrefs:
                            for obj_xref in detailed_change.objectValue_xrefs:
                                if self.is_affected(obj_xref, resolution):
                                    self.add_resolution(target_variant, obj_xref, resolution)
                        if detailed_change.previousValue_xrefs:
                            for obj_xref in detailed_change.previousValue_xrefs:
                                if self.is_affected(obj_xref, resolution):
                                    self.add_resolution(target_variant, obj_xref, resolution)

########################################################################
# public functions
########################################################################

def get_variant(change: AbstractChange) -> Variant:
    """
    Get the variant of a HighLevelChange or DetailedChange object.

    :param change: The change object to get the variant from.
    :return: The variant object
    """
    if change.variant is not None:
        retval = change.variant
        return retval
    else:
        return get_variant(change.eContainer())

def get_high_level_change(change: DetailedChange, change_container: HighLevelChange=None) -> HighLevelChange:
    """
    Get the HighLevelChange of a DetailedChange object.

    :param change: The DetailedChange object to get the HighLevelChange from.
    :param: change_container: In case change is deepcopy'd for a mitigation, the change.eContainer() does not work.
    :return: The HighLevelChange object
    """
    if isinstance(change, HighLevelChange):
        return change
    elif change_container is not None and isinstance(change_container, HighLevelChange):
        return change_container
    elif change.eContainer() is not None and isinstance(change.eContainer(), HighLevelChange):
        return change.eContainer()
    else:
        raise ValueError("The change is not part of a HighLevelChange.")

def update_fragment_list_index(fragment:str, index: int) -> str:
    """Updates the index of a fragment. e.g. /@asset.1 --> /@asset.2 if index = 2"""
    return fragment.rpartition(".")[0] + "." + str(index)

def substitute_fragment(input_fragment: str, old_fragment:str, new_fragment:str) -> str:
    """
    Substitutes the input fragment by replacing the old fragment_uri to the new fragment_uri. E.g.:
    input = '//@instance.0/@area/@area.0/@area.7/@asset.387/@port.0/@profile.0/@profileQuantityAndUnit'
    old = //@instance.0/@area/@area.0/@area.7/@asset.387
    new = //@instance.0/@area/@area.0/@area.7/@asset.388
    rewritten = '//@instance.0/@area/@area.0/@area.7/@asset.388/@port.0/@profile.0/@profileQuantityAndUnit'
    """
    return new_fragment + input_fragment.partition(old_fragment)[2]


def update_change_uri_fragment(change: DetailedChange, old_uri_fragment: str, new_uri_fragment: str):
    """
    Update the URI fragment of a change object inplace.

    :param change: The change object to update.
    :param old_uri_fragment: The old URI fragment to replace.
    :param new_uri_fragment: The new URI fragment to set.
    """

    logger.debug(f" \\- Updating change URI fragment: {change}, old={old_uri_fragment}, new={new_uri_fragment}")
    if change.objectFragment and change.objectFragment.startswith(old_uri_fragment):
        updated_uri = substitute_fragment(change.objectFragment, old_uri_fragment, new_uri_fragment)
        change.objectFragment = updated_uri
    if change.ownerFragment and change.ownerFragment.startswith(old_uri_fragment):
        change.ownerFragment = substitute_fragment(change.ownerFragment, old_uri_fragment, new_uri_fragment)
    for obj_xref in change.objectValue_xrefs:
        update_change_uri_fragment(obj_xref, old_uri_fragment, new_uri_fragment)
    for pref_xref in change.previousValue_xrefs:
        update_change_uri_fragment(pref_xref, old_uri_fragment, new_uri_fragment)


