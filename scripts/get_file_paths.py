#  This work is based on original code developed and copyrighted by TNO 2023.
#  Subsequent contributions are licensed to you by the developers of such code and are
#  made available to the Project under one or several contributor license agreements.
#
#  This work is licensed to you under the Apache License, Version 2.0.
#  You may obtain a copy of the license at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Contributors:
#      TNO         - Initial implementation
#  Manager:
#      TNO
import csv
import os
from dotenv import load_dotenv

load_dotenv()


def get_file_paths(folder_path, allowed_extensions=None):
    paths = []

    # If file_extensions is None, include all file types
    if allowed_extensions is None:
        allowed_extensions = set()

    # Walk through the directory and its subdirectories
    for foldername, subfolders, filenames in os.walk(folder_path):
        for filename in filenames:
            # Check if the file has allowed extension
            if not allowed_extensions or filename.lower().endswith(allowed_extensions):
                file_path = os.path.join(foldername, filename)
                paths.append(file_path)

    return paths


def write_to_file(paths, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        for file_path in paths:
            csv_writer.writerow([file_path, 'sld file path here to avoid auto style'])


if __name__ == "__main__":
    file_paths = get_file_paths(os.environ.get('FOLDER_PATH'),
                                allowed_extensions=tuple(os.environ.get('ALLOWED_EXTENSIONS').replace(" ", "").split(",")))
    write_to_file(file_paths, os.environ.get('LIST_TO_IMPORT_FILE'))
    print(f"File paths written to '{os.environ.get('LIST_TO_IMPORT_FILE')}'")
