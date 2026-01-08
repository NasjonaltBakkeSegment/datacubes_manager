import ast

def read_config_file(file_path):
    """
    Reads a configuration file where each line contains a variable and its content in the format:
    variable: content

    :param file_path: Path to the configuration file
    :return: Dictionary with variable names as keys and their content as values
    """
    config = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                # Strip any leading/trailing whitespace and ignore empty lines
                line = line.strip()
                # Skip empty lines or lines starting with '#'
                if not line or line.startswith('#'):
                    continue
                if line and ':' in line:  # Ensure the line contains a colon
                    # Split into variable and content, stripping extra spaces around them
                    variable, content = map(str.strip, line.split(':', 1))
                    
                    # Try to parse the content as a Python literal (e.g., a list, number, etc.)
                    try:
                        parsed_content = ast.literal_eval(content)
                    except (ValueError, SyntaxError):
                        # If parsing fails, keep the content as a string
                        parsed_content = content
                    
                    # Add the parsed variable and content to the dictionary
                    config[variable] = parsed_content
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
    
    return config





from datetime import datetime, timedelta

def generate_date_range(start_date, end_date):
    """
    Generate a list of all dates between start_date and end_date (inclusive) 
    in the format YYYY/MM/DD.

    :param start_date: Start date in the format YYYY/MM/DD
    :param end_date: End date in the format YYYY/MM/DD
    :return: List of dates in the format YYYY/MM/DD
    """
    # Parse the input dates
    start = datetime.strptime(start_date, "%Y/%m/%d")
    end = datetime.strptime(end_date, "%Y/%m/%d")
    
    # Generate a list of dates
    date_list = []
    current = start
    while current <= end:
        date_list.append(current.strftime("%Y/%m/%d"))
        current += timedelta(days=1)
    
    return date_list



import os

def find_safe_files_from_given_tile_within_time_interval(directories, search_string):
    """
    Searches for files in the given directories whose filenames contain the specified string.

    :param directories: List of directory paths to search in
    :param search_string: String to look for in filenames
    :return: List of complete file paths for files containing the search_string
    """
    matching_file_paths = []

    for directory in directories:
        # Ensure the directory exists
        if not os.path.isdir(directory):
            print(f"Warning: {directory} is not a valid directory. Skipping.")
            continue
        
        # Walk through the directory
        for root, _, files in os.walk(directory):
            for file in files:
                # Check if the filename contains the search string
                if search_string in file:
                    # Construct the full file path
                    full_path = os.path.join(root, file)
                    matching_file_paths.append(full_path)
    
    return matching_file_paths


#!/usr/bin/env python3

import os
from pathlib import Path
# from subprocess import call
import subprocess

def checkNcreate_netcdfNdatacubes(products, path2safe_catalog, path2dedicated_datacubes_on_demand, path2safe_to_netcdf, netcdf_creator_file, root_path):
    # # List of product names
    # products = [
    #     "S2A_MSIL2A_20150818T092006_N0500_R093_T37WDP_20231012T115416.SAFE",
    #     "S2A_MSIL2A_20150818T110046_N0500_R094_T34WDB_20231009T195950.SAFE",
    #     "S2C_MSIL2A_20251028T104151_N0511_R008_T32VPM_20251028T135916.SAFE",
    #     # Add more product names here...
    # ]

    # # Base path
    # path2safe_catalog = "/lustre/storeB/project/NBS2/sentinel/production/NorwAREA/nbsArchive/"
    # path2dedicated_datacubes_on_demand = "/lustre/storeB/project/NBS2/sentinel/production/NorwAREA/NetCDF-ondemand-products/datacubes"

    # Counters
    found = 0
    found_but_no_nc = 0
    missing = 0

    # Iterate over the list of products
    for product in products:
        product_path = product.strip()        # Remove leading/trailing whitespace (if any)
        product_file = product.split("/")[-1] # Only extract filename 
        # Skip empty strings
        if not product_file:
            continue

        # 2. Create variable 'zip_product' replacing .SAFE with .zip
        zip_product = product_file.replace(".SAFE", ".zip")
        nc_product = product_file.replace(".SAFE", ".nc")

        # 3. Extract year, month, and day (from the first date in the string, after 'MSIL2A_')
        datetime = product_file.split("_")[2]  # e.g., 20150818T110046
        year = datetime[:4]
        month = datetime[4:6]
        day = datetime[6:8]

        # 4. Platform short name (e.g. S2A), product level (e.g. L2A) and tile (e.g. T37WPD)
        platform = product_file.split("_")[0]
        product_level = product_file.split("_")[1][3:6]
        tile = product_file.split("_")[5]

        # 5. Build filepath
        zip_filepath = Path(path2safe_catalog) / platform / year / month / day / zip_product
        nc_filepath = Path(path2dedicated_datacubes_on_demand) / product_level / tile / nc_product

        temp_nc_storage_path = Path(root_path) / product_level / tile / nc_product

        # path2safe_to_netcdf = "/home/josteines/src/NBS/safe_to_netcdf"
        # netcdf_creator_file = "run_sentinel_data_converter.py"

        sentinel_converter_path = Path(path2safe_to_netcdf) / netcdf_creator_file

        # Build the command to run the external script
        command = [
            "python3",  # Or "python", depending on your setup
            sentinel_converter_path,
            "--input_filepath", product_path,
            "--output", temp_nc_storage_path,
            ]

        # 6. Check existence and existance of netCDF
        if zip_filepath.is_file():
            print(f"Safe exists: {zip_filepath}")
            found += 1
            # call(["qsub", "-V", "-b", "n", "create_netcdf.sh", str(filepath)])
            # if corresponding netCDF does not exist - create using subprocess and run_sentinel_converter.py in safe_to_netcdf
            # Place to check if netCDF is created: path2dedicated_datacubes_on_demand + product_level + tile (see config)
            if not nc_filepath.is_file():
                # Run the script with arguments
                # subprocess.run(["python", script_path = sentinel_converter_path, input_path = product_path, output_path = temp_nc_storage_path])#output_path = nc_filepath])
                # Run the command
                try:
                    result = subprocess.run(command, check=True, text=True, capture_output=True)
                    print("Script output:")
                    print(result.stdout)  # Print the output of the external script
                except subprocess.CalledProcessError as e:
                    print("Error occurred while running the script:")
                    print(e.stderr)
                print(f'{nc_filepath} does not exist! Creating this.')
                found_but_no_nc += 1
            else:
                print(f'{nc_filepath} exists! Moving on.')


        
        else:
            print(f"Missing: {zip_filepath}")
            missing += 1

        print('\n')

    # Print stats
    print("\n=== Summary ===")
    print(f"Found normal: {found}")
    print(f"Files lacking netCDF: {found_but_no_nc}")
    print(f"Missing: {missing}")
    print(f"Total processed: {found + missing}. Have made {found_but_no_nc} netCDF files that were lacking for the datacube on demand.")

    return