# Datacube Manager

A Python utility for managing NCML aggregation files that reference multiple NetCDF files. The core `Datacube` class allows creating, reading, updating, sorting, and validating NCML files, which aggregate NetCDF datasets along a specified dimension. Additional scripts are provided for building datacubes from directory structures.

## Features

- Load and parse an existing NCML aggregation file.
- Create a new NCML aggregation file.
- List all NetCDF files included in the aggregation.
- Add or remove NetCDF files to/from the aggregation.
- Clear all products from the aggregation.
- Validate that all referenced NetCDF files exist on disk.
- Sort products by timestamp.
- Delete the NCML datacube file from disk.

## Usage

### `Datacube` class (`datacube.py`)

```python
from datacube import Datacube

# Initialise with path to NCML file, optional dimension name and aggregation type
cube = Datacube("path/to/aggregation.ncml", dim_name="time", agg_type="joinExisting")

# List all products in the cube
print(cube.list_products())

# Check if a product is in the cube
print(cube.has_product("file1.nc"))

# Add a NetCDF product
cube.add_product("file1.nc")

# Remove a product
# Note: if the last product is removed, the NCML file is automatically deleted
cube.remove_product("file1.nc")

# Clear all products
cube.clear()

# Validate that all listed products exist on disk
if cube.validate():
    print("All files are present")
else:
    print("Some files are missing")

# Sort products by timestamp (ignores platform prefix e.g. S2A/S2B/S2C)
cube.sort()

# Delete the NCML file from disk
cube.delete_cube()
```

### Create a datacube on demand (`create_datacube_ondemand.py`)

Searches a predictable folder structure (`platform/year/month/day`) for NetCDF files matching a given tile, processing level, and date range, then adds them to a datacube.

```bash
python create_datacube_ondemand.py \
  --data_base /path/to/data \
  --start_date 2024-01-01 \
  --end_date 2024-03-31 \
  --tile T32VNM \
  --level L2A \
  --config config.yaml
```

The config YAML must contain a `paths.base_path` key (output path for the NCML file) and optionally a `platforms` section listing platform names (e.g. S2A, S2B, S2C).

### Process a directory (`process_directory.py` / `process_directory.sh`)

Recursively walks a directory for `.nc` files and adds each to the appropriate NCML datacube, organised by processing level, tile, and year.

```bash
python process_directory.py <ncml_base_path> <nc_root_dir>
# or
./process_directory.sh <ncml_base_path> <nc_root_dir>
```

### Process many directories (`process_many_directories.sh`)

Iterates over the last 12 months and multiple platforms (S2A, S2B, S2C), calling `process_directory.sh` for each monthly subdirectory. Edit the hardcoded `NCML_BASE_PATH` and `BASE_PATH` variables before use.

```bash
./process_many_directories.sh
```

## Requirements

- Python 3.x
- [lxml](https://lxml.de/) library
- [PyYAML](https://pyyaml.org/) library (for `create_datacube_ondemand.py`)

Install dependencies with:

```bash
pip install lxml pyyaml
```

## Notes

- The class expects paths to NetCDF files to be valid on the local filesystem.
- The NCML file will be created or updated at the specified path.
- The default aggregation dimension is `"time"` with aggregation type `"joinExisting"`, but these can be customised.
