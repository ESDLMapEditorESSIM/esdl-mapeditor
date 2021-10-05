from src.shape import Shape
from esdl.esdl_handler import EnergySystemHandler

esh = EnergySystemHandler()
esh.load_file('Nesselande contour warmtenet.esdl')
# esh.load_file('Arnhem Schuytgraaf contour warmtenet.esdl')

es = esh.get_energy_system()
polygon = es.instance[0].area.area[0].geometry

shape = Shape.create(polygon)
print(shape.get_wkt())

