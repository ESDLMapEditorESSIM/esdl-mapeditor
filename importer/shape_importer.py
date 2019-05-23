import shapefile
import model.esdl_sup as esdl
from uuid import uuid4
from app import distance
from pyproj import Proj, Transformer

def read_shapefile(filename):
    sf = shapefile.Reader(filename)
    return sf

def to_esdl_pipes(area, sf, transformer):
    i = 0
    for shapeRecord in sf.shapeRecords():
        i += 1
        if shapeRecord.shape.shapeType == shapefile.POLYLINE:
            #print('{} {}m = {}'.format(shapeRecord.shape.shapeTypeName, shapeRecord.record[0], shapeRecord.shape.points))
            pipe = esdl.Pipe(name=area.get_name()+'-Pipe'+str(i), id=uuid4())
            line = esdl.Line()
            d = 0.0
            prevlat, prevlon = None, None
            for point in shapeRecord.shape.points:
                lon, lat = transformer.transform(point[0], point[1])
                p = esdl.Point(lat=lat, lon=lon)
                line.add_point(p)
                if prevlat is not None:
                    d = d + distance((prevlat, prevlon),(lat, lon))
                prevlat, prevlon = lat, lon
            pipe.set_length(d * 1000) # in m instead of km
            pipe.set_geometry_with_type(line)
            area.add_asset_with_type(pipe)


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
    es.add_instance(instance)
    area = esdl.Area(name='Main Area')
    instance.set_area(area)
    return es, area


def read_multiple_shapefiles(files, main_area, transformer) :
    for file in files:
        sf = read_shapefile(file)
        area_name = file[file.rfind('/') + 1:]
        print(file)
        print(sf)
        print(sf.fields)
        # print(sf.shapeRecords())

        shape_area = esdl.Area(name=area_name, id=uuid4())
        main_area.add_area(shape_area)

        to_esdl_pipes(shape_area, sf, transformer)


fileNames = [
    "C:/temp/Shapefiles_180419 Update WSW/Bestaande_infrastructuur",
    "C:/temp/Shapefiles_180419 Update WSW/Cluster_grens",
    "C:/temp/Shapefiles_180419 Update WSW/Cluster_Noordwest_geplande_concept",
    "C:/temp/Shapefiles_180419 Update WSW/Gemeentegrens",
    "C:/temp/Shapefiles_180419 Update WSW/Koppeling_Trias",
    "C:/temp/Shapefiles_180419 Update WSW/Primair_net",
    "C:/temp/Shapefiles_180419 Update WSW/Regionaalnet",
    "C:/temp/Shapefiles_180419 Update WSW/Trias_gepland_definitief"
]
def main():


    es, main_area = create_energy_system()
    transformer = get_coordinate_transformer()

    read_multiple_shapefiles(fileNames, main_area, transformer)


    exportFile = 'westland.esdl'
    f = open(exportFile, 'w+', encoding='UTF-8')
    # f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    xml_namespace = ('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\nxmlns:esdl="http://www.tno.nl/esdl"\n')
    es.export(f, 0, namespaceprefix_='esdl:', name_='esdl:EnergySystem', namespacedef_=xml_namespace, pretty_print=True)


if __name__ == '__main__':
    main()