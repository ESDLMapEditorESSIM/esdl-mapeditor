"""Definition of meta model 'esdlproject'."""
from functools import partial
import pyecore.ecore as Ecore
from pyecore.ecore import *


name = 'esdlproject'
nsURI = 'http://www.tno.nl/esdl/project'
nsPrefix = 'esdlproject'

eClass = EPackage(name=name, nsURI=nsURI, nsPrefix=nsPrefix)

eClassifiers = {}
getEClassifier = partial(Ecore.getEClassifier, searchspace=eClassifiers)


class ESDLProject(EObject, metaclass=MetaEClass):

    name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    description = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    version = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    baseVariant = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)

    def __init__(self, *, name=None, description=None, baseVariant=None, version=None):
        # if kwargs:
        #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if name is not None:
            self.name = name

        if description is not None:
            self.description = description

        if version is not None:
            self.version = version

        if baseVariant:
            self.baseVariant.extend(baseVariant)


class Variant(EObject, metaclass=MetaEClass):

    name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    description = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    lastChanged = EAttribute(eType=EDate, unique=True, derived=False, changeable=True)
    id = EAttribute(eType=EString, unique=True, derived=False, changeable=True, iD=True)
    change = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)
    variant = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)
    parentVariant = EReference(ordered=True, unique=True, containment=False, derived=False)
    snapshot = EReference(ordered=True, unique=True, containment=True, derived=False)
    baseVariant = EReference(ordered=True, unique=True, containment=False, derived=False)
    snapshotRef = EReference(ordered=True, unique=True, containment=False, derived=False)

    def __init__(self, *, name=None, description=None, change=None, lastChanged=None, variant=None, parentVariant=None, snapshot=None, baseVariant=None, snapshotRef=None, id=None):
        # if kwargs:
        #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if name is not None:
            self.name = name

        if description is not None:
            self.description = description

        if lastChanged is not None:
            self.lastChanged = lastChanged

        if id is not None:
            self.id = id

        if change:
            self.change.extend(change)

        if variant:
            self.variant.extend(variant)

        if parentVariant is not None:
            self.parentVariant = parentVariant

        if snapshot is not None:
            self.snapshot = snapshot

        if baseVariant is not None:
            self.baseVariant = baseVariant

        if snapshotRef is not None:
            self.snapshotRef = snapshotRef


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


class BaseVariant(EObject, metaclass=MetaEClass):

    name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    description = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    lastChanged = EAttribute(eType=EDate, unique=True, derived=False, changeable=True)
    id = EAttribute(eType=EString, unique=True, derived=False, changeable=True, iD=True)
    variant = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)
    energysystem = EReference(ordered=True, unique=True, containment=True, derived=False)
    energysystemRef = EReference(ordered=True, unique=True, containment=False, derived=False)

    def __init__(self, *, variant=None, energysystem=None, name=None, description=None, lastChanged=None, energysystemRef=None, id=None):
        # if kwargs:
        #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if name is not None:
            self.name = name

        if description is not None:
            self.description = description

        if lastChanged is not None:
            self.lastChanged = lastChanged

        if id is not None:
            self.id = id

        if variant:
            self.variant.extend(variant)

        if energysystem is not None:
            self.energysystem = energysystem

        if energysystemRef is not None:
            self.energysystemRef = energysystemRef


class HighLevelChange(AbstractChange):

    label = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    commitMessage = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    author = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    change = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)

    def __init__(self, *, change=None, label=None, commitMessage=None, author=None, **kwargs):

        super().__init__(**kwargs)

        if label is not None:
            self.label = label

        if commitMessage is not None:
            self.commitMessage = commitMessage

        if author is not None:
            self.author = author

        if change:
            self.change.extend(change)


@abstract
class DetailedChange(AbstractChange):

    stringValue = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    previousValue = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    feature = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    ownerFragment = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    owner = EReference(ordered=True, unique=True, containment=False, derived=False)
    objectValue = EReference(ordered=True, unique=True, containment=True, derived=False)
    objectReference = EReference(ordered=True, unique=True, containment=False, derived=False)

    def __init__(self, *, owner=None, stringValue=None, previousValue=None, feature=None, objectValue=None, objectReference=None, ownerFragment=None, **kwargs):

        super().__init__(**kwargs)

        if stringValue is not None:
            self.stringValue = stringValue

        if previousValue is not None:
            self.previousValue = previousValue

        if feature is not None:
            self.feature = feature

        if ownerFragment is not None:
            self.ownerFragment = ownerFragment

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
