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
                    
                    # Handle tiles or comma-separated strings as lists
                    if ',' in content:
                        # Split by commas and strip whitespace from each item
                        parsed_content = [item.strip() for item in content.split(',')]
                    else:
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


''' # Old query function that stopped working - 'Sentinel2' suddenly not viable collection
from cdsetool.query import query_features
from datetime import date, datetime
from cdsetool.query import describe_collection

def queryCDSE4products_based_on_tile_and_product_level(date_from, date_to, tile_id, product_level, collection = 'Sentinel2'):
    search_terms = describe_collection(collection).keys()
    # print(search_terms)

     # Extract year, month, and day from start date
    date_from_year, date_from_month, date_from_day = map(int, date_from.split('/'))
    start_date = date(date_from_year, date_from_month, date_from_day)

    # Extract year, month, and day from end date
    date_to_year, date_to_month, date_to_day = map(int, date_to.split('/'))
    end_date = date(date_to_year, date_to_month, date_to_day)


    search_terms = {
        "tileId": tile_id,
        "startDate": start_date,
        "completionDate": end_date,
        # "processingLevel":"S2MSI2A",
        # "processingLevel":"S2MSI1C",
        "processingLevel": f"S2MSI{product_level[1:]}",
        "maxRecords": '1000'
    }
    
    # Query features
    features = query_features(collection, search_terms)
    output = list(features)

    print(f"There are {len(output)} products found!\n")
    
    # Filter products by product level
    product_level_products = [
        (feature['id'], feature['properties']['title'])
        for feature in output
        if product_level in feature['properties']['title']
    ]

    print(f"There are {len(product_level_products)} {product_level} products among the T{tile_id} query results")
    
    return product_level_products


queryCDSE4products_based_on_tile_and_product_level(date_from = '2017/01/01', date_to = '2024/12/31', tile_id = 'T32VLN'[1:], product_level = 'L2A') 
#'''


#'''
import requests 
import pandas as pd 
import urllib.parse 
from datetime import datetime, timedelta 

base_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=" # Odata

def queryCDSE4products_based_on_tile_and_product_level(date_from, date_to, tile_id, product_level, base_url=base_url, collection='SENTINEL-2'):     
    """     
    Queries CDSE for products in a given collection and polygon     
    
    :param base_url: OData base URL for CDSE     
    :param collection_name: Name of the collection to query   
    :param date_from: Start date of the query (ISO format)     
    :param date_to: End date of the query (ISO format)
    :param product_level: Name of the product level to query 
    :param tile: Tile IDs to query    
    :return: DataFrame including metadata for products     
    """

    query = (
        f"{base_url}"
        f"Collection/Name eq '{collection}' and "
        f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq 'S2MSI{product_level[1:]}') and "
        f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'tileId' and att/OData.CSC.StringAttribute/Value eq '{tile_id}') and " 
        f"ContentDate/End gt {date_from.replace('/','-')}T00:00:00.000Z and "
        f"ContentDate/End lt {date_to.replace('/','-')}T23:59:59.599Z"
        "&$orderby=ContentDate/End desc"
        # "&$expand=Attributes" # option to see expanded Attributes within products[i] below
        "&$count=False"
        f"&$top=1000"
    )

    products = []

    while query:

        r = requests.get(query)
        # print(r) # = <Response [200]> if working correctly
        if r.ok:
            response = r.json()
            products.extend(response.get('value', []))
            query = response.get('@odata.nextLink')
            # print(response.get('@odata.count')) # if count=True

    # Visualising the query results
    # print(products[0], '\n')
    # print(products[-1], '\n')

    print(f"There are {len(products)} products found on CDSE!\n")

    # Extracting Id and Name into list of tuples ('Id', 'Name') - with an extra check to see if the function returns products within correct productLevel and tileId 
    product_level_products = [
        (product.get('Id'), product.get('Name'))
        for product in products
        if product_level and 'T'+tile_id in product.get('Name')
    ]

    print(f"There are {len(product_level_products)} {product_level} products among the T{tile_id} query results")
    
    return product_level_products

# print(queryCDSE4products_based_on_tile_and_product_level(date_from = '2024/01/01', date_to = '2024/12/31', tile_id = '32VLN', product_level = 'L2A'))
# queryCDSE4products_based_on_tile_and_product_level(date_from = '2024/01/01', date_to = '2024/12/31', tile_id = '32VLN', product_level = 'L2A')
#'''

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

import glob
import shutil
    
