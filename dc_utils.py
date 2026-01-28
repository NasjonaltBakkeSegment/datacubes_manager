import os

def get_script_root_path():
    # Get the absolute path of the script and then extract the directory
    return os.path.dirname(os.path.abspath(__file__))

# Example usage
root_path = get_script_root_path()
print("Root path:", root_path)


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


'''
from cdsetool.query import query_features
from datetime import date, datetime
from cdsetool.query import describe_collection

def queryCDSE4products_based_on_tile_and_product_level(date_from, date_to, tile_id, product_level, collection = 'Sentinel2'):
    search_terms = describe_collection(collection).keys()
    print(search_terms)

    # Break apart the year, month and day from the start date
    date_from_year = date_from[:4]
    date_from_month = date_from[5:7]
    date_from_day = date_from[8:10]

    if date_from_month.startswith("0"):
        date_from_month = date_from_month[1:]
    if date_from_day.startswith("0"):
        date_from_day = date_from_day[1:]    

    start_date = date(int(date_from_year), int(date_from_month), int(date_from_day))

    # Break apart the year, month and day from the end date
    date_to_year = date_to[:4]
    date_to_month = date_to[5:7]
    date_to_day = date_to[8:10]

    if date_to_month.startswith("0"):
        date_to_month = date_to_month[1:]
    if date_to_day.startswith("0"):
        date_to_day = date_to_day[1:]


    end_date = date(int(date_to_year), int(date_to_month), int(date_to_day))
    



    #tile_ids = ["32VPM"]# ["32VNM"]
    # tile_ids = ["32VNM"]

    # tile_ids=["33WXT",
    # "33WXS",
    # "33WWT",
    # "33WWS",
    # "32VKN",
    # "32VKM",
    # "32VLN",
    # "32VLM",
    # "32VNN",
    # "32VPN",
    # "32VNP"]


    #for tile_id in tile_ids:
    features = query_features(collection, 
                            {"tileId": tile_id, 
                            "startDate": start_date, 
                            "completionDate": end_date,
                            # "processingLevel":"S2MSI2A"
                            # "processingLevel":"S2MSI1C"
                            "processingLevel":f"S2MSI{product_level[1:]}"
                            },
                            )
    print(product_level[1:])
    output = list(features)
    print('output:')
    print(output[0], '\n')

    titles = [output[i]['properties']['title'] for i in range(len(output))]

    # print('titles')
    # print(titles,'\n')
    print(f'There are {len(titles)} products found!', '\n')

    product_level_products = []
    for tit in titles:
        if product_level in tit:
            product_level_products.append(tit)

    print(f'There are {len(product_level_products)} {product_level} products among the query reesults')

    # with open(f's2_L2A_{tile_id}_products.txt','w') as outfile:
    #     for tit in titles:
    #         outfile.write(tit + '\n')
    return


queryCDSE4products_based_on_tile_and_product_level(date_from = '2017/01/01', date_to = '2024/12/31', tile_id = 'T33WXT'[1:], product_level = 'L2A') 
'''



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


import xarray as xr

def check_ds4certain_variable(path2nc, variable):
    ds = xr.open_dataset(path2nc)

    if variable in ds:
        ds.close()
        return True
    else:
        ds.close()
        return False
    
    
# def check_ds4certain_global_attribute(path2nc, global_attribute):
#     ds = xr.open_dataset(path2nc)

#     if global_attribute in ds.attrs:
#         ds.close()
#         return True
#     else:
#         ds.close()
#         return False

# def extract_cloud_coverage_from_global_attrs_and_assign_it_as_a_variable(dataset, path2output_ncfile):

#     # Extract the global attribute 'cloud_coverage'
#     cloud_coverage_value = dataset.attrs.get('cloud_coverage', None)

#     if cloud_coverage_value is not None:
#         # Extract the existing time coordinate
#         if 'time' in dataset.coords:
#             time = dataset.coords['time']

#             # Create a new DataArray for the cloud_coverage variable
#             cloud_coverage = xr.DataArray(
#                 data=[cloud_coverage_value],  # The value of the cloud coverage
#                 dims=['time'],  # Dimension name
#                 coords={'time': time},  # Use the existing time coordinate
#                 attrs={
#                     'units': '1',  # Unit of the variable
#                     'standard_name': 'cloud_area_fraction',  # CF convention standard name
#                     'long_name': 'Integrated percentage cloud cover for all pixel values.',  # Description
#                 },
#             ).astype('float32')

