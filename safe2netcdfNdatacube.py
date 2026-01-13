'''
Check if we already have the SAFE files. Create a file with the missing products. 

/home/nbs/production_r8/datacubes_manager/find_missing_products.sh
'''



from utils import read_config_file,\
                  generate_date_range,\
                  find_safe_files_from_given_tileNproductlevel_within_time_interval, \
                  checkNcreate_netcdfNdatacubes
import os

### read in the desired config file
config_file_path = 'sensing_time_window_dc_config.yaml'
config = read_config_file(config_file_path)
# print(config)

# Extract the required variables from the config file
start_time = config['start_sensing_date']
end_time = config['end_sensing_date']
tile = config['tile']
path2safe_catalog = config['path2safe_catalog']
product_type = config['product_type']
product_level = config['product_level']
netcdf_converter = config['netcdf_creator_file']
path2safe_to_netcdf = config['path2safe_to_netcdf']
path2dedicated_datacubes_on_demand = config['path2dedicated_datacubes_on_demand']
netcdf_creator_file = config['netcdf_creator_file']
root_path = config['root_path']


# Extract the dates on a YYYY/MM/DD format between the selected start and end date 
date_range = generate_date_range(start_date = start_time, end_date = end_time)

# Extract all safe file directories from the selected time period and with the selected product type
# safe_files = []
# for dates in date_range:
#     full_path = os.path.join(path2safe_catalog, product_type, dates)
#     safe_files.append(full_path)


# Run through all possible safe files for product_type* (e.g. S2*) products within the date range
safe_files = []
for dates in date_range:
    # List all directories in the parent directory
    parent_path = os.path.join(path2safe_catalog)
    for folder in os.listdir(parent_path):
        # Check if the folder starts with the value of `product_type` and is a directory
        if folder.startswith(product_type) and os.path.isdir(os.path.join(parent_path, folder)):
            full_path = os.path.join(parent_path, folder, dates)
            safe_files.append(full_path)


# print(safe_files)
# print('\n')

# Only extract the complete file paths of safe files of the selected tile
desired_safe_files = find_safe_files_from_given_tileNproductlevel_within_time_interval(directories = safe_files,
                                                                                search_string_tile = tile, 
                                                                        search_string_productlevel = product_level,
                                                                        )
desired_safe_files.sort()

print(desired_safe_files)
print('\n')


'''
Create netCDF files from the SAFE files 

/home/nbs/production_r8/safe_to_netcdf/create_netcdf_for_datacubes.sh
'''


checkNcreate_netcdfNdatacubes(products = desired_safe_files, 
                              path2safe_catalog = path2safe_catalog, 
                              path2dedicated_datacubes_on_demand = path2dedicated_datacubes_on_demand, 
                              path2safe_to_netcdf = path2safe_to_netcdf, 
                              netcdf_creator_file = netcdf_creator_file,
                              root_path = root_path,
                              start_sensing_date = start_time,
                              end_sensing_date = end_time,
                              product_type = product_type,
                              )