def remove_safe_folders(directory, file_name_without_extension):
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
        if os.path.isdir(item_path) and item.endswith(f"{file_name_without_extension}.SAFE"):
            # print(f"Removing folder: {item_path}")
            # Remove the directory and all its contents
            shutil.rmtree(item_path)


from pathlib import Path
# from subprocess import call
import subprocess

from datacube import Datacube

import sys
import os

# Save the original sys.path
original_sys_path = sys.path.copy()

# Get the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the neighboring folder 'safe_to_netcdf' to sys.path
neighboring_folder_path_safe_to_netcdf = os.path.join(current_dir, '..', 'safe_to_netcdf')
sys.path.insert(0, neighboring_folder_path_safe_to_netcdf)

# Import Sentinel2_reader_and_NetCDF_converter
# from s2_reader_and_NetCDF_converter import Sentinel2_reader_and_NetCDF_converter
from transform import transform

# Add the 'config' subfolder of 'safe_to_netcdf' to sys.path
config_folder_path = os.path.join(neighboring_folder_path_safe_to_netcdf, 'config')
sys.path.insert(0, config_folder_path)


# Verify the config folder is in sys.path
print(f"Added config folder to sys.path: {config_folder_path}")

# List the files in the config folder to verify it is accessible
if os.path.exists(config_folder_path) and os.path.isdir(config_folder_path):
    files_in_config = os.listdir(config_folder_path)
    print("Files in the config folder:")
    for file_name in files_in_config:
        print(f"- {file_name}")
else:
    print(f"Config folder does not exist or is not a directory: {config_folder_path}")


# import utils
# print(f"Using utils.py from: {utils.__file__}")

# Add the neighboring folder 'cdse_synchroniser' to sys.path
neighboring_folder_path_cdse_synchroniser = os.path.join(current_dir, '..', 'cdse_synchroniser')
sys.path.insert(0, neighboring_folder_path_cdse_synchroniser)

# Import both the `database` module and the `Database` class
import lib.database as database
from lib.database import Database

# Print the path of the imported database module
print(f"Using database.py from: {database.__file__}")


# def createNetCDFfromSAFE(product_file, product, nc_filepath, nc_file):
    
#     # Initialize the Sentinel2 reader and converter
#     converter = Sentinel2_reader_and_NetCDF_converter(product=product_file.replace('.zip',''), # Filename without extension
#                                                         indir=Path(product).parent,            # Path to parent folder of the product
#                                                     outdir=nc_filepath)                     # Output directory of the NetCDF output file (the parent folder)
#     # Perform the conversion if the SAFE file was read successfully
#     if converter.read_ok:
#         success = converter.write_to_NetCDF(nc_filepath, compression_level=4)
#         # if success:
#         #     print(f"Conversion successful! NetCDF file saved in: {nc_file}")
#         # else:
#         #     print("Conversion failed during NetCDF writing.")
#     else:
#         print("Failed to read the SAFE file. Please check the input file.")

#     # except subprocess.CalledProcessError as e:
#     #     print("Error occurred while running the script:")
#     #     print(e.stderr)
#     print(f'{nc_file} does not exist! Creating this.')

#     return

def createNetCDFfromSAFE(product_file, product, nc_file):

    # Check if the zip file is in place on lustre
    if Path(product).is_file():
         
        # Initialize the transformer
        transform(product_name = product_file.replace('.zip',''), # Filename without extension
                  safedir=str(Path(product).parent),              # Path to parent folder of the product
                  netcdfdir=str(Path(nc_file).parent),                              # Output directory of the NetCDF output file (the parent folder)
                  target = "netCDF",                              # Target format, either 'netCDF' or 'geoTIFF'
                  tmpdir='/lustre/storeB/project/NBS2/sentinel/production/NorwAREA/temporary_storage',
                  global_attributes_config = '/home/nbs/production_r8/safe_to_netcdf/config/global_attributes.yaml',
                  variable_attributes_config = '/home/nbs/production_r8/safe_to_netcdf/config/variable_attributes.yaml',
    )
        print(f'{nc_file} does not exist! Creating this.')
    
    else:
        print("Failed to read the SAFE file. Please check the input file.")

    return


