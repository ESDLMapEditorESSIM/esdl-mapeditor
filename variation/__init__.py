from pyecore.resources import global_registry
from .variation import getEClassifier, eClassifiers
from .variation import name, nsURI, nsPrefix, eClass
from .variation import Project, Variant, AbstractChange, HighLevelChange, DetailedChange, Set, Delete, Move, Add, Remove

from pyecore.ecore import EObject
from esdl import EnergySystem

from . import variation

__all__ = ['Project', 'Variant', 'AbstractChange', 'HighLevelChange',
           'DetailedChange', 'Set', 'Delete', 'Move', 'Add', 'Remove']

eSubpackages = []
eSuperPackage = None
variation.eSubpackages = eSubpackages
variation.eSuperPackage = eSuperPackage

Project.variants.eType = Variant
Variant.snapshot.eType = EnergySystem
HighLevelChange.changes.eType = DetailedChange
DetailedChange.owner.eType = EObject
DetailedChange.objectValue.eType = EObject
DetailedChange.objectReference.eType = EObject
Variant.changes.eType = AbstractChange
Variant.variant.eType = Variant
Variant.parentVariant.eType = Variant
Variant.parentVariant.eOpposite = Variant.variant
AbstractChange.variant.eType = Variant
AbstractChange.variant.eOpposite = Variant.changes

otherClassifiers = []

for classif in otherClassifiers:
    eClassifiers[classif.name] = classif
    classif.ePackage = eClass

for classif in eClassifiers.values():
    eClass.eClassifiers.append(classif.eClass)

for subpack in eSubpackages:
    eClass.eSubpackages.append(subpack.eClass)

register_packages = [variation] + eSubpackages
for pack in register_packages:
    global_registry[pack.nsURI] = pack