#             # Add the new variable to the dataset
#             dataset['cloud_coverage'] = cloud_coverage

#             # Save the updated dataset back to the netCDF file (optional)
#             dataset.to_netcdf(path2output_ncfile)  # Replace with your desired output file name

#             # Print the new variable to check
#             print(dataset.cloud_coverage)

#         else:
#             print("The dataset does not have a 'time' coordinate.")
#     else:
#         print("The global attribute 'cloud_coverage' does not exist in the dataset.")
#     return

import glob

''' # Both functions made redundant by using Datacube functionality from datacube.py
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
#'''

import shutil
    
def remove_safe_folders(directory):
    """
    Remove folders ending with '.SAFE' from the specified directory.

    Parameters:
    directory (str): The path to the directory to search for '.SAFE' folders.
    """
    # Iterate through all items in the directory
    for item in os.listdir(directory):
        # Construct the full path of the item
        item_path = os.path.join(directory, item)
        
        # Check if the item is a directory and its name ends with '.SAFE'
        if os.path.isdir(item_path) and item.endswith(".SAFE"):
            print(f"Removing folder: {item_path}")
            # Remove the directory and all its contents
            shutil.rmtree(item_path)


from pathlib import Path
# from subprocess import call
import subprocess
from datacube import Datacube

import sys

# Save the original sys.path
original_sys_path = sys.path.copy()

# Get the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get the neighboring folder path (safe_to_netcdf)
neighboring_folder_path = os.path.join(current_dir, '..', 'safe_to_netcdf')

# Prepend the neighboring folder to sys.path to prioritize its utils.py
sys.path.insert(0, neighboring_folder_path)

# Import Sentinel2_reader_and_NetCDF_converter
from s2_reader_and_NetCDF_converter import Sentinel2_reader_and_NetCDF_converter

import utils
print(f"Using utils.py from: {utils.__file__}")

def createNetCDFfromSAFE(product_file, product, nc_filepath, nc_file):
    # try:
    #     result = subprocess.run(command, check=True, text=True, capture_output=True)
    #     print("Script output:")
    #     print(result.stdout)  # Print the output of the external script
    
    # Initialize the Sentinel2 reader and converter
    converter = Sentinel2_reader_and_NetCDF_converter(product=product_file.replace('.zip',''), # Filename without extension
                                                        indir=Path(product).parent,            # Path to parent folder of the product
                                                    outdir=nc_filepath)                     # Output directory of the NetCDF output file (the parent folder)
    # Perform the conversion if the SAFE file was read successfully
    if converter.read_ok:
        success = converter.write_to_NetCDF(nc_filepath, compression_level=4)
        if success:
            print(f"Conversion successful! NetCDF file saved in: {nc_file}")
        else:
            print("Conversion failed during NetCDF writing.")
    else:
        print("Failed to read the SAFE file. Please check the input file.")

    # except subprocess.CalledProcessError as e:
    #     print("Error occurred while running the script:")
    #     print(e.stderr)
    print(f'{nc_file} does not exist! Creating this.')

    return


