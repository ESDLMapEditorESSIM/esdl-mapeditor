import os
from osgeo import gdal
from dotenv import load_dotenv

load_dotenv()


def convert_from_netcdf_to_tif(folder_path):
    # Walk through the directory and its subdirectories
    for foldername, subfolders, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            if filename.lower().endswith(".nc"):
                nc_dataset = gdal.Open(file_path)

                file_path = file_path.replace(".nc", ".tif")
                if os.path.exists(file_path):
                    os.remove(file_path)
                # Write out as GeoTIFF
                gdal.Translate(file_path, nc_dataset, format="GTiff")
                print(f"Created file: {file_path}")


if __name__ == "__main__":
    convert_from_netcdf_to_tif(os.environ.get("FOLDER_PATH"))
