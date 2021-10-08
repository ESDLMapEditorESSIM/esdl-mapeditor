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

from pyecore.notification import Notification, Kind
from pyecore.valuecontainer import ECollection, EOrderedSet
from pyecore.valuecontainer import PyEcoreValue, EList
from ordered_set import OrderedSet
from pyecore.ordered_set_patch import pop as pop_patch



def patch_notification_system():

    def remove(self, value, update_opposite=True):
        print("######## patched remove() ##########", self.__class__, len(self))
        if self.is_ref:
            self._update_container(None, previous_value=value)
            if update_opposite:
                self._update_opposite(value, self.owner, remove=True)
        # send notification before actual removal
        self.owner.notify(Notification(old=value,
                                       feature=self.feature,
                                       kind=Kind.REMOVE))
        super(OrderedSet, self).remove(value)

    # update remove
    setattr(ECollection, 'remove', remove)

    def pop(self, index=None):
        print("######## patched pop() ##########", self.__class__, len(self))
        if index is None:
            value = pop_patch(self)
        else:
            value = pop_patch(self, index)

        self.owner.notify(Notification(old=value,
                                       feature=self.feature,
                                       kind=Kind.REMOVE))
        if self.is_ref:
            self._update_container(None, previous_value=value)
            self._update_opposite(value, self.owner, remove=True)

        return value

    setattr(ECollection, 'pop', pop)
    # TODO: also check EList.__setitem()