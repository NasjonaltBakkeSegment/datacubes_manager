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

def find_safe_files_from_given_tileNproductlevel_within_time_interval(directories, search_string_tile, search_string_productlevel):
    """
    Searches for files in the given directories whose filenames contain the specified string.

    :param directories: List of directory paths to search in
    :param search_string_tile: Tile string to look for in filenames
    :param search_string_productlevel: Product level to look for in filenames
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
                if search_string_tile in file and search_string_productlevel in file:
                    # Construct the full file path
                    full_path = os.path.join(root, file)
                    matching_file_paths.append(full_path)
    
    return matching_file_paths


import glob

def create_ncml_with_aggregation(nc_files, output_ncml, dim_name="time", aggregation_type="joinExisting"):
    """
    Create an NcML file with an aggregation structure for given NetCDF files.

    Parameters:
        nc_files (list): List of paths to NetCDF files to include in the NcML file.
        output_ncml (str): Path to save the output .ncml file.
        dim_name (str): Dimension name for aggregation (default is "time").
        aggregation_type (str): Aggregation type (default is "joinExisting").
    """
    # Start the NcML structure
    ncml_content = f"""<?xml version='1.0' encoding='UTF-8'?>
<netcdf xmlns="http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2">
  <aggregation dimName="{dim_name}" type="{aggregation_type}">
"""

    # Add each NetCDF file to the aggregation
    for nc_file in nc_files:
        # Ensure file paths are absolute
        nc_file = os.path.abspath(nc_file)
        ncml_content += f'    <netcdf location="{nc_file}" ncoords="1"/>\n'

    # Close the NcML structure
    ncml_content += """  </aggregation>
