import sys
import os
import datetime
import yaml
import argparse
import re
from datacube import Datacube 

def parse_args():
    """
    Parse command-line arguments for creating a Datacube from NetCDF files.

    Returns:
        argparse.Namespace: Parsed arguments including start_date, end_date, tile, level, and config.
    """
    parser = argparse.ArgumentParser(
        description="Create a Datacube from NetCDF files."
    )

    parser.add_argument(
        '--start_date', '-s',
        type=is_valid_date,
        required=True,
        help='Start date in YYYY-MM-DD format (required).'
    )

    parser.add_argument(
        '--end_date', '-e',
        type=is_valid_date,
        required=True,
        help='End date in YYYY-MM-DD format (required).'
    )

    parser.add_argument(
        '--tile', '-t',
        type=is_valid_tile,
        required=True,
        help='Tile identifier (e.g., T27XVH, must start with "T") (required).'
    )

    parser.add_argument(
        '--level', '-l',
        choices=['L2A', 'L1B', 'L1C'],
        required=True,
        help='Processing level (must be one of: L2A, L1B, L1C) (required).'
    )

    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='Path to the YAML configuration file (optional). Defaults to "config.yaml" in the current directory.'
    )

    return parser.parse_args()

def is_valid_date(date_str):
    """
    Validates if a string is in the 'YYYY-MM-DD' date format.

    Args:
        date_str (str): The date string to validate.

    Returns:
        str: The original date string if valid.

    Raises:
        argparse.ArgumentTypeError: If the date string is not in the valid format.
    """
    try:
        # Attempt to parse the date string
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return date_str  # Return the valid date string
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date: '{date_str}'. Date must be in the format YYYY-MM-DD."
        )


def is_valid_tile(tile):
    """
    Custom validation function for the tile argument.
    Ensures the tile starts with 'T' and is followed by exactly five alphanumeric characters.
    """
    if not (tile.startswith("T") and len(tile) == 6 and re.match(r"T[a-zA-Z0-9]{5}$", tile)):
        raise argparse.ArgumentTypeError("Tile must have the format 'T*****' (T plus a five-character combination of letters and numbers).")
    return tile


def read_and_validate_config_file(config_file):

    necessary_paths = ["base_path", "ncml_path"] # paths that must be correct for script to run
    
    # Load config file
    with open(config_file, "r") as file:
        config = yaml.safe_load(file)

    for path in necessary_paths:
        if path not in config['paths']:
            raise KeyError(f"Missing required configuration key: {path}")

    print("Configuration is valid!")

    return config

def create_datacube(start_date, end_date, tile, level, config_file):
    '''
    Create a Datacube by searching for relevant NetCDF files in a predictable folder structure.

    Args:
        base_path (str): Base path to the folder containing the data.
        ncml_path (str): Path where the NCML file for the datacube will be created.
        start_date (str): Start date in the format YYYY-MM-DD.
        end_date (str): End date in the format YYYY-MM-DD.
        tile (str): Tile identifier (e.g., T27XVH).
        level (str): Processing level (e.g., L1C, L2A).

    Returns:
        None
    '''

    #check that the yaml config filoe contains the necessary information
    config = read_and_validate_config_file(config_file)

    # Extracting paths from config file
    base_path = config["paths"]['base_path']
    ncml_path = config["paths"]['ncml_path']
    platforms = config.get("platforms", {}).values() 

    # Parse the input dates
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')

    # Ensure start_date <= end_date
    if start_date > end_date:
        raise ValueError('The start date must be earlier than or equal to the end date.')

    # Open log files
    #TODO: Log files should be written to a different location. Provide base path (directory) for log files in config and add the filename within the script.
    #TODO: New log file should be written every time a job is run. E.g. include other arguments in filepath and/or timestamp. Needs to be unique.
    added_files_log = open('added_files_datacube.log', 'w')  # Logging successfully added files
    missing_directories_log = open('missing_directories.log', 'w')  # Logging missing directories
    tile_or_level_not_found_log = open('tile_or_level_not_found.log', 'w')  # Logging directories where tile or level is not found

    try:
        # Instantiate the datacube
        print(f'Initializing datacube at: {ncml_path}')
        cube = Datacube(ncml_path)  # Creates, loads and updates .ncml files.
        wrong_tile_or_level_counts = None
        # Iterating through directories of the standard form platform/year/month/date and add files to the datacube
        for platform in platforms:
            current_date = start_date
            while current_date <= end_date:
                year = current_date.year
                month = f'{current_date.month:02d}'
                day = f'{current_date.day:02d}'

                # Construct the directory path
                dir_path = os.path.join(base_path, platform, str(year), month, day)

                if os.path.exists(dir_path):
                    # Search for files matching the tile and level
                    for file_name in os.listdir(dir_path):
                        if file_name.endswith('.nc') and tile in file_name and level in file_name:
                            file_path = os.path.join(dir_path, file_name)
                            # Write to 'added_files.log'
                            # TODO: Datacube filepath needs to be derived within the script not provided in the config.
                            # The problem with this approach is that the config file needs to be updated every time we run the script.
                            # TODO: The base path (directory) where to write the datacubes should be within the config.
                            added_files_log.write(f'{file_path}\n')
                            cube.add_product(file_path)  # Add the file to the datacube
                        else:
                            # write 'tile_or_level_not_found_log'
                            wrong_tile_or_level_counts = True
                            # TODO: This is too much logging. There will be lots of days where the level and tile combination are not present.
                            tile_or_level_not_found_log.write(f'{dir_path}\n')
                else:
                    # Write to 'missing_directories.log'
                    missing_directories_log.write(f'{dir_path}\n')

                # Increment the date
                current_date += datetime.timedelta(days=1)

        if wrong_tile_or_level_counts:
            print('Provided tile or level was not found in some searched directories. If you suspect misspelling, check tile_or_level_not_found_log.')

       	print('Datacube creation complete.')
    
    finally:
        # Close log files
        added_files_log.close()
        missing_directories_log.close()
        tile_or_level_not_found_log.close()


if __name__ == '__main__':
    # TODO: Store data in separate on-demand folder away from production area.
    # TODO: Integrate safe_to_netcdf into this process. So search from SAFE files instead
    args = parse_args()

    # Call the function
    create_datacube(args.start_date, args.end_date, args.tile, args.level, args.config)
