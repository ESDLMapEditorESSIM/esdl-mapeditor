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

"""
Support functions for managing EObjects
"""
from pyecore.ecore import EAttribute, EObject, EClass, EReference, EStructuralFeature
from pyecore.valuecontainer import ECollection
import logging

logger = logging.getLogger(__name__)


# add support for shallow copying or cloning an object
# it copies the object's attributes (e.g. clone an object), does only shallow copying
def clone(self):
    """
    Shallow copying or cloning an object
    It only copies the object's attributes (e.g. clone an object)
    Usage object.clone() or copy.copy(object) (as _copy__() is also implemented)
    :param self:
    :return: A clone of the object
    """
    newone = type(self)()
    eclass = self.eClass
    for x in eclass.eAllStructuralFeatures():
        if isinstance(x, EAttribute):
            #logger.trace("clone: processing attribute {}".format(x.name))
            if x.many:
                eOrderedSet = newone.eGet(x.name)
                for v in self.eGet(x.name):
                    eOrderedSet.append(v)
            else:
                newone.eSet(x.name, self.eGet(x.name))
    return newone


def deepcopy(self, memo=None):
    """
    Deep copying an EObject.
    Does not work yet for copying references from other resources than this one.
    """
    #logger.debug("deepcopy: processing {}".format(self))
    first_call = False
    if memo is None:
        memo = dict()
        first_call = True
    if self in memo:
        return memo[self]

    copy: EObject = self.clone()
    #logger.debug("Shallow copy: {}".format(copy))
    eclass: EClass = self.eClass
    for x in eclass.eAllStructuralFeatures():
        if isinstance(x, EReference):
            #logger.debug("deepcopy: processing reference {}".format(x.name))
            ref: EReference = x
            value: EStructuralFeature = self.eGet(ref)
            if value is None:
                continue
            if ref.containment:
                if ref.many and isinstance(value, ECollection):
                    #clone all containment elements
                    eAbstractSet = copy.eGet(ref.name)
                    for ref_value in value:
                        duplicate = ref_value.__deepcopy__(memo)
                        eAbstractSet.append(duplicate)
                else:
                    copy.eSet(ref.name, value.__deepcopy__(memo))
            #else:
            #    # no containment relation, but a reference
            #    # this can only be done after a full copy
            #    pass
    # now copy should a full copy, but without cross references

    memo[self] = copy

    if first_call:
        #logger.debug("copying references")
        for k, v in memo.items():
            eclass: EClass = k.eClass
            for x in eclass.eAllStructuralFeatures():
                if isinstance(x, EReference):
                    #logger.debug("deepcopy: processing x-reference {}".format(x.name))
                    ref: EReference = x
                    orig_value: EStructuralFeature = k.eGet(ref)
                    if orig_value is None:
                        continue
                    if not ref.containment:
                        opposite = ref.eOpposite
                        if opposite and opposite.containment:
                            # do not handle eOpposite relations, they are handled automatically in pyEcore
                            continue
                        if x.many:
                            eAbstractSet = v.eGet(ref.name)
                            for orig_ref_value in orig_value:
                                try:
                                    copy_ref_value = memo[orig_ref_value]
                                except KeyError:
                                    logger.warning(f'Cannot find reference of type {orig_ref_value.eClass.name} for reference {k.eClass.name}.{ref.name} in deepcopy memo, using original')
                                    copy_ref_value = orig_ref_value
                                eAbstractSet.append(copy_ref_value)
                        else:
                            try:
                                copy_value = memo[orig_value]
                            except KeyError:
                                logger.warning(f'Cannot find reference of type {orig_value.eClass.name} of reference {k.eClass.name}.{ref.name} in deepcopy memo, using original')
                                copy_value = orig_value
                            v.eSet(ref.name, copy_value)
    return copy

    # show deleted object from memory
    # setattr(EObject, '__del__', lambda x: print('Deleted {}'.format(x.eClass.name)))

    # def update_id(n: Notification):
    #     if isinstance(n.feature, EAttribute):
    #         #print(n)
    #         if n.feature.name == 'id':
    #             resource = n.notifier.eResource
    #             if resource is not None and (n.kind != Kind.UNSET and n.kind != Kind.REMOVE):
    #                 print('ADDING to UUID dict {}#{}, notification type {}'.format(n.notifier.eClass.name, n.feature.name, n.kind.name))
    #                 resource.uuid_dict[n.new] = n.notifier
    #                 if n.old is not None and n.old is not '':
    #                     del resource.uuid_dict[n.old]
    # observer = EObserver()
    # observer.notifyChanged = update_id
    #
    # old_init = EObject.__init__
    # def new_init(self, **kwargs):
    #     observer.observe(self)
    #     old_init(self, **kwargs)
    #
    # setattr(EObject, '__init__', new_init)

    # Methods to automatically update the uuid_dict.
    # Currently disabled, because it does not work in all circumstances
    # This only works when the object which id is to be added to the dict is already part
    # of the energysystem xml tree, otherwise there is no way of knowing to which uuid_dict it should be added.
    # E.g.
    # > asset = esdl.Asset(id='uuid)
    # > asset.port.append(esdl.InPort(id='uuid)) # this does not work because asset is not part of the energy system yet
    # > area.asset.append(asset) #works for asset, but not for port. In order to have port working too, this statement
    # should be executed bofore adding the port...

    # old_set = EObject.__setattr__
    # def updated_set(self, feature, value):
    #     old_set(self, feature, value)
    #     #if feature == 'id':
    #     #print('Feature :{}#{}, value={}, resource={}'.format(self.eClass.name, feature, value, '?'))
    #     #if isinstance(feature, EReference):
    #     if hasattr(value, 'id') and feature[0] != '_':
    #         print('*****Update uuid_dict {}#{} for {}#id'.format(self.eClass.name, feature, value.eClass.name))
    #         self.eResource.uuid_dict[value.id] = value
    # setattr(EObject, '__setattr__', updated_set)
    #
    #
    #
    # old_append = EAbstractSet.append
    # def updated_append(self, value, update_opposite=True):
    #     old_append(self, value, update_opposite)
    #     #print('EAbstractSet :{}, value={}, resource={}, featureEr={}'.format(self, value, value.eResource, self.feature.eResource))
    #     if hasattr(value, 'id'):
    #         if self.feature.eResource:
    #             print('****Update uuid_dict AbstractSet-{}#id'.format(value.eClass.name))
    #             self.feature.eResource.uuid_dict[value.id] = value
    #         elif value.eResource:
    #             print('****Update uuid_dict AbstractSet-{}#id'.format(value.eClass.name))
    #             value.eResource.uuid_dict[value.id] = value
    #
    # setattr(EAbstractSet, 'append', updated_append)




    # def toJSON(self):
    #     return json.dumps(self, default=lambda o: list(o),
    #                       sort_keys=True, indent=4)
    # setattr(EOrderedSet, 'toJSON', toJSON)