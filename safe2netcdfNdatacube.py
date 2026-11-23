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
                     SynchOnDemand, \
                     _product_stem, \
                     wait_for_downloaded_products, \
                     find_safe_catalog_directories, \
                     safe_catalog_directory_for_product, \
                     DownloadProductsTimeoutError
                  


import os
from datetime import datetime

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
datacube_interval_start = config.get('datacube_interval_start', '01/01')
datacube_interval_end = config.get('datacube_interval_end', '12/31')
datacube_mode = config.get('datacube_mode', 'recurring')
download_timeout_seconds = int(config.get('download_timeout_seconds', 3600))
download_poll_seconds = int(config.get('download_poll_seconds', 30))
download_stability_polls = int(config.get('download_stability_polls', 2))


def build_datacube_periods(
    requested_start,
    requested_end,
    interval_start,
    interval_end,
    mode='recurring',
):
    """Create either one full-range or recurring calendar datacube interval."""
    requested_start_date = datetime.strptime(requested_start, '%Y/%m/%d')
    requested_end_date = datetime.strptime(requested_end, '%Y/%m/%d')

    if mode == 'single':
        return [(
            f'{requested_start_date:%Y%m%d}_{requested_end_date:%Y%m%d}',
            requested_start,
            requested_end,
            generate_date_range(
                start_date=requested_start,
                end_date=requested_end,
            ),
        )]
    if mode != 'recurring':
        raise ValueError(
            f"Unsupported datacube_mode '{mode}'. Use 'single' or 'recurring'."
        )

    interval_start_month, interval_start_day = map(int, interval_start.split('/'))
    interval_end_month, interval_end_day = map(int, interval_end.split('/'))

    periods = []
    for year in range(requested_start_date.year, requested_end_date.year + 1):
        period_start_date = datetime(year, interval_start_month, interval_start_day)
        period_end_year = year + int(
            (period_start_date.month, period_start_date.day)
            > (interval_end_month, interval_end_day)
        )
        period_end_date = datetime(period_end_year, interval_end_month, interval_end_day)

        clipped_start = max(period_start_date, requested_start_date)
        clipped_end = min(period_end_date, requested_end_date)
        if clipped_start <= clipped_end:
            period_start = clipped_start.strftime('%Y/%m/%d')
            period_end = clipped_end.strftime('%Y/%m/%d')
            periods.append((
                f'{clipped_start:%Y%m%d}_{clipped_end:%Y%m%d}',
                period_start,
                period_end,
                generate_date_range(start_date=period_start, end_date=period_end),
            ))

    return periods

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


    periods = build_datacube_periods(
        requested_start=start_time,
        requested_end=end_time,
        interval_start=datacube_interval_start,
        interval_end=datacube_interval_end,
        mode=datacube_mode,
    )
    if datacube_mode == 'single':
        print('Creating one datacube for the complete requested date range.')
    else:
        print(
            f'Creating datacubes for recurring intervals '
            f'{datacube_interval_start} to {datacube_interval_end}.'
        )

    for period_label, period_start, period_end, period_date_range in periods:
        print(f'start_date = {period_date_range[0]}')
        print(f'end_date = {period_date_range[-1]}')
        
        # Run through all possible safe files for product_type* (e.g. S2*) products within the date range
        safe_files = find_safe_catalog_directories(
            path2safe_catalog=path2safe_catalog,
            product_type=product_type,
            date_range=period_date_range,
        )
        # print(safe_files)
        # print('\n')

        # Only extract the complete file paths of safe files of the selected tile
        desired_safe_files = find_safe_files_from_given_tileNproductlevel_within_time_interval(directories = safe_files,
                                                                                        search_string_tile = tile, 
                                                                                search_string_productlevel = product_level,
                                                                                )
        desired_safe_files.sort()

        # print(desired_safe_files[:5])
        period_description = f'{period_start} to {period_end}'
        print(f'Number of SAFE files found {len(desired_safe_files)} on our system for {product_level} {tile} in {period_description}.')
        print('\n')
        

        '''
        1. Query CDSE and check what products we do not have

        2. Single out the missing products

        3. Add the missing products to the download queue

        4. Make the netCDF files and the datacubes - already in place
        '''

        # Query CDSE for tile spesific products and compare against SAFE files on Satellittdata.no
        SAFE_query_results = queryCDSE4products_based_on_tile_and_product_level(date_from = period_start, date_to = period_end, tile_id = tile_id, product_level = product_level)
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

        print(f'{period_description} {product_level} {tile} products that only appear from querying CDSE - not on lustre:')
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
        print(f'{period_description} {product_level} {tile} products that only appear on lustre - not in CDSE-query:')
        if len(only_in_lustre) == 0:
            print('No products missing from the query!')
        else: 
            for prod in only_in_lustre:
                print(prod, '\n')
        print(f'There are {len(only_in_lustre)} products missing fromthe CDSE-query.')
        '''

        #'''
        if only_in_query:
            # Install the missing SAFE products on lustre from CDSE
            SynchOnDemand(list_of_products = only_in_query,
                        config_platform = config_platform_path,
                        config_mission = config_mission_path,
                        config_general = config_general_path)

            # list_of_products = list of tuples [(id, product_name), (id, product_name)...]
        #'''

        if only_in_query:
            expected_download_directories = {
                safe_catalog_directory_for_product(path2safe_catalog, product[1])
                for product in only_in_query
            }
            try:
                wait_for_downloaded_products(
                    expected_products=only_in_query,
                    search_directories=expected_download_directories,
                    timeout_seconds=download_timeout_seconds,
                    poll_seconds=download_poll_seconds,
                    stability_polls=download_stability_polls,
                )
            except DownloadProductsTimeoutError as error:
                print(
                    f'Post-sync checker: {len(error.missing_products)} '
                    'product(s) are missing or incomplete:'
                )
                for product_status in error.missing_products:
                    print(f'  - {product_status}')
                raise
            print(
                f'Post-sync checker passed: all {len(only_in_query)} '
                'product(s) submitted for synchronization are present, '
                'stable, and valid.'
            )

        # The initial scan predates synchronization; discover all products
        # before handing the list to the NetCDF conversion step.
        safe_files = find_safe_catalog_directories(
            path2safe_catalog=path2safe_catalog,
            product_type=product_type,
            date_range=period_date_range,
        )
        desired_safe_files = find_safe_files_from_given_tileNproductlevel_within_time_interval(
            directories=safe_files,
            search_string_tile=tile,
            search_string_productlevel=product_level,
        )
        desired_safe_files.sort()
        expected_names = {_product_stem(product[1]) for product in only_in_query}
        discovered_names = {
            _product_stem(product_path) for product_path in desired_safe_files
        }
        missing_after_rescan = sorted(expected_names - discovered_names)
        print(
            f'Post-sync catalog rescan: {len(missing_after_rescan)} of '
            f'{len(expected_names)} synchronized product(s) are still missing.'
        )
        if missing_after_rescan:
            for product_name in missing_after_rescan:
                print(f'  - {product_name}')
        if missing_after_rescan:
            raise RuntimeError(
                'Downloaded products were not found in the expected SAFE '
                f'catalog directories: {missing_after_rescan}'
            )
        
        '''
        Create netCDF files from the SAFE files 

        /home/nbs/production_r8/safe_to_netcdf/create_netcdf_for_datacubes.sh
        '''

        # '''
        checkNcreate_netcdfNdatacubes(
                                    #products = only_in_query, # just the safe file lacking on lustre
                                    products = desired_safe_files, # all safe files within the datacube
                                    path2safe_catalog = path2safe_catalog, 
                                    path2dedicated_datacubes_on_demand = path2dedicated_datacubes_on_demand, 
                                    path2safe_to_netcdf = path2safe_to_netcdf, 
                                    netcdf_creator_file = netcdf_creator_file,
                                    root_path = root_path,
                                    # start_sensing_date = start_time,
                                    # end_sensing_date = end_time,
                                    start_sensing_date = period_start,
                                    end_sensing_date = period_end,
                                    product_type = product_type,
                                    path2second_chance_netcdf = path2netcdf_stored_in_production,
                                    error_log_path = error_log_path,
                                    datacube_filename=f'{product_type}_{product_level}_{tile}_{period_label}.ncml',
                                    )
        # '''

print('The complete list of SAFE products missing on lustre for this run:')
print(len(complete_list_only_in_query), complete_list_only_in_query)
