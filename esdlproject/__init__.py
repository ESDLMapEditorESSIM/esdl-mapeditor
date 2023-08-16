from pyecore.resources import global_registry
from .esdlproject import getEClassifier, eClassifiers
from .esdlproject import name, nsURI, nsPrefix, eClass
from .esdlproject import ESDLProject, Variant, AbstractChange, HighLevelChange, DetailedChange, Set, Delete, Move, Add, Remove, EnergySystemProxy

from esdl import EnergySystem
from pyecore.ecore import EObject

from . import esdlproject

__all__ = ['ESDLProject', 'Variant', 'AbstractChange', 'HighLevelChange',
           'DetailedChange', 'Set', 'Delete', 'Move', 'Add', 'Remove', 'EnergySystemProxy']

eSubpackages = []
eSuperPackage = None
esdlproject.eSubpackages = eSubpackages
esdlproject.eSuperPackage = eSuperPackage

ESDLProject.proxy.eType = EnergySystemProxy
Variant.snapshot.eType = EnergySystem
Variant.snapshotRef.eType = EnergySystem
Variant.lastProcessedChange.eType = AbstractChange
HighLevelChange.change.eType = DetailedChange
DetailedChange.owner.eType = EObject
DetailedChange.objectValue.eType = EObject
DetailedChange.objectReference.eType = EObject
EnergySystemProxy.energysystem.eType = EnergySystem
EnergySystemProxy.energysystemRef.eType = EnergySystem
Variant.change.eType = AbstractChange
Variant.variant.eType = Variant
Variant.parentVariant.eType = Variant
Variant.parentVariant.eOpposite = Variant.variant
Variant.energySystemProxy.eType = EnergySystemProxy
AbstractChange.variant.eType = Variant
AbstractChange.variant.eOpposite = Variant.change
EnergySystemProxy.variant.eType = Variant
EnergySystemProxy.variant.eOpposite = Variant.energySystemProxy

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
