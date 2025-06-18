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
        if os.path.exists(self.ncml_path):
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
                # In case aggregation missing for some reason
                self._aggregation = etree.SubElement(
                    self._root, "aggregation", dimName=self.dim_name, type=self.agg_type
                )

        if self.has_product(filepath):
            print(f"Product already present: {filepath}")
            return

        # Add netcdf element
        etree.SubElement(self._aggregation, "netcdf", location=filepath, ncoords="1")
        self._tree.write(self.ncml_path, pretty_print=True, xml_declaration=True, encoding="utf-8")

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
                self._tree.write(self.ncml_path, pretty_print=True, xml_declaration=True, encoding="utf-8")
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