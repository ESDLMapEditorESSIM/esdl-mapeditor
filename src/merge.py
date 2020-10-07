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

import esdl.esdl
from pyecore.ecore import EObject, EClass, EReference
from pyecore.valuecontainer import EAbstractSet
import pyecore.behavior
from uuid import uuid4
"""
Merges 2 EnergySystems into one
"""

_options = dict()


class ESDLMerger:

    def __init__(self):
        _options['forceCombineInstances'] = True
        _options['forceCombineMainArea'] = True

    def config(self, forceCombineInstances=True, forceCombineMainArea=True):
        _options['forceCombineInstances'] = forceCombineInstances
        _options['forceCombineMainArea'] = forceCombineMainArea

    def merge(self, left: esdl.EnergySystem, right: esdl.EnergySystem) -> esdl.EnergySystem:
        """
        Merges the right energy system into the left
        It only looks at containment features, so attributes are ignored for now
        If right is having containment features not present in left, they get added.
        If left has containment features not present in right, they are kept.
        """
        #left.instance[0].area.merge(right.instance[0].area)
        #left.merge(right)
        _compareAndMerge(left, right)
        print("##############################################################################################")
        _compareAndMerge(left, right, updateReferences=True)
        return left


def _compareAndMerge(left: EObject, right: EObject, parent=None, reference=None, updateReferences=False):
    leftClass: EClass = left.eClass
    for feature in leftClass.eAllStructuralFeatures():
        leftName = ""
        if hasattr(left, 'id'): leftName = left.id
        if hasattr(left, 'name'): leftName = left.name
        rightName = ""
        if hasattr(right, 'id'): rightName = right.id
        if hasattr(right, 'name'): rightName = right.name


        if isinstance(feature, EReference):
            print("Comparing {}[{}].{} with {}[{}].{}".format(left.eClass.name, leftName, feature.name, right.eClass.name, rightName, feature.name))
            ref: EReference = feature
            if not updateReferences and ref.containment and not (ref.eOpposite and ref.eOpposite.containment):
                # Only handle containment references, not references that are contained somewhere else
                leftValue = left.eGet(ref)
                rightValue = right.eGet(ref)
                if ref.many:
                    # multiple relations are contained
                    result = _mergeMany(leftValue, rightValue, left, ref)
                    if result:
                        left.eSet(ref, result)

                else:
                    # single containment relation
                    result = _mergeSingle(leftValue, rightValue, left, ref)
                    if result:
                        left.eSet(ref, result)
            elif updateReferences and not ref.containment and not (ref.eOpposite and ref.eOpposite.containment):
                # 2nd run for non-containment references (and not eOpposite references)
                #TODO: need to traverse containment relaations
                leftValue = left.eGet(ref)
                rightValue = right.eGet(ref)
                if ref.many:
                    # todo: multi references list
                    pass
                else:
                    if leftValue is None and rightValue is not None:
                        if hasattr(rightValue, 'id'):
                            print('## {}.{} should point to {}'.format(left.eClass.name, ref.name, rightValue.id))

def _mergeMany(leftValue, rightValue, parent=None, reference=None):
    if not isinstance(leftValue, EAbstractSet):
        raise ValueError('Not a set')

    if _options['forceCombineInstances'] and parent.eClass.name == "EnergySystem" and reference.name == 'instance':
        print("- Force combine main instances in numerical order")
        for i in range(0, min(len(leftValue), len(rightValue))):
            l = leftValue[i]
            r = rightValue[i]
            _compareAndMerge(l, r, parent, reference)
        return leftValue

    print("- Merging a set for {}.{}".format(parent.eClass.name, reference.name))
    same, difference = leftValue.merge(rightValue)
    if difference:
        #add differences
        print("- Adding {} to {}.{}".format(difference, parent.eClass.name, reference.name))
        leftValue.extend(difference)
    if same:
        for (l, r) in same:
            #should be: contine merge for same
            _compareAndMerge(l, r, parent, reference)
    return leftValue

def _mergeSingle(leftValue: EObject, rightValue: EObject, parent=None, reference=None) -> (EObject, bool):
    if rightValue is None and leftValue is None:
        return None

    if rightValue is None:
        print("- Keeping left branch {} of {} as right is None".format(leftValue, reference.name))
        return leftValue

    if leftValue is None:
        # merge right if available
        # indicate False that merging this branch is ready and don't continue
        print("- Copying right branch {} of {} as left is None".format(rightValue, reference.name))
        return rightValue.deepcopy()

    result = leftValue.merge(rightValue)
    if result == leftValue:
        # result is still the same object (e.g. not replaced by something new (e.g. in case of merging two Main Areas))
        _compareAndMerge(leftValue, rightValue, parent, reference)
    return result


# add default merge for all EObjects
def merge_unsupported(self, other, parent=None, reference=None):
    print("Merging not supported for type {}, returning self.".format(self.eClass.name))
    return self
setattr(EObject, 'merge', merge_unsupported)

# merge two AbstractSets (e.g. EOrderedSet) based on id's
# calculates the differences and the similarities in the lists and returns this
# same is a list of tuples (self.item, other.item) and differences just a list of items not in self but only in other
def mergeList(self, other, parent=None, reference=None):
    self_id_list = [x.id for x in self]
    same = list()
    diff = list()
    for o in other:
        if o.id in self_id_list:
            j = [z for z in self if z.id == o.id][0]
            same.append( (j, o) )
        else:
            diff.append(o)
    #difference = [i for i in self if not i.id in [x.id for x in other]]
    print("- Merge Lists: Diff: {}, same: {} (left: {} and right: {})".format(diff, same, list(self), list(other)))
    return same, diff
setattr(EAbstractSet, 'merge', mergeList)


@esdl.Area.behavior
def merge(self:esdl.Area, other: esdl.Area, parent=None, reference=None) -> esdl.Area:
    if _options['forceCombineMainArea']:
        print("- Force merging main area's {} and {} into one.".format(self.name, other.name))
        return self
    elif self.id == other.id:
        print("- merge {}: {} with {}: both equal".format(self.eClass.name, self.name, other.name))
        # return self and handle sub containments
        return self
    else:
        if self.containingArea is None:
            # this is the main area, as it does not have a containing Area
            print("- Merging main areas into a merged area with two subAreas")
            newarea = esdl.Area(id=str(uuid4()), name="Merged Area")
            newarea.area.append(self)
            newarea.area.append(other.deepcopy())
            # todo update references e.g. Carriers and Sectors
            return newarea
            #parent.eSet(reference, newarea)
        else:
            print("- Areas are different, merging: TODO")
            # different areas: add both
            return _compareAndMerge(self, other)

