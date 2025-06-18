# Datacube

A Python utility class to manage an NCML aggregation file that references multiple NetCDF files. This class allows creating, reading, updating, and validating the NCML file, which aggregates NetCDF datasets along a specified dimension.

## Features

- Load and parse an existing NCML aggregation file.
- Create a new NCML aggregation file.
- List all NetCDF files included in the aggregation.
- Add or remove NetCDF files to/from the aggregation.
- Clear all products from the aggregation.
- Validate that all referenced NetCDF files exist on disk.

## Usage

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
cube.remove_product("file1.nc")

# Clear all products
cube.clear()

# Validate that all listed products exist on disk
if cube.validate():
    print("All files are present")
else:
    print("Some files are missing")
```

## Requirements

- Python 3.x
- [lxml](https://lxml.de/) library

Install dependencies with:

```bash
pip install lxml
```

## Notes

- The class expects paths to NetCDF files to be valid on the local filesystem.
- The NCML file will be created or updated at the specified path.
- The default aggregation dimension is `"time"` with aggregation type `"joinExisting"`, but these can be customised.
