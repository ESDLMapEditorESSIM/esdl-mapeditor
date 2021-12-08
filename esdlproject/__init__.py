from pyecore.resources import global_registry
from .esdlproject import getEClassifier, eClassifiers
from .esdlproject import name, nsURI, nsPrefix, eClass
from .esdlproject import ESDLProject, Variant, AbstractChange, HighLevelChange, DetailedChange, Set, Delete, Move, Add, Remove, BaseVariant

from esdl import EnergySystem
from pyecore.ecore import EObject

from . import esdlproject

__all__ = ['ESDLProject', 'Variant', 'AbstractChange', 'HighLevelChange',
           'DetailedChange', 'Set', 'Delete', 'Move', 'Add', 'Remove', 'BaseVariant']

eSubpackages = []
eSuperPackage = None
esdlproject.eSubpackages = eSubpackages
esdlproject.eSuperPackage = eSuperPackage

ESDLProject.baseVariant.eType = BaseVariant
Variant.snapshot.eType = EnergySystem
Variant.snapshotRef.eType = EnergySystem
HighLevelChange.change.eType = DetailedChange
DetailedChange.owner.eType = EObject
DetailedChange.objectValue.eType = EObject
DetailedChange.objectReference.eType = EObject
BaseVariant.energysystem.eType = EnergySystem
BaseVariant.energysystemRef.eType = EnergySystem
Variant.change.eType = AbstractChange
Variant.variant.eType = Variant
Variant.parentVariant.eType = Variant
Variant.parentVariant.eOpposite = Variant.variant
Variant.baseVariant.eType = BaseVariant
AbstractChange.variant.eType = Variant
AbstractChange.variant.eOpposite = Variant.change
BaseVariant.variant.eType = Variant
BaseVariant.variant.eOpposite = Variant.baseVariant

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
