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
    variantCollection = EReference(ordered=True, unique=True,
                                   containment=True, derived=False, upper=-1)

    def __init__(self, *, name=None, description=None, variantCollection=None, version=None):
        # if kwargs:
        #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if name is not None:
            self.name = name

        if description is not None:
            self.description = description

        if version is not None:
            self.version = version

        if variantCollection:
            self.variantCollection.extend(variantCollection)


class Variant(EObject, metaclass=MetaEClass):
    """A variant is a variant on a loaded esdl::EnergySystem (defined through the EnerySystemProxy). In principle it collects changes made to an ESDL in memory (referenced by the snapshotRef) and stores it in the change relations (as most tools edit an ESDL and not generate changes). To collect changes, a listener is added to the EMF Resource that each variant has. 
When serializing the changes of a variant are serialized in XML. """
    name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    description = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    lastChanged = EAttribute(eType=EDate, unique=True, derived=False, changeable=True)
    id = EAttribute(eType=EString, unique=True, derived=False, changeable=True, iD=True)
    change = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)
    variant = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)
    parentVariant = EReference(ordered=True, unique=True, containment=False, derived=False)
    snapshot = EReference(ordered=True, unique=True, containment=True, derived=False)
    variantCollection = EReference(ordered=True, unique=True, containment=False, derived=False)
    snapshotRef = EReference(ordered=True, unique=True, containment=False, derived=False)
    lastProcessedChange = EReference(ordered=True, unique=True, containment=False, derived=False)

    def __init__(self, *, name=None, description=None, change=None, lastChanged=None, variant=None, parentVariant=None, snapshot=None, variantCollection=None, snapshotRef=None, id=None, lastProcessedChange=None):
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

        if variantCollection is not None:
            self.variantCollection = variantCollection

        if snapshotRef is not None:
            self.snapshotRef = snapshotRef

        if lastProcessedChange is not None:
            self.lastProcessedChange = lastProcessedChange


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


class VariantCollection(EObject, metaclass=MetaEClass):
    """An EnergySystemProxy proxies an actual EnergySystem. This proxy is needed as we want to seperate the ESDL ecore model from this ecore model. It is a bit inconvenient, but allows us to have the loaded EnergySystems and its variants in seperate EMF Resources when editing them. When Serializing the ESDLProject, each EnergySystem that is loaded in the project is serialized using the energysystem containment relation. When loaded, the EnergySystem is moved out of the ESDLProject into its own EMF Resource and is then referenced by the energysystemRef. This allows for multiple (same) EnergySystems with same IDs of assets to work in parallel without ID clashes."""
    name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    description = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    lastChanged = EAttribute(eType=EDate, unique=True, derived=False, changeable=True)
    id = EAttribute(eType=EString, unique=True, derived=False, changeable=True, iD=True)
    variant = EReference(ordered=True, unique=True, containment=True, derived=False)
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

        if variant is not None:
            self.variant = variant

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
    objectFragment = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    owner = EReference(ordered=True, unique=True, containment=False, derived=False)
    objectValue = EReference(ordered=True, unique=True, containment=True, derived=False)
    objectValue_xrefs = EReference(ordered=True, unique=True,
                                   containment=True, derived=False, upper=-1)
    previousValue_xrefs = EReference(ordered=True, unique=True,
                                     containment=True, derived=False, upper=-1)

    def __init__(self, *, owner=None, stringValue=None, previousValue=None, feature=None, objectValue=None, ownerFragment=None, objectValue_xrefs=None, previousValue_xrefs=None, objectFragment=None, **kwargs):

        super().__init__(**kwargs)

        if stringValue is not None:
            self.stringValue = stringValue

        if previousValue is not None:
            self.previousValue = previousValue

        if feature is not None:
            self.feature = feature

        if ownerFragment is not None:
            self.ownerFragment = ownerFragment

        if objectFragment is not None:
            self.objectFragment = objectFragment

        if owner is not None:
            self.owner = owner

        if objectValue is not None:
            self.objectValue = objectValue

        if objectValue_xrefs:
            self.objectValue_xrefs.extend(objectValue_xrefs)

        if previousValue_xrefs:
            self.previousValue_xrefs.extend(previousValue_xrefs)


class Set(DetailedChange):

    previousObjectValue = EReference(ordered=True, unique=True, containment=True, derived=False)

    def __init__(self, *, previousObjectValue=None, **kwargs):

        super().__init__(**kwargs)

        if previousObjectValue is not None:
            self.previousObjectValue = previousObjectValue


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
