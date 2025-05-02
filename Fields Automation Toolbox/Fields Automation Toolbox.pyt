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
                parameterType = "required",
                direction = "Input"),
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
                displayName = "Filter Name",
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
            headers = ('OLD NAMES', 'NEW NAMES', 'NEW ALIAS')
        if identifier == 'add':
            headers = ('Field Name', 'Alias', 'Type', 'Precision', 'Length')
        if identifier == 'delete':
            headers = ['TO BE DELETED']
        for header in headers:
            if header not in fields_to_check.columns.to_list():
                raise NameError(f"{headers} headers must be in these name not {fields_to_check.columns.to_list()}")
        

    def __change_field_name(self, fc, fields_to_change):
        self.__check_field_headers(fields_to_change, 'change')
        for index, row in fields_to_change.iterrows():
            old_name = row['OLD NAMES']
            new_name = row['NEW NAMES']
            new_alias = row['NEW ALIAS']
            try:
                arcpy.management.AlterField(fc, old_name, new_name, new_alias)
            except Exception as e:
                print(f"Could not rename {old_name} in {fc}: {e}")
        # List to store found geodatabases   

    def __add_field_name(self, fc, fields_to_add):
        self.__check_field_headers(fields_to_add, 'add')
        for index, row in fields_to_add.iterrows():
            Name = row['Field Name']
            Alias = row['Alias']
            field_type = row["Type"]
            precision = row['Precision']
            length = row['Length']
            try:
                if field_type == "TEXT":
                    arcpy.management.AddField(fc,Name, field_type, field_length=length, field_alias=Alias)
                else:
                    arcpy.management.AddField(fc,Name, field_type, field_precision=9, field_length=length, field_alias=Alias)
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
        if parameters[1].valueAsText is not None and parameters[1].valueAsText.endswith(".csv"):
            fields_to_change = pd.read_csv(parameters[1].valueAsText)
        else:
            fields_to_change = None
            arcpy.AddMessage("No or Invalid fields name to change csv present")
        if parameters[2].valueAsText is not None and parameters[2].valueAsText.endswith(".csv"):
            fields_to_add = pd.read_csv(parameters[2].valueAsText)
        else:
            fields_to_add = None
            arcpy.AddMessage("No fields name to add csv present")
        if parameters[3].valueAsText is not None and parameters[3].valueAsText.endswith(".csv"):
            fields_to_delete = pd.read_csv(parameters[3].valueAsText)
        else:
            fields_to_delete = None
            arcpy.AddMessage("No fields name to delete csv present")
        if parameters[4].valueAsText is not None:
            filter_name = parameters[4].valueAsText
        else:
            filter_name = ""
        shp_type = parameters[5].valueAsText
        gdb_list = []
        shp_list = []

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
                feature_classes = arcpy.ListFeatureClasses(f"*{filter_name}*", shp_type)
                for fc in feature_classes:
                    if fields_to_change is not None:
                        self.__change_field_name(fc, fields_to_change)
                    if fields_to_add is not None:
                        self.__add_field_name(fc, fields_to_add)
                    if fields_to_delete is not None:
                        self.__delete_field_name(fc, fields_to_delete)
        else:
            arcpy.AddMessage('No gdb in Folder')
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
