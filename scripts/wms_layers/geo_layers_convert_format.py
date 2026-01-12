import os
from osgeo import gdal
from dotenv import load_dotenv

load_dotenv()

STRINGS_TO_REPLACE = {
    "RO_STACKED": "permian",
    "TR_STACKED": "triassic",
    "SLDN_STACKED": "jurassic",
    "KN_STACKED": "cretaceous",
    "N_STACKED": "paleogene",
    "NLDOBR": "brussels",
    "msz2": "maassluis2",
    "msz3": "maassluis3",
    "msz4": "maassluis4",
    "ooz2": "oosterhout2",
    "_P50_basecase_80-45-40": "",
    "_basecase_80-45-40": "",
    "_ATES": "",
    "_P50": "",
    "__": "_",
}


def convert_from_netcdf_to_tif(folder_path):
    # Walk through the directory and its subdirectories
    for foldername, subfolders, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            # if filename.lower().endswith(("tif", ".xml")):
            #     os.remove(file_path)
            if filename.lower().endswith(".nc"):
                nc_dataset = gdal.Open(file_path)

                file_path = file_path.replace(".nc", ".tif")
                for str_old, str_new in STRINGS_TO_REPLACE.items():
                    file_path = file_path.replace(str_old, str_new)
                if os.path.exists(file_path):
                    os.remove(file_path)
                # Write out as GeoTIFF
                gdal.Translate(file_path, nc_dataset, format="GTiff")
                print(f"Created file: {file_path}")


if __name__ == "__main__":
    convert_from_netcdf_to_tif(os.environ.get("FOLDER_PATH"))
