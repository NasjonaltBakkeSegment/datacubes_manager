import os
import re
import argparse
from datacube import Datacube

def process_directory(ncml_base_path, nc_root_dir):
    '''
    Traverse a directory for .nc files, and add each to its corresponding NCML file.

    Parameters:
        nc_root_dir (str): Root directory to search for .nc files.
        ncml_base_path (str): Base path under which NCML files are stored.
    '''
    for dirpath, _, filenames in os.walk(nc_root_dir):
        for filename in filenames:
            if not filename.endswith(".nc"):
                continue

            nc_path = os.path.join(dirpath, filename)

            # Extract tile with leading 'T', e.g. 'T31UFT'
            tile_match = re.search(r"(T\d{2}[A-Z]{3})", filename)
            if not tile_match:
                print(f"Could not find tile in filename: {filename}")
                continue
            tile = tile_match.group(1)

            # Extract date string in format YYYYMMDD
            date_match = re.search(r"(\d{8})T", filename)
            if not date_match:
                print(f"Could not find date in filename: {filename}")
                continue
            year = date_match.group(1)[:4]

            # Build NCML path
            ncml_path = os.path.join(ncml_base_path, tile, year, f"dc_{year}_{tile}.ncml")

            # Ensure directory exists
            os.makedirs(os.path.dirname(ncml_path), exist_ok=True)

            # Add product to datacube
            cube = Datacube(ncml_path)
            cube.add_product(nc_path)
            print(f"Added {nc_path} to {ncml_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process .nc files into NCML structure.")
    parser.add_argument("ncml_base_path", help="Base path for NCML files.")
    parser.add_argument("nc_root_dir", help="Root directory to search for .nc files.")

    args = parser.parse_args()

    process_directory(args.ncml_base_path, args.nc_root_dir)