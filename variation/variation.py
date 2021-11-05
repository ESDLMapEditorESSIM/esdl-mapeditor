"""Definition of meta model 'variation'."""
from functools import partial
import pyecore.ecore as Ecore
from pyecore.ecore import *


name = 'variation'
nsURI = 'http://www.tno.nl/esdl/variation'
nsPrefix = 'variation'

eClass = EPackage(name=name, nsURI=nsURI, nsPrefix=nsPrefix)

eClassifiers = {}
getEClassifier = partial(Ecore.getEClassifier, searchspace=eClassifiers)


class Project(EObject, metaclass=MetaEClass):

    name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    description = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    version = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    variants = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)

    def __init__(self, *, name=None, description=None, variants=None, version=None):
        # if kwargs:
        #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if name is not None:
            self.name = name

        if description is not None:
            self.description = description

        if version is not None:
            self.version = version

        if variants:
            self.variants.extend(variants)


class Variant(EObject, metaclass=MetaEClass):

    name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    description = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    lastChanged = EAttribute(eType=EDate, unique=True, derived=False, changeable=True)
    changes = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)
    variant = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)
    parentVariant = EReference(ordered=True, unique=True, containment=False, derived=False)
    snapshot = EReference(ordered=True, unique=True, containment=True, derived=False)

    def __init__(self, *, name=None, description=None, changes=None, lastChanged=None, variant=None, parentVariant=None, snapshot=None):
        # if kwargs:
        #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if name is not None:
            self.name = name

        if description is not None:
            self.description = description

        if lastChanged is not None:
            self.lastChanged = lastChanged

        if changes:
            self.changes.extend(changes)

        if variant:
            self.variant.extend(variant)

        if parentVariant is not None:
            self.parentVariant = parentVariant

        if snapshot is not None:
            self.snapshot = snapshot


@abstract
class AbstractChange(EObject, metaclass=MetaEClass):

    changedAt = EAttribute(eType=EDate, unique=True, derived=False, changeable=True)
    variant = EReference(ordered=True, unique=True, containment=False, derived=False)

    def __init__(self, *, variant=None, changedAt=None):
        # if kwargs:
        #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if changedAt is not None:
            self.changedAt = changedAt

        if variant is not None:
            self.variant = variant


class HighLevelChange(AbstractChange):

    label = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    commitMessage = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    changes = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)

    def __init__(self, *, changes=None, label=None, commitMessage=None, **kwargs):

        super().__init__(**kwargs)

        if label is not None:
            self.label = label

        if commitMessage is not None:
            self.commitMessage = commitMessage

        if changes:
            self.changes.extend(changes)


@abstract
class DetailedChange(AbstractChange):

    stringValue = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    previousValue = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    feature = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    owner = EReference(ordered=True, unique=True, containment=False, derived=False)
    objectValue = EReference(ordered=True, unique=True, containment=True, derived=False)
    objectReference = EReference(ordered=True, unique=True, containment=False, derived=False)

    def __init__(self, *, owner=None, stringValue=None, previousValue=None, feature=None, objectValue=None, objectReference=None, **kwargs):

        super().__init__(**kwargs)

        if stringValue is not None:
            self.stringValue = stringValue

        if previousValue is not None:
            self.previousValue = previousValue

        if feature is not None:
            self.feature = feature

        if owner is not None:
            self.owner = owner

        if objectValue is not None:
            self.objectValue = objectValue

        if objectReference is not None:
            self.objectReference = objectReference


class Set(DetailedChange):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class Delete(DetailedChange):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class Move(DetailedChange):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class Add(DetailedChange):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)


class Remove(DetailedChange):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
