import logging
from typing import List, Tuple

from pyecore.ecore import EObject, EClass, EReference
from pyecore.valuecontainer import ECollection

from esdlproject import AbstractChange, Add, Set, DetailedChange, Remove

logger = logging.getLogger(__name__)


def deepcopy_eobject_change(eobject: EObject,
                            memo=None,
                            changeList:List[AbstractChange] = None) -> Tuple[EObject, List[AbstractChange]]:
    """
    Deepcopies an EObject, but removes the references, as these need to be serialized correctly. This serialization is
    done by creating an AbstractChange for each reference as a Set or Add Change to set these references after the
    EObject has been loaded.
    See also code of deepcopy() of an EObject in support_functions.py that does copy the references too
    """

    first_call = False
    if memo is None:
        memo = dict()
        first_call = True
    if eobject in memo:
        return memo[eobject], changeList
    copy: EObject = eobject.clone()

    if first_call:
        changeList = []
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
                        duplicate, cl = deepcopy_eobject_change(ref_value, memo, changeList)
                        changeList.extend(cl)
                        eAbstractSet.append(duplicate)
                else:
                    duplicate, cl = deepcopy_eobject_change(value, memo, changeList)
                    changeList.extend(cl)
                    copy.eSet(ref.name, duplicate)

    # now copy should a full copy, but without cross references

    memo[eobject] = copy

    if first_call:
        for k, v in memo.items():
            eclass: EClass = k.eClass
            for x in eclass.eAllStructuralFeatures():
                if isinstance(x, EReference):
                    #logger.debug("deepcopy with Changes: processing x-reference {}".format(x.name))
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
                                change = Add(ownerFragment=k.eURIFragment(), objectFragment=fragment, feature=x.name)
                                changeList.append(change)
                                #logger.debug("deepcopy change{}: processing x-reference {}: {}".format(eobject, x.name, fragment))
                        else:
                            fragment = orig_value.eURIFragment()
                            change = Set(ownerFragment=k.eURIFragment(), objectFragment=fragment, feature=x.name)
                            changeList.append(change)
    changeList,_ = filterDoubleConnectedTo(changeList)
    # copy over the eIsSet configuration, otherwise all attributes are set due to this deepcopy
    #copy._isset = InternalSet(self._isset)
    copy._isset = eobject._isset.copy()
    return copy, changeList


def filterDoubleConnectedTo(change_list: List[DetailedChange]) -> (List[DetailedChange], List[DetailedChange]):
    """
    Filter out double ConnectedTo relations in a list of DetailedChanges
    """
    connected_to_list = []
    doubles = []
    return_list = list(change_list)

    # find possible duplicates
    for i, ch in enumerate(change_list):
        if (isinstance(ch, Add) or isinstance(ch, Remove)) and ch.feature == 'connectedTo':
            connected_to_list.append((i, ch))

    # filter out duplicates
    for i, (index, change) in enumerate(connected_to_list):
        for j, (jndex, change2) in enumerate(connected_to_list[i+1:]):
            #k = i+1+j
            if change.ownerFragment == change2.objectFragment and change2.ownerFragment == change.objectFragment and \
                change.eClass.name == change2.eClass.name:
                # change2 is double
                #print(f'DoubleConnectedTo: {i} remove {j}: {change2.ownerFragment} <-> {change2.objectFragment}')
                connected_to_list.remove((jndex, change2))
                doubles.append(change2)
                return_list.remove(change2)
            elif change.ownerFragment == change2.ownerFragment and change2.objectFragment == change.objectFragment and \
                change.eClass.name == change2.eClass.name:
                #print(f'DoubleConnectedTo: {i} remove {j} {change2.ownerFragment} <-> {change2.objectFragment}')
                connected_to_list.remove((jndex, change2))
                doubles.append(change2)
                return_list.remove(change2)
    return return_list, doubles
