import os
from lxml import etree

class Datacube:
    NS = "http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2"
    NSMAP = {None: NS}

    def __init__(self, ncml_path, dim_name="time", agg_type="joinExisting"):
        self.ncml_path = ncml_path
        self.dim_name = dim_name
        self.agg_type = agg_type
        self._tree = None
        self._root = None
        self._aggregation = None
        if os.path.exists(self.ncml_path) and os.path.getsize(self.ncml_path) > 0:
            self._load_ncml()

    def _load_ncml(self):
        '''
        Load the cube
        '''
        self._tree = etree.parse(self.ncml_path)
        self._root = self._tree.getroot()
        self._aggregation = self._root.find(f"{{{self.NS}}}aggregation")

    def _create_ncml(self):
        '''
        Create the cube
        '''
        # Create directory if not exists
        os.makedirs(os.path.dirname(self.ncml_path), exist_ok=True)

        # Create root and aggregation elements
        self._root = etree.Element("netcdf", nsmap=self.NSMAP)
        self._aggregation = etree.SubElement(
            self._root, "aggregation", dimName=self.dim_name, type=self.agg_type
        )
        self._tree = etree.ElementTree(self._root)
        self._tree.write(self.ncml_path, pretty_print=True, xml_declaration=True, encoding="utf-8")

    def list_products(self):
        '''
        List all products in the cube
        '''
        if self._aggregation is None:
            return []

        # Find all <netcdf> elements within the aggregation
        netcdf_elements = self._aggregation.findall(f"{{{self.NS}}}netcdf")
        # Extract the 'location' attribute from each
        return [elem.get("location") for elem in netcdf_elements]

    def has_product(self, filepath):
        '''
        Checks whether a product is included in the cube
        '''
        return filepath in self.list_products()

    def add_product(self, filepath):
        '''
        Add a product to the cube
        '''
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"NetCDF file not found: {filepath}")

        if self._tree is None:
            self._create_ncml()
        else:
            if self._aggregation is None:
                self._aggregation = etree.SubElement(
                    self._root, "aggregation", dimName=self.dim_name, type=self.agg_type
                )

        if self.has_product(filepath):
            print(f"Product already present: {filepath}")
            return

        # Add netcdf element
        etree.SubElement(self._aggregation, "netcdf", location=filepath, ncoords="1")

        # Ensure proper formatting
        etree.indent(self._tree, space="  ")

        self._tree.write(self.ncml_path, pretty_print=True, xml_declaration=True, encoding="utf-8")

        # Reload the NCML file to ensure in-memory state matches the file on disk
        self._load_ncml()

    def remove_product(self, filepath):
        '''
        Remove a product from the cube
        '''
        if self._aggregation is None:
            print("No aggregation found in NCML.")
            return

        for nc in self._aggregation.findall(f"{{{self.NS}}}netcdf"):
            if nc.get("location") == filepath:
                self._aggregation.remove(nc)
                # Ensure proper formatting
                etree.indent(self._tree, space="  ")
                self._tree.write(self.ncml_path, pretty_print=True, xml_declaration=True, encoding="utf-8")
                if len(self._aggregation.findall(f"{{{self.NS}}}netcdf")) == 0:
                    print("Deleting datacube as it contains no products")
                    self.delete_cube()
                return
        print(f"Product not found: {filepath}")

    def clear(self):
        '''
        Remove all products from the cube
        '''
        if self._aggregation is not None:
            self._aggregation.clear()
            self._tree.write(self.ncml_path, pretty_print=True, xml_declaration=True, encoding="utf-8")

    def validate(self):
        '''
        Check whether netCDF files list in cube exist
        '''
        missing_files = []
        for filepath in self.list_products():
            if not os.path.exists(filepath):
                missing_files.append(filepath)
        if missing_files:
            print("Missing NetCDF files:")
            for f in missing_files:
                print(f" - {f}")
            return False
        return True

    def delete_cube(self):
        '''
        Delete the ncml datacube file
        '''
        if os.path.exists(self.ncml_path):
            os.remove(self.ncml_path)
            print(f'Data cube deleted: {self.ncml_path}')
        else:
            print(f'File does not exist: {self.ncml_path}')

    def sort(self):
        '''
        Sort the datacube products by timestamp and the rest of the filename after the timestamp,
        ignoring the platform (e.g., S2A, S2B, S2C).
        '''
        if self._aggregation is None:
            print("No aggregation found in NCML.")
            return

        netcdf_elements = self._aggregation.findall(f"{{{self.NS}}}netcdf")

        # Define a helper function to extract the sorting key
        def extract_sort_key(elem):
            location = elem.get("location", "")
            filename = os.path.basename(location)
            # Split the filename into parts and ignore the platform (e.g., S2A, S2B)
            parts = filename.split("_")
            if len(parts) > 2:
                # Extract everything from the timestamp (e.g., 20221203T104421 and beyond)
                key = "_".join(parts[2:])
            else:
                key = ""
            return key

        sorted_elements = sorted(netcdf_elements, key=extract_sort_key)

        dim_name = self._aggregation.get("dimName", "time")
        agg_type = self._aggregation.get("type", "joinExisting")

        self._aggregation.clear()
        self._aggregation.set("dimName", dim_name)
        self._aggregation.set("type", agg_type)

        for elem in sorted_elements:
            self._aggregation.append(elem)

        etree.indent(self._tree, space="  ")

        self._tree.write(self.ncml_path, pretty_print=True, xml_declaration=True, encoding="utf-8")
        print("Data cube sorted successfully.")

        # Reload the NCML file to ensure in-memory state matches the file on disk
        self._load_ncml()

    def remove_duplicates(self):
        '''
        Remove duplicate products, retaining only the one with the latest baseline.
        If multiple products have the same baseline, retain the one with the latest second timestamp.
        '''
        if self._aggregation is None:
            print("No aggregation found in NCML.")
            return

        netcdf_elements = self._aggregation.findall(f"{{{self.NS}}}netcdf")
        latest_products = {}

        def extract_key_baseline_and_timestamp(location):
            filename = os.path.basename(location)
            parts = filename.split("_")
            if len(parts) > 3:
                unique_key = "_".join(parts[:3] + parts[4:-1])  # Unique identifier for products (excluding baseline and timestamp)
                baseline = parts[3]  # Baseline (e.g., N0511)
                second_timestamp = parts[-1].split(".")[0]  # Second timestamp (e.g., 20251231T142312)
            else:
                unique_key = filename
                baseline = ""
                second_timestamp = ""
            return unique_key, baseline, second_timestamp

        for elem in netcdf_elements:
            location = elem.get("location", "")
            unique_key, baseline, second_timestamp = extract_key_baseline_and_timestamp(location)
            if unique_key not in latest_products:
                # First occurrence of this unique key
                latest_products[unique_key] = (baseline, second_timestamp, elem)
            else:
                # Compare existing product with the new one based on baseline and second timestamp
                existing_baseline, existing_second_timestamp, _ = latest_products[unique_key]

                if baseline > existing_baseline or (baseline == existing_baseline and second_timestamp > existing_second_timestamp):
                    # If the new product has a later baseline or the same baseline but a later second timestamp, update
                    latest_products[unique_key] = (baseline, second_timestamp, elem)

        # Clear the aggregation and rebuild it with the latest products
        dim_name = self._aggregation.get("dimName", "time")
        agg_type = self._aggregation.get("type", "joinExisting")

        self._aggregation.clear()
        self._aggregation.set("dimName", dim_name)
        self._aggregation.set("type", agg_type)

        for _, (_, _, elem) in latest_products.items():
            self._aggregation.append(elem)

        etree.indent(self._tree, space="  ")
        self._tree.write(self.ncml_path, pretty_print=True, xml_declaration=True, encoding="utf-8")
        print("Duplicates removed successfully.")

        # Reload the NCML file to ensure in-memory state matches the file on disk
        self._load_ncml()