def checkNcreate_netcdfNdatacubes(products, path2safe_catalog, path2dedicated_datacubes_on_demand, path2safe_to_netcdf, netcdf_creator_file, root_path, product_type, start_sensing_date, end_sensing_date, path2second_chance_netcdf, error_log_path):

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
        if "SAFE.zip" in product_file:
            nc_product = product_file.replace(".SAFE.zip",".nc")
        else:
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
            # print(f"The directory '{nc_filepath}' does not exist. Creating it...")
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
            #print(f"Safe exists: {zip_filepath}")
            found += 1

            #######################################################################################

            # Variable to check
            variable2check = 'cloud_coverage'
            
            if nc_file.is_file():

                try:
                
                    if check_ds4certain_variable(path2nc=nc_file, variable=variable2check) == True:
                        # print(f'{nc_file} exists and does have {variable2check} as a variable! Moving on.')
                        pass
                    else:
                        createNetCDFfromSAFE(product_file = product_file,
                                            product = product, 
                                        # nc_filepath = nc_filepath, 
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
                                        # nc_filepath = nc_filepath, 
                                              nc_file = nc_file,
                                    )
                    found_but_no_nc += 1

                    # Keep all nc paths in a list 
                    paths2each_single_ncfile_within_a_datacube.append(str(nc_file))

                except Exception as e:
                    # If an exception occurs, log the product and the error message
                    error_log[product] = str(e)
                    print(f'Failed to write {product_file}to NetCDF: {error_log[product]}, \n')
                    failed +=1


            # As there is created more than planned (.SAFE folders with content) - remove these for now:
            remove_safe_folders(directory = nc_filepath, file_name_without_extension = product_file.replace('.zip',''))
        else:
            print(f"Missing: {zip_filepath}")
            missing += 1

        # # Keep all nc paths in a list 
        # paths2each_single_ncfile_within_a_datacube.append(str(nc_file))

        # As there is created more than planned (.SAFE folders with content) - remove these for now:
        #remove_safe_folders(directory = nc_filepath, file_name_without_extension = product_file.replace('.zip',''))


        # print('\n')

    # Print stats
    print("\n=== Summary ===")
    print(f"Found normal: {found}")
    print(f"Files lacking netCDF: {found_but_no_nc}")
    print(f"Missing: {missing}")
    print(f"Total processed: {found + missing}. Have made {found_but_no_nc} netCDF files that were lacking for the datacube on demand.")
    print(f"Total failed convertions to netCDF: {failed}")

    # Write the error log to a text file
    if len(error_log) > 0:
        with open(f"{error_log_path}/{year}_{tile}_error_log.txt", "w") as file:
            for product, error_message in error_log.items():
                file.write(f"{product}: {error_message}\n")

    print("Error log written to 'error_log.txt'")

    #print(paths2each_single_ncfile_within_a_datacube)
    print('\n')

    # path to datacubes on demand where nc products and datacubes are saved under product level and tile
    # path2dedicated_datacubes_on_demand = Path(path2dedicated_datacubes_on_demand) # = /lustre/storeB/project/NBS2/sentinel/production/NorwAREA/NetCDF-ondemand-products/datacubes
    path2dedicated_datacubes_on_demand = Path(path2dedicated_datacubes_on_demand) / product_level / tile


    # p = Path(path2dedicated_datacubes_on_demand)
    # for file_path in p.iterdir():
    #     if file_path.is_file():
    #         print(file_path.name) # Prints only the file name
    #         # To get the full path, use:
    #         # print(file_path)

    # 1. Loop through all .nc files in base_path
    nc_files = glob.glob(os.path.join(nc_filepath, "*.nc"))
    print('nc_files = ')
    print(len(nc_files))
    print('paths2each_single_ncfile_within_a_datacube = ')
    print(len(paths2each_single_ncfile_within_a_datacube))


    
    date_str_start = start_sensing_date.replace('/','')
    date_str_end = end_sensing_date.replace('/','')

    print(f'The date_str_start = {date_str_start} and the date_end_str = {date_str_end} for the current datacube.')

    path2spesific_datacubes_folder = Path(path2dedicated_datacubes_on_demand) / 'datacubes'

    # Create datacubes folder if not excisting
    if not os.path.exists(path2spesific_datacubes_folder) or not os.path.isdir(path2spesific_datacubes_folder):
        print(f"The directory '{path2spesific_datacubes_folder}' does not exist. Creating it...")
        os.makedirs(path2spesific_datacubes_folder)  # Create the directory

    # else:
    #     print(f"The directory '{path2spesific_datacubes_folder}' does exist.")

    # 3. Create filepath for datacube (base_path/S2_L2A_T32VNM_YEAR.ncml)
    #datacube_filename = f"{product_type}_{product_level}_{tile}_{date_str_start}_{date_str_end}.ncml"
    datacube_filename = f"{product_type}_{product_level}_{tile}_{date_str_start[:4]}.ncml"
    datacube_filepath = os.path.join(path2spesific_datacubes_folder, datacube_filename)
    print(datacube_filepath)

    # Creating/editing the datacube using Datacube from datacube.py
    datacube = Datacube(datacube_filepath)
    for nc_path in paths2each_single_ncfile_within_a_datacube:
        #print(str(nc_path))
        datacube.add_product(nc_path)

    # Ensure the removal of eventual duplicate products and sorting of the remaining products
    datacube.remove_duplicates()
    datacube.sort()

    # # As there is created more than planned (.SAFE folders with content) - remove these for now:
    # remove_safe_folders(directory = path2dedicated_datacubes_on_demand)

    return

