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
from typing import List, Tuple

from pyecore.commands import AbstractCommand
from pyecore.ecore import EObject, EStructuralFeature, EClass, EReference
from pyecore.resources import Resource
from pyecore.valuecontainer import ECollection
from src.log import get_logger

logger = get_logger(__name__)

class AddCrossReference(AbstractCommand):
    """
    For cross references, the value itself is not relevant, only the location in the tree (eURIFragment,
    such as /instance.0/area/asset.0/port.0
    """
    def __init__(self, owner: EObject, feature: EStructuralFeature, value: EObject, index=None):
        super().__init__(owner, feature, value)  # fake value as we do not use it
        self.index = index
        if value is not None:
            self.valueURIFragment = value.eURIFragment()
        self.ownerURIFragment = owner.eURIFragment()
        self._collection = self.resource.resolve(self.ownerURIFragment).eGet(self.feature)
        if not self.index and self.value:
            self.index = self._collection.index(self.value)
        self._executed = True

    @property
    def can_execute(self):
        executable = super().can_execute
        executable = executable and self.value is not None
        # Cannot use original owners collection, as in a deepcopy we don't know the resource the original belongs to
        # we need to resolve here the uri fragments in the target resource where this Add is executed upon.
        # but we don't have this resource here (it assumes the resource of the original owner...)
        #self._collection = self.owner.eGet(self.feature)
        # so the collection below is the original collection before deepcopy
        self._collection = self.resource.resolve(self.ownerURIFragment).eGet(self.feature)

        return executable

    @property
    def can_undo(self):
        can = super().can_undo
        value = self.resource.resolve(self.valueURIFragment)
        #return can and self.value in self._collection  #  this value is not in the collection as it is a deepcopy
        return can #and value in self._collection  #  this value is not in the collection as it is a deepcopy

    def undo(self):
        self._collection.pop(self.index)

    def redo(self):
        value = self.resource.resolve(self.valueURIFragment)
        self._collection.insert(self.index, value)

    def do_execute(self):
        value = self.resource.resolve(self.valueURIFragment)
        if self.index is not None:
            self._collection.insert(self.index, value)
        else:
            self.index = len(self._collection)
            self._collection.append(value)


class SetCrossReference(AbstractCommand):
    def __init__(self, owner=None, feature=None, value=None, previous_value=None):
        super().__init__(owner, feature, value)
        self.previous_value = previous_value
        self.valueURIFragment = value.eURIFragement()
        self.previous_valueURIFragment = previous_value.eURIFragement()
        self.ownerURIFragment = owner.eURIFragment()
        self._executed = True

    @property
    def can_execute(self):
        can = super().can_execute
        return can and not self.feature.many

    def undo(self):
        prev_value = self.resource.resolve(self.previous_valueURIFragment)
        #self.owner.eSet(self.feature, self.previous_value)
        self.resource.resolve(self.ownerURIFragment).eSet(self.feature, prev_value)

    def redo(self):
        val = self.resource.resolve(self.valueURIFragment)
        #self.owner.eSet(self.feature, self.value)
        self.resource.resolve(self.ownerURIFragment).eSet(self.feature, val)

    def do_execute(self):
        #prev_value = self.ownerResource.resolve(self.previous_valueURIFragment)
        #self.previous_value = self.owner.eGet(self.feature)
        self.previous_value = self.resource.resolve(self.ownerURIFragment).eGet(self.feature)
        self.previous_valueURIFragment = self.previous_value.eURIFragment()

        #self.owner.eSet(self.feature, self.value)
        val = self.resource.resolve(self.valueURIFragment)
        self.resource.resolve(self.ownerURIFragment).eSet(self.feature, val)

class Set(AbstractCommand):
    def __init__(self, owner=None, feature=None, value=None):
        super().__init__(owner, feature, value)

    @property
    def can_execute(self):
        can = super().can_execute
        return can and not self.feature.many

    def undo(self):
        self.owner.eSet(self.feature, self.previous_value)

    def redo(self):
        self.owner.eSet(self.feature, self.value)

    def do_execute(self):
        object_ = self.owner
        self.previous_value = object_.eGet(self.feature)
        object_.eSet(self.feature, self.value)


class Add(AbstractCommand):
    def __init__(self, owner=None, feature=None, value=None, index=None):
        super().__init__(owner, feature, value)
        self.index = index
        self._collection = None
        self.deepcopy = False

    @property
    def can_execute(self):
        executable = super().can_execute
        executable = executable and self.value is not None
        self._collection = self.owner.eGet(self.feature)
        return executable

    @property
    def can_undo(self):
        can = super().can_undo
        if self.deepcopy:
            return can
        return can and self.value in self._collection

    def undo(self):
        self._collection.pop(self.index)

    def redo(self):
        self._collection.insert(self.index, self.value)

    def do_execute(self):
        if self.index is not None:
            self._collection.insert(self.index, self.value)
        else:
            self.index = len(self._collection)
            self._collection.append(self.value)


