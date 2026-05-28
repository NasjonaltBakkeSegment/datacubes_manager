'''
Check if we already have the SAFE files. Create a file with the missing products. 

/home/nbs/production_r8/datacubes_manager/find_missing_products.sh
'''



from dc_utils import get_script_root_path,\
                     read_config_file,\
                     generate_date_range,\
                     find_safe_files_from_given_tileNproductlevel_within_time_interval, \
                     checkNcreate_netcdfNdatacubes, \
                     queryCDSE4products_based_on_tile_and_product_level, \
                     filter_products_by_latest_publication_date, \
                     filter_tuples_by_titles, \
                     SynchOnDemand
                  


import os

# Get the root path to the current directory
root_path = get_script_root_path()

### read in the desired config file
config_file_path = f'{root_path}/sensing_time_window_dc_config.yaml'
config = read_config_file(config_file_path)
# print(config)

# Extract the required variables from the config file
start_time = config['start_sensing_date']
end_time = config['end_sensing_date']
tiles = config['tile']
# tile_id = tile[1:] # Removing the first 'T' - This is used for the CDSE query
path2safe_catalog = config['path2safe_catalog']
product_type = config['product_type']
product_level = config['product_level']
netcdf_converter = config['netcdf_creator_file']
path2safe_to_netcdf = config['path2safe_to_netcdf']
path2dedicated_datacubes_on_demand = config['path2dedicated_datacubes_on_demand']
netcdf_creator_file = config['netcdf_creator_file']
path2netcdf_stored_in_production = config['path2netcdf_stored_in_production']
error_log_path = config['error_log_path']
config_platform_path = config['config_platform_path']
config_mission_path = config['config_mission_path']
config_general_path = config['config_general_path']

complete_list_only_in_query = []
# Ensure that tiles is a list that can be run through
if isinstance(tiles, str):
    tiles = [tiles]

for tile in tiles:

    tile_id = tile[1:] # Removing the first 'T' - This is used for the CDSE query

    # Extract the dates on a YYYY/MM/DD format between the selected start and end date 
    date_range = generate_date_range(start_date = start_time, end_date = end_time)

    # Extract all safe file directories from the selected time period and with the selected product type
    # safe_files = []
    # for dates in date_range:
    #     full_path = os.path.join(path2safe_catalog, product_type, dates)
    #     safe_files.append(full_path)


    # To separate each datacube by year the given date range is also devided by years
    import numpy as np
    yearly_list = np.arange(int(date_range[0][:4]), int(date_range[-1][:4])+1)
    print(f'Years for which datacubes are created:')
    print(yearly_list)
    for year in yearly_list:

        yearly_date_range = generate_date_range(start_date = f'{year}/{start_time[5:]}', end_date = f'{year}/{end_time[5:]}')
        print(f'start_date = {yearly_date_range[0]}')
        print(f'end_date = {yearly_date_range[-1]}')
        
        # Run through all possible safe files for product_type* (e.g. S2*) products within the date range
        safe_files = []
        # for dates in date_range:
        for dates in yearly_date_range:
            # List all directories in the parent directory
            parent_path = os.path.join(path2safe_catalog)
            for folder in os.listdir(parent_path):
                # Check if the folder starts with the value of `product_type` and is a directory
                if folder.startswith(product_type) and os.path.isdir(os.path.join(parent_path, folder, dates)):
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

        # print(desired_safe_files[:5])
        print(f'Number of SAFE files found {len(desired_safe_files)} on our system for {product_level} {tile} in {year}.')
        print('\n')
        

        '''
        1. Query CDSE and check what products we do not have

        2. Single out the missing products

        3. Add the missing products to the download queue

        4. Make the netCDF files and the datacubes - already in place
        '''

        # Query CDSE for tile spesific products and compare against SAFE files on Satellittdata.no
        SAFE_query_results = queryCDSE4products_based_on_tile_and_product_level(date_from = f'{year}/{start_time[5:]}', date_to = f'{year}/{end_time[5:]}', tile_id = tile_id, product_level = product_level) 
        SAFE_files_on_lustre = []
        for file in desired_safe_files:
            filename = file.split('/')[-1]
            SAFE_files_on_lustre.append(filename)

        # Filter out products from CDSE that is missing on Satellittdata.no
        
        # # Find items in list_a that are not in list_b
        # only_in_query = [item.replace('.SAFE','') for item in SAFE_query_results if item.replace('.SAFE','.zip') not in SAFE_files_on_lustre]

        # Filter the query result to make sure that they only include the latest version of each product
        #filtered_SAFE_query_results = filter_products_by_latest_publication_date(SAFE_query_results)

        only_in_query = filter_tuples_by_titles(
                                                tuple_list = SAFE_query_results,
                                                #tuple_list = filtered_SAFE_query_results, 
                                                title_list = SAFE_files_on_lustre)

        print(f'{year} {product_level} {tile} products that only appear from querying CDSE - not on lustre:')
        if len(only_in_query) == 0:
            print('No products missing from lustre!')
        else:
            for prod in only_in_query:
                print(prod, '\n')
    
        print(f'There are {len(only_in_query)} products missing on lustre')
        print('\n')

        complete_list_only_in_query.extend(only_in_query)

        # Find items in list_b that are not in list_a
        #only_in_lustre = [item.replace('.zip','') for item in SAFE_files_on_lustre if item.replace('.zip','.SAFE') not in SAFE_query_results]

        '''
        print(f'{year} {product_level} {tile} products that only appear on lustre - not in CDSE-query:')
        if len(only_in_lustre) == 0:
            print('No products missing from the query!')
        else: 
            for prod in only_in_lustre:
                print(prod, '\n')
        print(f'There are {len(only_in_lustre)} products missing fromthe CDSE-query.')
        '''

        #'''
        if len(only_in_query) > 0:
            # Install the missing products on lustre from CDSE
            SynchOnDemand(list_of_products = only_in_query,
                        config_platform = config_platform_path,
                        config_mission = config_mission_path,
                        config_general = config_general_path)
            # list_of_products = list of tuples [(id, product_name), (id, product_name)...]
        #'''
        
        '''
        Create netCDF files from the SAFE files 

        /home/nbs/production_r8/safe_to_netcdf/create_netcdf_for_datacubes.sh
        '''

        #'''
        checkNcreate_netcdfNdatacubes(products = desired_safe_files, 
                                    path2safe_catalog = path2safe_catalog, 
                                    path2dedicated_datacubes_on_demand = path2dedicated_datacubes_on_demand, 
                                    path2safe_to_netcdf = path2safe_to_netcdf, 
                                    netcdf_creator_file = netcdf_creator_file,
                                    root_path = root_path,
                                    # start_sensing_date = start_time,
                                    # end_sensing_date = end_time,
                                    start_sensing_date = f'{year}/{start_time[5:]}',
                                    end_sensing_date = f'{year}/{end_time[5:]}',
                                    product_type = product_type,
                                    path2second_chance_netcdf = path2netcdf_stored_in_production,
                                    error_log_path = error_log_path,
                                    )
        # '''

print('The complete list of SAFE products missing on lustre for this run:')
print(len(complete_list_only_in_query), complete_list_only_in_query)

