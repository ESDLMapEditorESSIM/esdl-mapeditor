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
from itertools import chain

from pyecore.notification import Notification, Kind, ENotifer
from pyecore.valuecontainer import ECollection, PyEcoreValue
from pyecore.ecore import EObject
from ordered_set import OrderedSet
from pyecore.ordered_set_patch import pop as pop_patch



def patch_notification_system():

    def remove(self, value, update_opposite=True):
        #print("\t\t######## patched ECollection.remove() ##########", self.__class__, len(self))
        # send notification before actual removal
        self.owner.notify(Notification(old=value,
                                       feature=self.feature,
                                       kind=Kind.REMOVE))

        if self.is_ref:
            self._update_container(None, previous_value=value)
            if update_opposite:
                self._update_opposite(value, self.owner, remove=True)

        super(OrderedSet, self).remove(value)

    # update remove
    setattr(ECollection, 'remove', remove)

    def pop(self, index=None):
        #print("\t\t######## patched ECollection.pop() ##########", self.__class__, len(self))
        if index is None:
            peek = self.items[-1]
        else:
            peek = self.items[index]

        # send notification before actually removing, such that we can find the index of the element for our
        # undo-redo information
        self.owner.notify(Notification(old=peek,
                                       feature=self.feature,
                                       kind=Kind.REMOVE))

        if index is None:
            value = pop_patch(self)
        else:
            value = pop_patch(self, index)

        if self.is_ref:
            self._update_container(None, previous_value=value)
            self._update_opposite(value, self.owner, remove=True)

        return value

    setattr(ECollection, 'pop', pop)
    # TODO: also check EList.__setitem()


    # def delete(self, recursive=True):
    #     print("\t\t######## patched EClass.delete() ##########", self.eClass.__name__)
    #     if recursive:
    #         for obj in self.eAllContents():
    #             obj.delete()
    #     seek = set(self._inverse_rels)
    #     # we also clean all the object references
    #     connTo = None
    #     refs = []
    #     for r in self.eClass.eAllReferences():
    #         if r.name == 'connectedTo':
    #             connTo = r
    #         else:
    #             refs.append(r)
    #     if connTo is not None:
    #         refs.append(connTo)
    #     print('Updated list:', self.eClass.name, refs)
    #
    #     seek.update((self, ref) for ref in refs)
    #     for owner, feature in seek:
    #         fvalue = owner.eGet(feature)
    #         if feature.many:
    #             if self in fvalue:
    #                 fvalue.remove(self)
    #                 continue
    #             elif self is owner:
    #                 fvalue.clear()
    #                 continue
    #             value = next((val for val in fvalue
    #                           if getattr(val, '_wrapped', None) is self),
    #                          None)
    #             if value:
    #                 fvalue.remove(value)
    #         else:
    #             if self is fvalue or self is owner:
    #                 owner.eSet(feature, None)
    #                 continue
    #             value = (fvalue if getattr(fvalue, '_wrapped', None) is self
    #                      else None)
    #             if value:
    #                 owner.eSet(feature, None)
    #
    # setattr(EObject, 'delete', delete)


    # def notify(self, notification):
    #     notification.notifier = notification.notifier or self
    #     resource = self.eResource
    #     resource_listeners = []
    #     resource_eternals = []
    #     if resource:
    #         resource_listeners = resource.listeners
    #         resource_eternals = resource._eternal_listener
    #     else:
    #         print("NO RESOURCE FOR", notification.notifier.eClass.name, notification.feature.name)
    #     listeners = chain(resource_eternals, resource_listeners,
    #                       self._eternal_listener, self.listeners)
    #     for listener in listeners:
    #         listener.notifyChanged(notification)

    # setattr(ENotifer, 'notify', notify)


    def _update_container(self, value, previous_value=None):
        if not self.is_cont:
            return
        if value:
            resource = value.eResource
            if resource and value in resource.contents:
                resource.remove(value)
            prev_container = value._container
            prev_feature = value._containment_feature
            if (prev_container != self.owner
                    or prev_feature != self.feature) \
                    and isinstance(prev_container, EObject):
                prev_container.__dict__[prev_feature.name] \
                              .remove_or_unset(value)
            value._container = self.owner
            value._containment_feature = self.feature
        if previous_value:
            # keep the container reference, so we can find out to what resource this object belongs to
            # and that notifications are send for these changes.
            # TODO: reset the previous_value._container after processing the notification
            # (see also patch in XMLResource to fix this manually)
            #print("NO CONTAINER FOR", previous_value, previous_value._container, previous_value._containment_feature)
            pass
            #previous_value._container = None
            #previous_value._containment_feature = None

    #setattr(PyEcoreValue, '_update_container', _update_container)