class Remove(AbstractCommand):
    def __init__(self, owner=None, feature=None, value=None, index=None):
        super().__init__(owner, feature, value)
        self.index = index
        self.deepcopy = False
        self._collection = None
        if bool(self.index is not None) == bool(self.value is not None):
            raise ValueError('Remove command cannot have index and value set '
                             'together.')

    @property
    def can_execute(self):
        executable = super().can_execute
        self._collection = self.owner.eGet(self.feature)
        if self.index is None:
            executable = executable and self.value is not None
        else:
            self.value = self._collection[self.index]
        return executable

    def undo(self):
        self._collection.insert(self.index, self.value)

    def redo(self):
        self._collection.pop(self.index)

    def do_execute(self):
        if self.index is None:
            self.index = self._collection.index(self.value)
        self._collection.pop(self.index)

class Delete(AbstractCommand):
    def __init__(self, owner=None):
        super().__init__(owner=owner)

    @property
    def can_execute(self):
        self.feature = self.owner.eContainmentFeature()
        self.references = {}
        elements = {self.owner}
        elements.update(self.owner.eAllContents())
        for element in elements:
            rels_tuple = [(ref, element.eGet(ref))
                          for ref in element.eClass.eAllReferences()]
            self.references[element] = rels_tuple
        self.inverse_references = {}
        for element in elements:
            rels_tuple = []
            for obj, reference in element._inverse_rels:
                if reference.many:
                    index = obj.eGet(reference).index(element)
                else:
                    index = 0
                rels_tuple.append((index, obj, reference))
            self.inverse_references[element] = rels_tuple
        return True

    def undo(self):
        for element, v in self.references.items():
            for reference, content in v:
                if reference.many:
                    element.eGet(reference).extend(content)
                else:
                    element.eSet(reference, content)
        for element, v in self.inverse_references.items():
            for i, obj, reference in v:
                if reference.many:
                    obj.eGet(reference).insert(i, element)
                else:
                    obj.eSet(reference, element)

    def redo(self):
        self.do_execute()

    def do_execute(self):
        self.owner.delete()

    def __repr__(self):
        return f'{self.__class__.__name__} {self.owner}'

def deepcopy_with_xrefs(eobject: EObject,
                        memo=None,
                        xrefs: List[AbstractCommand] = None) -> Tuple[EObject, List[AbstractCommand]]:
    """
    Deepcopies an EObject, but removes the cross-references, as these need to be handles separately. This serialization is
    done by creating an AddCrossReference notification for each reference as a Set or Add notification to set these
    references separately from the EObject to avoid dangling references to the original if a sub-object contains these
    references.
    See also code of deepcopy() of an EObject in support_functions.py that does copy the references too
    See also ChangeSerializer.py deepcopy_eobject_change() that does the same but then for serializing changes.
    """

    first_call = False
    if memo is None:
        memo = dict()
        first_call = True
    if eobject in memo:
        return memo[eobject], xrefs
    copy: EObject = eobject.clone()

    if first_call:
        xrefs = []
    eclass: EClass = eobject.eClass
    for x in eclass.eAllStructuralFeatures():
        if isinstance(x, EReference):
            ref: EReference = x
            value = eobject.eGet(ref)
            if value is None:
                continue
            if ref.containment:
                if ref.many and isinstance(value, ECollection):
                    # clone all containment elements
                    eAbstractSet: ECollection = copy.eGet(ref.name)
                    for ref_value in value:
                        duplicate, cl = deepcopy_with_xrefs(ref_value, memo, xrefs)
                        xrefs.extend(cl)
                        eAbstractSet.append(duplicate)
                else:
                    duplicate, cl = deepcopy_with_xrefs(value, memo, xrefs)
                    xrefs.extend(cl)
                    copy.eSet(ref.name, duplicate)

    # now copy should a full copy, but without cross references

    memo[eobject] = copy

    if first_call:
        for k, v in memo.items():
            eclass: EClass = k.eClass
            for x in eclass.eAllStructuralFeatures():
                if isinstance(x, EReference):
                    logger.debug("deepcopy with Changes: processing x-reference {}".format(x.name))
                    ref: EReference = x
                    orig_value = k.eGet(ref)
                    if orig_value is None:
                        continue
                    if not ref.containment:
                        opposite = ref.eOpposite
                        if opposite and opposite.containment:
                            # do not handle eOpposite relations, they are handled automatically in pyEcore
                            continue
                        if x.many:
                            for orig_ref_value in orig_value:
                                fragment = orig_ref_value.eURIFragment()
                                #change = Add(ownerFragment=k.eURIFragment(), stringValue=fragment, feature=x.name)
                                change = AddCrossReference(owner=k, feature=x, value=orig_ref_value)
                                xrefs.append(change)
                                logger.debug("deepcopy change {}: processing x-reference {}: {}".format(eobject, x.name, fragment))
                        else:
                            fragment = orig_value.eURIFragment()
                            change = SetCrossReference(owner=k, feature=x, value=orig_value)
                            logger.debug(
                                "deepcopy change {}: processing x-reference {}: {}".format(eobject, x.name, fragment))
                            xrefs.append(change)
    # TODO filter out double connectedTo references
    #xrefs = filterDoubleConnectedTo(xrefs)
    return copy, xrefs