# # This can be used if one wants to evaluate the entire dict all together
# def filter_dict_by_filename(tile_dict):
#     def extract_filename(product_name):
#         """Extract the filename without the publication date."""
#         return product_name.split('.', 1)[0][:-15]  # Remove the last 15 characters (YYYYMMDDTHHMMSS)
    
#     def extract_publication_date(product_name):
#         """Extract the publication date as a sortable string."""
#         return product_name[-15:]  # Extract the last 15 characters YYYYMMDDTHHMMSS

#     # Step 1: Create a mapping of filenames to their latest product
#     filename_to_latest_product = {}
#     for product_list in tile_dict.values():
#         for product_id, product_name in product_list:
#             filename = extract_filename(product_name)
#             publication_date = extract_publication_date(product_name)
#             # Check if this filename already exists in the map
#             if filename not in filename_to_latest_product:
#                 filename_to_latest_product[filename] = [product_id, product_name]
#             else:
#                 # Compare publication dates and update if this one is newer
#                 existing_date = extract_publication_date(filename_to_latest_product[filename][1])
#                 if publication_date > existing_date:
#                     filename_to_latest_product[filename] = [product_id, product_name]
    
#     # Step 2: Build the filtered dictionary
#     filtered_dict = {}
#     for tile, product_list in tile_dict.items():
#         filtered_list = []
#         for product_id, product_name in product_list:
#             filename = extract_filename(product_name)
#             # Add the product only if it matches the latest product for the filename
#             if filename_to_latest_product[filename] == [product_id, product_name]:
#                 filtered_list.append([product_id, product_name])
#         if filtered_list:
#             filtered_dict[tile] = filtered_list

#     return filtered_dict

def filter_products_by_latest_publication_date(product_list):
    def extract_filename(product_name):
        """Extract the filename without the publication date."""
        return product_name.split('.', 1)[0][:-15]  # Remove the last 15 characters (YYYYMMDDTHHMMSS)
    
    def extract_publication_date(product_name):
        """Extract the publication date as a datetime object."""
        publication_date_str = product_name.split('.', 1)[0][-15:]  # Extract the last 15 characters
        # Convert the string to a datetime object
        return datetime.strptime(publication_date_str, "%Y%m%dT%H%M%S")

    # Step 1: Create a mapping of filenames to their latest product
    filename_to_latest_product = {}
    for product_id, product_name in product_list:
        filename = extract_filename(product_name)
        publication_date = extract_publication_date(product_name)
        
        if filename not in filename_to_latest_product:
            # Add new entry if filename is not already present
            filename_to_latest_product[filename] = [product_id, product_name, publication_date]
        else:
            # Compare publication dates using the datetime objects
            existing_date = filename_to_latest_product[filename][2]
            if publication_date > existing_date:
                # Replace the old entry with the new one
                filename_to_latest_product[filename] = [product_id, product_name, publication_date]

    # Step 2: Return the filtered list of products (remove the datetime from the output)
    return [[product_id, product_name] for product_id, product_name, _ in filename_to_latest_product.values()]


def filter_tuples_by_titles(tuple_list, title_list):
        """
        Filters tuples based on whether the title in the tuple (without its extension) 
        matches a title in the title list. The resulting list contains tuples with titles
        stripped of their extensions.

        Args:
            tuple_list (list of tuples): A list of tuples in the format (id, title) where title has a ".SAFE" extension.
            title_list (list of str): A list of titles with a ".zip" extension.

        Returns:
            list of tuples: A list of tuples where the title matches the title list, stripped of its extension.
        """
        # Helper function to remove the file extension
        def strip_extension(title):
            return title.split('.', 1)[0]  # Split by the last '.' and take the base name

        # Normalize the title list by stripping the ".zip" extension
        normalized_titles = [strip_extension(title) for title in title_list]

        # Filter the tuples, normalize their titles, and remove extensions in the final result
        filtered_list = [(id_, title) for id_, title in tuple_list if strip_extension(title) not in normalized_titles]

        return filtered_list



