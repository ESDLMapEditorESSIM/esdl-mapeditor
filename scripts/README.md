# Scripts
Copy the `.env-template` to `.env` and update

## Load geospatial data in geoserver and add as wms layers
```
sudo apt install postgis
```
````postgresql
CREATE EXTENSION postgis_raster;
````

1. Run `get_file_paths.py`  
This will result in a .csvfile with a geospatial datafile per line.  
Insert .sld file paths for custom styling.
Remove the lines you don't want to load for the next step.  

2. Run `load_wms_layers.py`, update PARAM_FILE
This will load the geospatial files in postgis and geoserver. And it will add the layers to the specified project in the ME mongo settings, including the folder tree.

