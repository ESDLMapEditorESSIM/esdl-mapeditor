from pyecore.resources import global_registry
from .esdlproject import getEClassifier, eClassifiers
from .esdlproject import name, nsURI, nsPrefix, eClass
from .esdlproject import ESDLProject, Variant, AbstractChange, HighLevelChange, DetailedChange, Set, Delete, Move, Add, Remove, VariantCollection

from pyecore.ecore import EObject
from esdl import EnergySystem

from . import esdlproject

__all__ = ['ESDLProject', 'Variant', 'AbstractChange', 'HighLevelChange',
           'DetailedChange', 'Set', 'Delete', 'Move', 'Add', 'Remove', 'VariantCollection']

eSubpackages = []
eSuperPackage = None
esdlproject.eSubpackages = eSubpackages
esdlproject.eSuperPackage = eSuperPackage

ESDLProject.variantCollection.eType = VariantCollection
Variant.snapshot.eType = EnergySystem
Variant.snapshotRef.eType = EnergySystem
Variant.lastProcessedChange.eType = AbstractChange
HighLevelChange.change.eType = DetailedChange
DetailedChange.owner.eType = EObject
DetailedChange.objectValue.eType = EObject
DetailedChange.objectValue_xrefs.eType = DetailedChange
DetailedChange.previousValue_xrefs.eType = DetailedChange
Set.previousObjectValue.eType = EObject
VariantCollection.energysystem.eType = EnergySystem
VariantCollection.energysystemRef.eType = EnergySystem
Variant.change.eType = AbstractChange
Variant.variant.eType = Variant
Variant.parentVariant.eType = Variant
Variant.parentVariant.eOpposite = Variant.variant
Variant.variantCollection.eType = VariantCollection
AbstractChange.variant.eType = Variant
AbstractChange.variant.eOpposite = Variant.change
VariantCollection.variant.eType = Variant
VariantCollection.variant.eOpposite = Variant.variantCollection

otherClassifiers = []

for classif in otherClassifiers:
    eClassifiers[classif.name] = classif
    classif.ePackage = eClass

for classif in eClassifiers.values():
    eClass.eClassifiers.append(classif.eClass)

for subpack in eSubpackages:
    eClass.eSubpackages.append(subpack.eClass)

register_packages = [esdlproject] + eSubpackages
for pack in register_packages:
    global_registry[pack.nsURI] = pack