</netcdf>
"""

    # Save the NcML content to the output file
    with open(output_ncml, "w") as f:
        f.write(ncml_content)
    print(f"NcML file created: {output_ncml}")

    return


import xml.etree.ElementTree as ET

def compare_ncml_files(file1, file2):
    """
    Compares two NcML files to check if they are completely identical.
    
    Parameters:
        file1 (str): Path to the first NcML file.
        file2 (str): Path to the second NcML file.
    
    Returns:
        bool: True if the files are identical, False otherwise.
    """
    try:
        # Parse both NcML files into XML trees
        tree1 = ET.parse(file1)
        tree2 = ET.parse(file2)
        
        # Convert the trees to normalized strings for comparison
        root1 = ET.tostring(tree1.getroot(), encoding='unicode')
        root2 = ET.tostring(tree2.getroot(), encoding='unicode')
        
        # Compare the strings
        return root1 == root2
    except Exception as e:
        print(f"Error comparing files: {e}")
        return False


from pathlib import Path
# from subprocess import call
import subprocess
from datacube import Datacube

def checkNcreate_netcdfNdatacubes(products, path2safe_catalog, path2dedicated_datacubes_on_demand, path2safe_to_netcdf, netcdf_creator_file, root_path, product_type, start_sensing_date, end_sensing_date):
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

    paths2each_single_ncfile_within_a_datacube = []

    # Iterate over the list of products
    for product in products:
        product_path = product.strip()        # Remove leading/trailing whitespace (if any)
        product_file = product.split("/")[-1] # Only extract filename 
        # Skip empty strings
        if not product_file:
            continue

        # 2. Create variable 'zip_product' replacing .SAFE with .zip
        zip_product = product_file#.replace(".SAFE", ".zip")
        nc_product = product_file.replace(".zip", ".nc")

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
        #nc_filepath = Path(path2dedicated_datacubes_on_demand) / product_level / tile
        

        temp_nc_storage_path = Path(root_path) / product_level / tile
        nc_filepath = temp_nc_storage_path

        if not os.path.exists(nc_filepath) or not os.path.isdir(nc_filepath):
            print(f"The directory '{nc_filepath}' does not exist. Creating it...")
            os.makedirs(nc_filepath)  # Create the directory

        nc_file = Path(nc_filepath) / nc_product


        # path2safe_to_netcdf = "/home/josteines/src/NBS/safe_to_netcdf"
        # netcdf_creator_file = "run_sentinel_data_converter.py"

        sentinel_converter_path = Path(path2safe_to_netcdf) / netcdf_creator_file

        # Build the command to run the external script
        command = [
            "python3",  # Or "python", depending on your setup
            sentinel_converter_path,
            "--input_filepath", product_path,
            "--output", nc_filepath,
            ]

        # 6. Check existence and existance of netCDF
        if zip_filepath.is_file():
            print(f"Safe exists: {zip_filepath}")
            found += 1

            if not nc_file.is_file():
                
                try:
                    result = subprocess.run(command, check=True, text=True, capture_output=True)
                    print("Script output:")
                    print(result.stdout)  # Print the output of the external script
                except subprocess.CalledProcessError as e:
                    print("Error occurred while running the script:")
                    print(e.stderr)
                print(f'{nc_file} does not exist! Creating this.')
                found_but_no_nc += 1
            else:
                print(f'{nc_file} exists! Moving on.')


        
        else:
            print(f"Missing: {zip_filepath}")
            missing += 1

        # Keep all nc paths in a list 
        paths2each_single_ncfile_within_a_datacube.append(str(nc_file))

        print('\n')

    # Print stats
    print("\n=== Summary ===")
    print(f"Found normal: {found}")
    print(f"Files lacking netCDF: {found_but_no_nc}")
    print(f"Missing: {missing}")
    print(f"Total processed: {found + missing}. Have made {found_but_no_nc} netCDF files that were lacking for the datacube on demand.")

    print(paths2each_single_ncfile_within_a_datacube)
    print('\n')


    # This is the nc_filepath
    # base_path="/lustre/storeB/project/NBS2/sentinel/production/NorwAREA/NetCDF-ondemand-products/datacubes/L2A/T32VPM"

    # path to datacubes on demand where nc products and datacubes are saved under product level and tile
    # path2dedicated_datacubes_on_demand = Path(path2dedicated_datacubes_on_demand) # = /lustre/storeB/project/NBS2/sentinel/production/NorwAREA/NetCDF-ondemand-products/datacubes
    path2dedicated_datacubes_on_demand = Path(root_path) / product_level / tile

    p = Path(path2dedicated_datacubes_on_demand)
    for file_path in p.iterdir():
        if file_path.is_file():
            print(file_path.name) # Prints only the file name
            # To get the full path, use:
            # print(file_path)

    # 1. Loop through all .nc files in base_path
    nc_files = glob.glob(os.path.join(nc_filepath, "*.nc"))
    # print(nc_files)
    print(paths2each_single_ncfile_within_a_datacube)

    # for netcdf_filepath in paths2each_single_ncfile_within_a_datacube:#nc_files:
    #     '''
    #     # 2. Extract year from filename (e.g. S2C_MSIL2A_20250312T103851_...)
    #     filename = os.path.basename(netcdf_filepath)
        
    #     # Assuming the date is always in the format YYYYMMDD starting at position 11
    #     # (adjust index if your filenames differ)
    #     date_str = filename.split('_')[2]  # '20250312T103851'
    #     year = date_str[:4]  # '2025'
    #     '''
    #     date_str_start = start_sensing_date.replace('/','')
    #     date_str_end = end_sensing_date.replace('/','')

    #     path2spesific_datacubes_folder = Path(path2dedicated_datacubes_on_demand) / 'datacubes'

    #     # Create datacubes folder if not excisting
    #     if not os.path.exists(path2spesific_datacubes_folder) or not os.path.isdir(path2spesific_datacubes_folder):
    #         print(f"The directory '{path2spesific_datacubes_folder}' does not exist. Creating it...")
    #         os.makedirs(path2spesific_datacubes_folder)  # Create the directory

    #     # 3. Create filepath for datacube (base_path/S2_L2A_T32VNM_YEAR.ncml)
    #     datacube_filename = f"{product_type}_{product_level}_{tile}_{date_str_start}_{date_str_end}.ncml"
    #     datacube_filepath = os.path.join(path2spesific_datacubes_folder, datacube_filename)
    #     print(datacube_filepath)

    #     # # 4. Initialise with path to NCML file 
    #     # cube = Datacube(datacube_filepath, dim_name="time", agg_type="joinExisting")

    #     # # 5. Add netcdf file to datacube
    #     # cube.add_product(netcdf_filepath)

    '''
    # 2. Extract year from filename (e.g. S2C_MSIL2A_20250312T103851_...)
    filename = os.path.basename(netcdf_filepath)
    
    # Assuming the date is always in the format YYYYMMDD starting at position 11
    # (adjust index if your filenames differ)
    date_str = filename.split('_')[2]  # '20250312T103851'
    year = date_str[:4]  # '2025'
    '''
    date_str_start = start_sensing_date.replace('/','')
    date_str_end = end_sensing_date.replace('/','')

    print(f'The date_str_start = {date_str_start} and the date_end_str = {date_str_end} for the current datacube.')

    path2spesific_datacubes_folder = Path(path2dedicated_datacubes_on_demand) / 'datacubes'

    # Create datacubes folder if not excisting
    if not os.path.exists(path2spesific_datacubes_folder) or not os.path.isdir(path2spesific_datacubes_folder):
        print(f"The directory '{path2spesific_datacubes_folder}' does not exist. Creating it...")
        os.makedirs(path2spesific_datacubes_folder)  # Create the directory

    else:
        print(f"The directory '{path2spesific_datacubes_folder}' does exist.")

    # 3. Create filepath for datacube (base_path/S2_L2A_T32VNM_YEAR.ncml)
    datacube_filename = f"{product_type}_{product_level}_{tile}_{date_str_start}_{date_str_end}.ncml"
    datacube_filepath = os.path.join(path2spesific_datacubes_folder, datacube_filename)
    print(datacube_filepath)


    new_datacube_filename = f"new_{product_type}_{product_level}_{tile}_{date_str_start}_{date_str_end}.ncml"
    new_datacube_filepath = os.path.join(path2spesific_datacubes_folder, new_datacube_filename)
    print(new_datacube_filepath)

    # Check if the new datacube is identical to eventual old datacube
    if Path(datacube_filepath).is_file():
        print(f'The datacube {datacube_filename} already exist. Creating a new one and checking if they are identical.')

        create_ncml_with_aggregation(nc_files = paths2each_single_ncfile_within_a_datacube, 
                              output_ncml = new_datacube_filepath
                              )

        if compare_ncml_files(datacube_filepath, new_datacube_filepath) == False:

            try:
                # 1. Remove the file
                os.remove(datacube_filepath)
                print(f"Removed the outdated '{datacube_filepath}' successfully.")

                # 2. Rename the other file to the removed file's name
                # The 'new name' in os.rename() will be the path/name of the file that was just removed
                os.rename(new_datacube_filepath, datacube_filepath)
                print(f"Renamed '{new_datacube_filepath}' to '{datacube_filepath}' successfully.")

            except FileNotFoundError as e:
                print(f"Error: One of the files was not found. {e}")
            except OSError as e:
                # Handles permissions errors or other general OS errors
                print(f"Error with file operation: {e}")

        else:
            print(f"There are no differences between the datacubes. {datacube_filepath} is kept as it is and {new_datacube_filepath} is removed.")

            # Remove the newly created datacube as it is identical to the old one
            os.remove(new_datacube_filepath)

    else:
        print(f'The datacube {datacube_filename} did not exist. Creating it...')

        create_ncml_with_aggregation(nc_files = paths2each_single_ncfile_within_a_datacube, 
                              output_ncml = datacube_filepath
                              )



    return
