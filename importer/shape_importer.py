import shapefile
import esdl.esdl as esdl
from pyecore.ecore import EClass, EObject, EStructuralFeature
from uuid import uuid4
from esdl.processing.ESDLGeometry import distance
from pyproj import Proj, Transformer
from esdl.esdl_handler import EnergySystemHandler


inner_diameter_keys = ('inner diam', 'diameter', 'inner diameter', 'innerdiameter')
outer_diameter_keys = ('outer diam', 'diameter', 'outer diameter', 'outerdiameter')
name_keys = ('name', 'naam')



def read_shapefile(filename):
    sf = shapefile.Reader(filename)
    return sf

def to_esdl(area, sf, transformer):
    i = 0
    for shapeRecord in sf.shapeRecords():
        i += 1
        if shapeRecord.shape.shapeType == shapefile.POLYLINE:
            print('{} {} = {}'.format(shapeRecord.shape.shapeTypeName, shapeRecord.record[0], shapeRecord.shape.points))
            pipe = esdl.Pipe(name=area.name+'-Pipe'+str(i), id=str(uuid4()))
            line = esdl.Line()
            d = 0.0
            prevlat, prevlon = None, None
            for point in shapeRecord.shape.points:
                lon, lat = transformer.transform(point[0], point[1])
                p = esdl.Point(lat=lat, lon=lon)
                line.point.append(p)
                if prevlat is not None:
                    d = d + distance((prevlat, prevlon),(lat, lon))
                prevlat, prevlon = lat, lon
            pipe.length = d * 1000 # in m instead of km

            # diameter was put in mm!
            pipe.innerDiameter = float(get_recordproperty(shapeRecord.record, inner_diameter_keys, 0.0))/1000
            pipe.outerDiameter = float(get_recordproperty(shapeRecord.record, outer_diameter_keys, 0.0))/1000

            pipe.geometry = line
            inport = esdl.InPort(id=str(uuid4()), name='InPort')
            outport = esdl.OutPort(id=str(uuid4()), name='OutPort')
            pipe.port.extend((inport, outport))
            area.asset.append(pipe)

        if shapeRecord.shape.shapeType == shapefile.POINT:
            # probably an asset
            esdl_type = get_type(shapeRecord.record)
            esdl_instance = esdl_type(name=get_name(shapeRecord.record), id=str(uuid4()))
            #instance = esdl.GenericProducer(name=get_name(shapeRecord.record), id=str(uuid4()))
            point = shapeRecord.shape.points[0]
            lon, lat = transformer.transform(point[0], point[1])
            p = esdl.Point(lat=lat, lon=lon)
            esdl_instance.geometry = p
            area.asset.append(esdl_instance)
            inport = esdl.InPort(id=str(uuid4()), name='InPort')
            outport = esdl.OutPort(id=str(uuid4()), name='OutPort')
            esdl_instance.port.extend((inport,outport))


"""
if the shape record contains the type field, use that to find 
the appropriate ESDL class
"""
def get_type(record: shapefile._Record):
    record_dict = record.as_dict()
    for key, value in record_dict.items():
        if 'type' == key.lower():
            for esdl_type in esdl.eClassifiers:
                t: EClass = esdl.getEClassifier(esdl_type).eClass
                if esdl.EnergyAsset.eClass in t.eAllSuperTypes():
                    #print('checking', esdl_type)
                    if value.lower() in esdl_type.lower():
                        print('Using {} as type for this shape'.format(esdl_type))
                        return esdl.getEClassifier(esdl_type)
    return esdl.GenericProducer

def get_name(record: shapefile._Record):
    record_dict = record.as_dict()

    for key, value in record_dict.items():
        if key.lower() in name_keys:
            return value
    return "unnamed"

def get_recordproperty(record: shapefile._Record, possible_names: list, default_value=None):
    record_dict = record.as_dict()
    for key, value in record_dict.items():
        if key.lower() in possible_names:
            return value
    return default_value

