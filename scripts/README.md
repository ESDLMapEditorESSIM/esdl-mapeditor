# Scripts

Install `requirements.txt` in this folder on top of the MapEditor requirements (these are not necessary for the
MapEditor itself).  
Copy the `.env-template` to `.env` and update the values.

## Load geospatial data in geoserver and add as wms layers

1. Run `get_file_paths.py`  
   This will result in a .csvfile with a geospatial datafile per line.  
   Optionally insert .sld file paths for custom styling. Raster file colors will be auto scaled by default.  
   Remove the lines you don't want to load in the next step.

2. Run `load_wms_layers.py`  
   This will load the geospatial files in postgis and geoserver.  
   And it will add the layers to the specified project in
   the ME mongo settings, including the folder tree.