def checkNcreate_netcdfNdatacubes(products, path2safe_catalog, path2dedicated_datacubes_on_demand, path2safe_to_netcdf, netcdf_creator_file, root_path, product_type, start_sensing_date, end_sensing_date, path2second_chance_netcdf):

    # Counters
    found = 0
    found_but_no_nc = 0
    missing = 0
    failed = 0

    paths2each_single_ncfile_within_a_datacube = []

    # Initialize an empty dictionary to store failed products and their error messages
    error_log = {}

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
        nc_filepath = Path(path2dedicated_datacubes_on_demand) / product_level / tile
        

        if not os.path.exists(nc_filepath) or not os.path.isdir(nc_filepath):
            print(f"The directory '{nc_filepath}' does not exist. Creating it...")
            os.makedirs(nc_filepath)  # Create the directory

        nc_file = Path(nc_filepath) / nc_product

        second_chance_nc_file = Path(path2second_chance_netcdf) / platform / year / month / day / nc_product


        # path2safe_to_netcdf = "/home/josteines/src/NBS/safe_to_netcdf"
        # netcdf_creator_file = "run_sentinel_data_converter.py"

        '''
        sentinel_converter_path = Path(path2safe_to_netcdf) / netcdf_creator_file
        
        # Build the command to run the external script
        command = [
            "python3",  # Or "python", depending on your setup
            sentinel_converter_path,
            "--input_filepath", product_path,
            "--output", nc_filepath,
            ]
        '''
        # 6. Check existence and existance of netCDF
        if zip_filepath.is_file():
            print(f"Safe exists: {zip_filepath}")
            found += 1

            #######################################################################################

            # Variable to check
            variable2check = 'cloud_coverage'

            if nc_file.is_file():

                try:
                
                    if check_ds4certain_variable(path2nc=nc_file, variable=variable2check) == True:
                        print(f'{nc_file} exists and does have {variable2check} as a variable! Moving on.')
                    else:
                        createNetCDFfromSAFE(product_file = product_file,
                                            product = product, 
                                        nc_filepath = nc_filepath, 
                                            nc_file = nc_file,
                                        )
                        found_but_no_nc += 1

                    # Keep all nc paths in a list 
                    paths2each_single_ncfile_within_a_datacube.append(str(nc_file))

                except Exception as e:
                    # If an exception occurs, log the product and the error message
                    error_log[product] = str(e)
                    failed += 1


            elif not nc_file.is_file():

                try:

                    createNetCDFfromSAFE(product_file = product_file,
                                            product = product, 
                                        nc_filepath = nc_filepath, 
                                            nc_file = nc_file,
                                        )
                    found_but_no_nc += 1

                    # Keep all nc paths in a list 
                    paths2each_single_ncfile_within_a_datacube.append(str(nc_file))

                except Exception as e:
                    # If an exception occurs, log the product and the error message
                    error_log[product] = str(e)
                    failed +=1

        else:
            print(f"Missing: {zip_filepath}")
            missing += 1

        # # Keep all nc paths in a list 
        # paths2each_single_ncfile_within_a_datacube.append(str(nc_file))

        # As there is created more than planned (.SAFE folders with content) - remove these for now:
        remove_safe_folders(directory = nc_filepath)


        print('\n')

    # Print stats
    print("\n=== Summary ===")
    print(f"Found normal: {found}")
    print(f"Files lacking netCDF: {found_but_no_nc}")
    print(f"Missing: {missing}")
    print(f"Total processed: {found + missing}. Have made {found_but_no_nc} netCDF files that were lacking for the datacube on demand.")
    print(f"Total failed convertions to netCDF: {failed}")

    # Write the error log to a text file
    with open(f"{tile}_error_log.txt", "w") as file:
        for product, error_message in error_log.items():
            file.write(f"{product}: {error_message}\n")

    print("Error log written to 'error_log.txt'")

    print(paths2each_single_ncfile_within_a_datacube)
    print('\n')

    # path to datacubes on demand where nc products and datacubes are saved under product level and tile
    # path2dedicated_datacubes_on_demand = Path(path2dedicated_datacubes_on_demand) # = /lustre/storeB/project/NBS2/sentinel/production/NorwAREA/NetCDF-ondemand-products/datacubes
    path2dedicated_datacubes_on_demand = Path(path2dedicated_datacubes_on_demand) / product_level / tile


    p = Path(path2dedicated_datacubes_on_demand)
    for file_path in p.iterdir():
        if file_path.is_file():
            print(file_path.name) # Prints only the file name
            # To get the full path, use:
            # print(file_path)

    # 1. Loop through all .nc files in base_path
    nc_files = glob.glob(os.path.join(nc_filepath, "*.nc"))
    print('nc_files = ')
    print(nc_files)
    print('paths2each_single_ncfile_within_a_datacube = ')
    print(paths2each_single_ncfile_within_a_datacube)


    
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

    ''' My own creation to make the datacube
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
    '''

    # Creating/editing the datacube using Datacube from datacube.py
    datacube = Datacube(datacube_filepath)
    for nc_path in nc_files:
        #print(str(nc_path))
        datacube.add_product(nc_path)

    # Ensure the removal of eventual duplicate products and sorting of the remaining products
    datacube.remove_duplicates()
    datacube.sort()

    # # As there is created more than planned (.SAFE folders with content) - remove these for now:
    # remove_safe_folders(directory = path2dedicated_datacubes_on_demand)

    return
