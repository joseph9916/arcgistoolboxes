# -*- coding: utf-8 -*-

import arcpy
import pandas as pd
import os

class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Change field names of feature classes in a Folder"
        self.alias = "Change field names of feature classes in a Folder"

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Change field names in a Folder"
        self.description = "Change field names of feature classes in a Folder"

    def getParameterInfo(self):
        """Define the tool parameters."""
        params = [
            arcpy.Parameter(
                displayName = "GDB FOLDER",
                name = "GDB FOLDER",
                datatype = "DEFolder",
                parameterType = "optional",
                direction = "Input"),
            arcpy.Parameter(
                displayName = "GDBS",
                name = "GDBS",
                datatype = "DEWorkspace",
                parameterType = "optional",
                direction = "Input",
                multiValue = True),
             arcpy.Parameter(
                displayName = "Feature Class Names",
                name = "Feature Class Names",
                datatype = "DEFeatureClass",
                parameterType = "optional",
                direction = "Input",
                multiValue = True),
            arcpy.Parameter(
                displayName = "Field Change CSV",
                name = "Field Change CSV",
                datatype = "DEFile",
                parameterType = "optional",
                direction = "Input"),
            arcpy.Parameter(
                displayName = "Field ADD CSV",
                name = "Field ADD CSV",
                datatype = "DEFile",
                parameterType = "optional",
                direction = "Input"),
            arcpy.Parameter(
                displayName = "Field Delete CSV",
                name = "Field Delete CSV",
                datatype = "DEFile",
                parameterType = "optional",
                direction = "Input"),
            arcpy.Parameter(
                displayName = "Filter Name (separate more than one with a comma)",
                name = "Filter Name",
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
        params[7].filter.type = "ValueList"
        params[7].filter.list = ["Point", "Polyline", "Polygon"]
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

    def __check_field_headers(self, fields_to_check, identifier):
        if identifier == 'change':
            headers = ['OLD NAMES', 'NEW NAMES', 'NEW ALIAS', 'LENGTH']
        if identifier == 'add':
            headers = ['Field Name', 'Alias', 'TYPE', 'PRECISION', 'LENGTH']
        if identifier == 'delete':
            headers = ['TO BE DELETED']
        for header in headers:
            if header not in fields_to_check.columns.to_list():
                raise NameError(f"{headers} headers must be in these name not {fields_to_check.columns.to_list()}")
        

    def __change_field_name(self, fc, fields_to_change):
        self.__check_field_headers(fields_to_change, 'change')
        fields_list = arcpy.ListFields(fc)
        # Check if the fields to change exist in the feature class
        fields_dict = {field.name: field for field in fields_list}
        for index, row in fields_to_change.iterrows():
            old_name = row['OLD NAMES']
            new_name = row['NEW NAMES']
            new_alias = row['NEW ALIAS']
            new_length = row['LENGTH']
            field_to_change = fields_dict.get(old_name)
            if field_to_change is None:
                arcpy.AddMessage(f"Field {old_name} does not exist in {fc}. Skipping...")
                continue
            try:
                arcpy.AddMessage(f"Changing {old_name} of type {field_to_change.type} in {fc}")
                if field_to_change.type == 'String':
                    if pd.isna(new_name) or new_name == "" or str(new_name).lower() == "nan":
                        new_name = old_name
                    if pd.isna(new_length) or new_length == "" or str(new_length).lower() == "nan":
                        new_length = 255  # Default length for text fields
                    else:
                        try:
                            new_length = int(new_length)
                        except Exception:
                            new_length = 255
                    arcpy.management.AlterField(fc, old_name, new_name, new_alias, field_length=new_length)
                    arcpy.AddMessage(f"Changed {old_name} to {new_name} with length {new_length} in {fc}")
                else:
                    arcpy.management.AlterField(fc, old_name, new_name, new_alias)
                    arcpy.AddMessage(f"Changed {old_name} to {new_name} in {fc}")
                
            except Exception as e:
                arcpy.AddMessage(f"Could not rename {old_name} in {fc}: {e}")
        # List to store found geodatabases

    def __add_field_name(self, fc, fields_to_add):
        self.__check_field_headers(fields_to_add, 'add')
        for index, row in fields_to_add.iterrows():
            Name = row['Field Name']
            Alias = row['Alias']
            field_type = row["TYPE"].upper()
            if field_type not in ['TEXT', 'SHORT', 'LONG', 'FLOAT', 'DOUBLE', 'DATE', 'BLOB', 'RASTER']:
                raise ValueError(f"Invalid field type: {field_type}. Must be one of TEXT, SHORT, LONG, FLOAT, DOUBLE, DATE, BLOB, RASTER.")
            precision = row['PRECISION']
            length = row['LENGTH']
            try:
                if field_type == "TEXT":
                    arcpy.management.AddField(fc,Name, field_type, field_length=length, field_alias=Alias)
                elif field_type in ["SHORT", "LONG", "FLOAT", "DOUBLE"]:
                    if pd.isna(precision) or precision == "" or str(precision).lower() == "nan":
                        precision = 0  # Default precision for numeric fields
                    arcpy.management.AddField(fc,Name, field_type, field_precision=precision, field_alias=Alias)
                else:
                    arcpy.management.AddField(fc,Name, field_type, field_alias=Alias)
                arcpy.AddMessage(f"Added {Name} to {fc}")
            except Exception as e:
                arcpy.AddMessage(f"Could not add {Name} in {fc}: {e}")

    def __delete_field_name(self, fc, fields_to_delete):
        self.__check_field_headers(fields_to_delete, 'delete')
        for index, row in fields_to_delete.iterrows():
            Name = row['TO BE DELETED']
            try:
                arcpy.management.DeleteField(fc, Name)
                arcpy.AddMessage(f"This field {Name} has been deleted")
            except Exception as e:
                arcpy.AddMessage(f"Could not delete {Name} in {fc}: {e}")


    def execute(self, parameters, messages):
        """The source code of the tool."""

        folder = parameters[0].valueAsText
        gdb_paths = parameters[1].valueAsText
        feature_classes_str = parameters[2].valueAsText
        if feature_classes_str is not None and feature_classes_str != "":
            feature_classes = [fc.strip().replace("'", "") for fc in feature_classes_str.split(";")]
        else:
            feature_classes = []
        gdb_list = []
        if gdb_paths is not None and gdb_paths != "":
            for gdb_path in gdb_paths.split(";"):
                clean_path = gdb_path.strip().replace("'", "")
                if os.path.exists(clean_path):
                    gdb_list.append(clean_path)
                else:
                    arcpy.AddWarning(f"The provided GDB path {gdb_path} does not exist. Skipping...")
        if (gdb_paths is None or gdb_paths == "") and (folder is None or folder == "") and (feature_classes_str is None or feature_classes_str == ""):
            arcpy.AddMessage(f"{feature_classes_str}")
            raise ValueError("You must provide either a GDB folder or a GDB path or feature classes.")
        if parameters[3].valueAsText is not None and parameters[3].valueAsText.endswith(".csv"):
            fields_to_change = pd.read_csv(parameters[3].valueAsText)
        else:
            fields_to_change = None
            arcpy.AddMessage("No or Invalid fields name to change csv present")
        if parameters[4].valueAsText is not None and parameters[4].valueAsText.endswith(".csv"):
            fields_to_add = pd.read_csv(parameters[4].valueAsText)
        else:
            fields_to_add = None
            arcpy.AddMessage("No fields name to add csv present")
        if parameters[5].valueAsText is not None and parameters[5].valueAsText.endswith(".csv"):
            fields_to_delete = pd.read_csv(parameters[5].valueAsText)
        else:
            fields_to_delete = None
            arcpy.AddMessage("No fields name to delete csv present")
        if parameters[6].valueAsText is not None:
            filter_names = parameters[6].valueAsText
        else:
            filter_names = []
        shp_type = parameters[7].valueAsText
        shp_list = []

        arcpy.AddMessage("Start")
        if folder is not None and folder != "":
            # Walk through the directory to find .gdb folders
            for dirpath, dirnames, filenames in os.walk(folder):
                for dirname in dirnames:
                    if dirname.endswith(".gdb"):  # Check if the folder is a geodatabase
                        gdb_list.append(os.path.join(dirpath, dirname))
            #raise TypeError("{}headers must be in these name".format(gdb_list))
        if len(gdb_list) > 0:
            #raise TypeError("headers must be in these name")
            for gdb_path in gdb_list:
                arcpy.env.workspace = gdb_path
                if isinstance(filter_names, list):
                    filter_list = []
                    for item in filter_names:
                        filter_list.extend(str(item).split(","))
                for filter_name in filter_list:
                    if filter_name != "":
                        for feature_class in arcpy.ListFeatureClasses(f"*{filter_name}*", shp_type):
                            if feature_class not in feature_classes:
                                feature_classes.append(feature_class)
                        arcpy.AddMessage(f"Feature classes with filter {filter_name} are {feature_classes}")

        else:
            arcpy.AddMessage('No gdb in Folder')
            if len(feature_classes) == 0:
                arcpy.AddMessage("No feature classes found in the specified geodatabases.")
                return
        for feature_class in feature_classes:
            if not arcpy.Exists(feature_class):
                arcpy.AddWarning(f"The feature class {feature_class} does not exist. Skipping...")
                continue
            if fields_to_change is not None:
                self.__change_field_name(feature_class, fields_to_change)
            if fields_to_add is not None:
                self.__add_field_name(feature_class, fields_to_add)
            if fields_to_delete is not None:
                self.__delete_field_name(feature_class, fields_to_delete)
            shp_list.append(feature_class)
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