# def writing_missing_products_2_file(tile, tuple_list, file_path):
#     """
#     Updates the tile's data in a .txt file by updating the entire dictionary each time.
#     If the tile already exists, its value is updated by adding new tuples to the existing ones.
#     If the tile does not exist, a new key-value pair is added.
#     The list of tuples is sorted alphabetically by the title before saving.
    
#     Args:
#         tile (str): The tile name.
#         tuple_list (list of tuples): A list of tuples in the format (id, title) for the given tile.
#         file_path (str): Path to the .txt file where the data should be stored.
    
#     Returns:
#         None
#     """
#     # Initialize an empty dictionary to hold the tile data
#     tile_data = {}

#     # Read the existing file content (if it exists)
#     try:
#         with open(file_path, 'r') as file:
#             # Read the file and evaluate its content as a Python dictionary
#             content = file.read().strip()
#             if content:
#                 tile_data = eval(content)  # Convert the string back to a dictionary
#     except FileNotFoundError:
#         # If the file doesn't exist, start with an empty dictionary
#         pass
#     except SyntaxError:
#         # If the file is not properly formatted, start fresh
#         pass

#     # If the tile already exists, append the new tuples to the existing list
#     if tile in tile_data:
#         existing_tuples = tile_data[tile]
#         # Avoid duplicating tuples by using a set
#         updated_tuples = list(set(existing_tuples + tuple_list))
#         # Sort the list of tuples alphabetically by title (second element of each tuple)
#         tile_data[tile] = sorted(updated_tuples, key=lambda x: x[1])
#     else:
#         # Sort the new list of tuples before adding
#         tile_data[tile] = sorted(tuple_list, key=lambda x: x[1])

#     # Write the updated dictionary back to the .txt file
#     with open(file_path, 'w') as file:
#         file.write(str(tile_data))  # Convert the dictionary to a string and write it

#     return

import json

def writing_missing_products_2_file(tile, tuple_list, file_path):
    """
    Updates the tile's data in a JSON file by updating the entire dictionary each time.
    If the tile already exists, its value is updated by adding new tuples to the existing ones.
    If the tile does not exist, a new key-value pair is added.
    Duplicate (id, title) pairs are automatically removed.
    The list of tuples is sorted alphabetically by the title before saving.
    
    Args:
        tile (str): The tile name.
        tuple_list (list of tuples): A list of tuples in the format (id, title) for the given tile.
        file_path (str): Path to the JSON file where the data should be stored.
    
    Returns:
        None
    """
    # Initialize an empty dictionary to hold the tile data
    tile_data = {}

    # Read the existing JSON file content (if it exists)
    try:
        with open(file_path, 'r') as file:
            tile_data = json.load(file)  # Load the JSON content as a dictionary
    except FileNotFoundError:
        # If the file doesn't exist, start with an empty dictionary
        pass
    except json.JSONDecodeError:
        # If the file is not properly formatted, start fresh
        pass

    # Ensure all tuples in the input are unique
    tuple_list = list(set(tuple_list))
    
    # If the tile already exists, merge the new tuples with the existing ones
    if tile in tile_data:
        # Convert existing and new tuples to sets to ensure uniqueness
        existing_tuples = tile_data[tile]
        updated_tuples = list(set([tuple(t) for t in existing_tuples] + tuple_list))
        # Sort the list of tuples alphabetically by title (second element of each tuple)
        tile_data[tile] = sorted(updated_tuples, key=lambda x: x[1])
    else:
        # Sort the new list of tuples before adding
        tile_data[tile] = sorted(tuple_list, key=lambda x: x[1])

    # Write the updated dictionary back to the JSON file
    with open(file_path, 'w') as file:
        json.dump(tile_data, file, indent=4)  # Write the dictionary as a JSON file with formatting

    return


from synchronise_on_demand import synchronise_on_demand

def SynchOnDemand(list_of_products,
                  # config, # might need to split this
                  config_platform, # Add the file paths of these to the config in datacubes_manager
                  config_mission,
                  config_general):
     
    synchronise_on_demand(list_of_products, \
                  config_platform, # Add the file paths of these to the config in datacubes_manager \
                  config_mission, \
                  config_general)
    return
    