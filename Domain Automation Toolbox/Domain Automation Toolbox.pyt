# -*- coding: utf-8 -*-

import arcpy
import pandas as pd
import os
import json


class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Change Domain Names in a Folder"
        self.description = "Change Domain Names in a Folder"

    def getParameterInfo(self):
        """Define the tool parameters."""
        params = [
            arcpy.Parameter(
                displayName = "FOLDER OF GDBS",
                name = "FOLDER OF GDBS",
                datatype = "DEFolder",
                parameterType = "optional",
                direction = "Input"),
            arcpy.Parameter(
                displayName = "GDB",
                name = "GDB",
                datatype = "DEWorkspace",
                parameterType = "optional",
                direction = "Input"),    
            arcpy.Parameter(
                displayName = "Domain to Create CSV",
                name = "Domain to Create CSV",
                datatype = "DEFile",
                parameterType = "optional",
                direction = "Input"),
            arcpy.Parameter(
                displayName = "Domains to assign Fields CSV",
                name = "Domains to assign Fields CSV",
                datatype = "DEFile",
                parameterType = "optional",
                direction = "Input"),
            arcpy.Parameter(
                displayName = "Domains to Delete CSV",
                name = "Field Delete CSV",
                datatype = "DEFile",
                parameterType = "optional",
                direction = "Input"),
            arcpy.Parameter(
                displayName = "Coded Value to Create for Domains CSV",
                name = "Coded Value to Create for Domains CSV",
                datatype = "DEFile",
                parameterType = "optional",
                direction = "Input"),
            arcpy.Parameter(
                displayName = "Coded Value to Create for Domains JSON",
                name = "Coded Value to Create for Domains JSON",
                datatype = "DEFile",
                parameterType = "optional",
                direction = "Input"),
            arcpy.Parameter(
                displayName = "Filter Name (separate more than one with a comma)",
                name = "Filter Name  (separate more than one with a comma)",
                datatype = "GPString",
                parameterType = "optional",
                direction = "Input"),
            arcpy.Parameter(
                displayName = "Type (Point, Polyline, Polygon)",
                name = "Type (Point, Polyline, Polygon)",
                datatype = "GPString",
                parameterType = "Required",
                direction = "Input")
                ]
        params[8].filter.type = "ValueList"
        params[8].filter.list = ["Point", "Polyline", "Polygon"]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return
    
    def __check_domain_headers(self, headers_to_check, identifier):
        if identifier == 'create':
            headers = ('Domain Name','Description','Field Type','Domain Type')
        if identifier == 'delete':
            headers = ('Delete Domain',)
        if identifier == 'assign':
            headers = ('Field_Name','Domain_Name')
        for header in headers:
            if header not in headers_to_check.columns.to_list():
                raise NameError(f"{headers} headers must be in these name not {headers_to_check.columns.to_list()}")
        
    
    def __domain_to_delete(self, delete_csv,  gdb_path, gdb_name):

        # List all existing domains
        existing_domains = [d.name for d in arcpy.da.ListDomains(gdb_path)]
        self.__check_domain_headers(delete_csv, 'delete')
        for index, row in delete_csv.iterrows():
            domain_name = row['Delete Domain']
            if domain_name in existing_domains:
                try:
                    arcpy.management.DeleteDomain(gdb_path, domain_name)
                    existing_domains.remove(domain_name)  # Update the list of existing domains
                    arcpy.AddMessage(f"✅ Deleted domain '{domain_name}' in {gdb_name}")
                except Exception as e:
                    arcpy.AddMessage(f"⚠ Could not delete domain '{domain_name}': {e}")
    
    def __domain_to_create(self, create_csv, gdb_path, gdb_name):
        # List all existing domains
        existing_domains = [d.name for d in arcpy.da.ListDomains(gdb_path)]
        self.__check_domain_headers(create_csv, 'create')
        for index, row in create_csv.iterrows():
            domain_name = row['Domain Name']
            domain_description = row['Description']
            field_type = row['Field Type']
            domain_type = row['Domain Type']
            new_domains = []
            if domain_name not in existing_domains:
                try:
                    arcpy.management.CreateDomain(gdb_path, domain_name, domain_description, field_type, domain_type)
                    new_domains.append(domain_name)  # Update the list of existing domains
                    arcpy.AddMessage(f"✅ Created domain '{domain_name}' in {gdb_name}")
                except Exception as e:
                    arcpy.AddMessage(f"⚠ Could not create domain '{domain_name}': {e}")
            else:
                arcpy.AddMessage(f"⚠ Domain '{domain_name}' already exists in {gdb_name}. Skipping creation.")
        return new_domains
    def from_json_file(self, filename):
        """
        Returns a list of coded domains from the specified JSON file.
        """
        if not os.path.exists(filename):
            print(f"Error: The file {filename} does not exist.")
            return []
        with open(filename, 'r', encoding="utf-8") as f:
            json_string = f.read()
            if not json_string:
                return []
            return json.loads(json_string)    

    def __coded_values_to_create(self, coded_value_json, coded_values_to_create_csv, gdb_path, gdb_name):
        # Load list of coded values from JSON
        if coded_value_json and os.path.exists(coded_value_json):
            codes_dicts = self.from_json_file(coded_value_json)
        else:
            arcpy.AddMessage(f"⚠ Invalid or missing JSON file: {coded_value_json}")
            return
        existing_domains = [d.name for d in arcpy.da.ListDomains(gdb_path)]
        # Add coded values to existing domains
        for index, row in coded_values_to_create_csv.iterrows():
            domain_name = row["Domain Name"]
            #domain_name = codes_dict.get("domain_name")  # Get domain name from dictionary
            if domain_name in existing_domains:
                # Check if the domain exists
                codes_dict = codes_dicts.get(domain_name, {})
                if not codes_dict or len(codes_dict) == 0:
                    arcpy.AddMessage(f"⚠ No codes found for domain '{domain_name}' in JSON file. Skipping...")
                    continue
                for code, description in codes_dict.items():
                    if codes_dict.get("domainType") == "coded":
                        # Validate code and description
                        if code is None or description is None:
                            arcpy.AddMessage(f"⚠ Skipping invalid code or description for domain '{domain_name}'")
                            continue
                        try:
                            arcpy.management.AddCodedValueToDomain(gdb_path, domain_name, code, description)
                            arcpy.AddMessage(f"✅ Added code '{code}' to domain '{domain_name} in {gdb_name}'")
                        except Exception as e:
                            arcpy.AddMessage(f"⚠ Could not add code '{code}' to domain '{domain_name}': {e}")
                    elif codes_dict.get("domainType") == "range":
                        # Handle range domains
                        try:
                            start = codes_dict.get("start")
                            end = codes_dict.get("end")
                            if start is not None and end is not None:
                                arcpy.management.AddRangeToDomain(gdb_path, domain_name, start, end)
                                arcpy.AddMessage(f"✅ Added range '{start} - {end}' to domain '{domain_name}'")
                            else:
                                arcpy.AddMessage(f"⚠ Invalid range for domain '{domain_name}'. Skipping...")
                        except Exception as e:
                            arcpy.AddMessage(f"⚠ Could not add range to domain '{domain_name}': {e}")                
            else:
                arcpy.AddMessage(f"⚠ Domain '{domain_name}' does not exist in {gdb_path}. Skipping...")

    def __assign_domains_to_fields(self, assign_csv, feature_classes, gdb_path, gdb_name):
        self.__check_domain_headers(assign_csv, 'assign')
        existing_domains = [d.name for d in arcpy.da.ListDomains(gdb_path)]
        # Assign domains to fields
        for fc in feature_classes:
            for index, row in assign_csv.iterrows():
                field_name = row['Field_Name']
                domain_name = row['Domain_Name']

                # Check if the domain exists before assigning
                if domain_name in existing_domains:
                    try:
                        arcpy.management.AssignDomainToField(fc, field_name, domain_name)
                        arcpy.AddMessage(f"✅ Assigned domain '{domain_name}' to field '{field_name}' in {fc}")
                    except Exception as e:
                        arcpy.AddMessage(f"⚠ Could not assign domain '{domain_name}' to field '{field_name}': {e}")
                else:
                    arcpy.AddMessage(f"⚠ Domain '{domain_name}' not found in {gdb_name}. Skipping assignment pf '{domain_name}' to field '{field_name}' in {fc}")

    def get_gdb_list(self, root_folder):
        """Get a list of all geodatabases in the specified folder."""
        gdb_list = []
        for dirpath, dirs, files in os.walk(root_folder):
            for dirname in dirs:
                if dirname.endswith(".gdb"):
                    gdb_list.append(os.path.join(dirpath, dirname))
        return gdb_list

    def execute(self, parameters, messages):
        """The source code of the tool."""
        root_folder = parameters[0].valueAsText
        gdb_path = parameters[1].valueAsText
        if parameters[2].valueAsText is not None and parameters[2].valueAsText.endswith(".csv"):
            domain_to_create = pd.read_csv(parameters[2].valueAsText)
        else:
            domain_to_create = None
            arcpy.AddMessage("No or Invalid domain to create csv present")
        if parameters[3].valueAsText is not None and parameters[3].valueAsText.endswith(".csv"):
            domain_to_assign_to_fields = pd.read_csv(parameters[3].valueAsText)
        else:
            domain_to_assign_to_fields = None
            arcpy.AddMessage("No or Invalid domain to assign to field csv present")
        if parameters[4].valueAsText is not None and parameters[4].valueAsText.endswith(".csv"):
            domain_to_delete = pd.read_csv(parameters[4].valueAsText)
        else:
            domain_to_delete = None
            arcpy.AddMessage("No or Invalid domain name to delete csv present")
        if parameters[5].valueAsText is not None and parameters[5].valueAsText.endswith(".csv"):
            coded_values_domain_to_create = pd.read_csv(parameters[5].valueAsText)
        else:
            coded_values_domain_to_create = None
            arcpy.AddMessage("No or Invalid coded value domain csv present")
        if parameters[6].valueAsText is not None and parameters[6].valueAsText.endswith(".json"):
            coded_values_domain = parameters[6].valueAsText
        else:
            coded_values_domain = None
            arcpy.AddMessage("No or Invalid coded value domain json present")
        if parameters[7].valueAsText is not None:
            filter_names = parameters[7].valueAsText
        else:
            filter_names = ""
        shp_type = parameters[8].valueAsText
        shp_list = []

        # Locate all geodatabases
        if root_folder:
            gdb_list = self.get_gdb_list(root_folder)
        else:
            gdb_list = [gdb_path] if gdb_path else []
        if len(gdb_list) == 0:
            arcpy.AddMessage("No geodatabases found in the specified folder.")
            return

        # Process each geodatabase
        for gdb_path in gdb_list:
            arcpy.env.workspace = gdb_path
            # Delete domains 
            if domain_to_delete is not None:
                self.__domain_to_delete(domain_to_delete, gdb_path, os.path.basename(gdb_path))
            if domain_to_create is not None:
                arcpy.AddMessage(f"Creating domains in {gdb_path}")
                self.__domain_to_create(domain_to_create, gdb_path, os.path.basename(gdb_path))
            if coded_values_domain is not None:
                self.__coded_values_to_create(coded_values_domain, coded_values_domain_to_create, gdb_path, os.path.basename(gdb_path))
            # Get feature classes matching the pattern
            for filter_name in filter_names.split(','):
                feature_classes = arcpy.ListFeatureClasses(f"*{filter_name}*", shp_type)
            if domain_to_assign_to_fields is not None:
                self.__assign_domains_to_fields(domain_to_assign_to_fields, feature_classes, gdb_path, os.path.basename(gdb_path))
            
            else:
                arcpy.AddMessage('No gdb in Folder')
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