# TODO: generic approach for properties
# def set_recordproperty(eobject:EObject, attribute: str, record: shapefile._Record, possible_names: list=None, default_value=None):
#     feature: EStructuralFeature = eobject.eClass.findEStructuralFeature(attribute)
#
#     if possible_names is None:
#
#     record_dict = record.as_dict()
#     for key, value in record_dict.items():
#         if key.lower() in possible_names:
#             return value
#     return default_value

'''
Returns a transformer to transform coodinate systems
Dutch transformations are usually based on Amersfoort/ RD New (EPSG 28992)
Input is then x,y coordinates
Output transformation is by default EPSG 4326 / WGS 82 that outputs lon,lat coordinates based on the whole earth. 
Optionally a wkt string can be given in as an input projection, read from the shape file.prj file.
'''
def get_coordinate_transformer(wkt=None, epsg_in="epsg:28992", epsg_out="epsg:4326"):
    # wkt = 'PROJCS["RD_New",GEOGCS["GCS_Amersfoort",DATUM["D_Amersfoort",SPHEROID["Bessel_1841",6377397.155,299.1528128]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Double_Stereographic"],PARAMETER["False_Easting",155000.0],PARAMETER["False_Northing",463000.0],PARAMETER["Central_Meridian",5.38763888888889],PARAMETER["Scale_Factor",0.9999079],PARAMETER["Latitude_Of_Origin",52.15616055555555],UNIT["Meter",1.0]]'
    # projection = Proj(projparams=wkt)
    projectionIn = None
    if wkt is not None:
        projectionIn = Proj(projparams=wkt)
    else:
        # default input projection
        projectionIn = Proj(init=epsg_in)
    projectionOut = Proj(init=epsg_out)
    transformer = Transformer.from_proj(proj_from=projectionIn, proj_to=projectionOut)
    return transformer

def create_energy_system():
    es = esdl.EnergySystem(name="Imported Shapefile EnergySystem", id=uuid4())
    instance = esdl.Instance(name="Instance", id=uuid4())
    es.instance.append(instance)
    area = esdl.Area(name='Main Area', id=str(uuid4()))
    instance.area = area
    return es, area


def read_multiple_shapefiles(files, main_area, transformer) :
    for file in files:
        sf = read_shapefile(file)
        with open(file+'.prj', 'r') as project_file:
            data = project_file.read()
            transformer = get_coordinate_transformer(wkt=data)

        area_name = file[file.rfind('/') + 1:]
        print("File: ", file)
        print("- Shapefile: ", sf)
        print("- Fields: ", sf.fields)
        print("- Shaperecords: ", sf.shapeRecords())

        shape_area = esdl.Area(name=area_name, id=str(uuid4()))
        main_area.area.append(shape_area)

        to_esdl(shape_area, sf, transformer)


# fileNames = [
#     "C:/temp/Shapefiles_180419 Update WSW/Bestaande_infrastructuur",
#     "C:/temp/Shapefiles_180419 Update WSW/Cluster_grens",
#     "C:/temp/Shapefiles_180419 Update WSW/Cluster_Noordwest_geplande_concept",
#     "C:/temp/Shapefiles_180419 Update WSW/Gemeentegrens",
#     "C:/temp/Shapefiles_180419 Update WSW/Koppeling_Trias",
#     "C:/temp/Shapefiles_180419 Update WSW/Primair_net",
#     "C:/temp/Shapefiles_180419 Update WSW/Regionaalnet",
#     "C:/temp/Shapefiles_180419 Update WSW/Trias_gepland_definitief"
# ]

fileNames = [
    "C:/temp/test_systeem/pipelines",
    "C:/temp/test_systeem/sources",
    "C:/temp/test_systeem/sources2",
]


def main():
    esh = EnergySystemHandler()
    es = esh.create_empty_energy_system("Imported EnergySystem", "", "Instance", "Main Area")
    main_area = es.instance[0].area
    transformer = get_coordinate_transformer()

    read_multiple_shapefiles(fileNames, main_area, transformer)
    print(esh.to_string())
    exportFile = 'exported_es.esdl'
    esh.save_as(exportFile)


if __name__ == '__main__':
    main()
