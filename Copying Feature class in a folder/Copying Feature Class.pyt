# -*- coding: utf-8 -*-

import arcpy
import os


class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Copying Feature Class"
        self.alias = "Copying Feature Class"

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Tool"
        self.description = ""

    def getParameterInfo(self):
        """Define the tool parameters."""
        params = [
            arcpy.Parameter(
                displayName = "Feature Class Name",
                name = "Feature Class Name",
                datatype = "DEFeatureClass",
                parameterType = "Required",
                direction = "Input"),
            arcpy.Parameter(
                displayName = "Output GDB FOLDER",
                name = "Output GDB FOLDER",
                datatype = "DEFolder",
                parameterType = "required",
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

    def execute(self, parameters, messages):
        """The source code of the tool."""
        input_feature_class = parameters[0].valueAsText
        output_gdb_folder = parameters[1].valueAsText
        feature_class_name = os.path.basename(input_feature_class)
        # Locate all geodatabases
        gdb_list = self.get_gdb_list(output_gdb_folder)
        # Check if the geodatabase list is empty
        if len(gdb_list) == 0:
            arcpy.AddMessage("No geodatabases found in the specified folder.")
            return
        # Process each geodatabase
        for gdb_path in gdb_list:
            arcpy.env.workspace = gdb_path
            output_feature_class = os.path.join(gdb_path, feature_class_name)
            # Check if the feature class already exists
            if arcpy.Exists(output_feature_class):
                arcpy.delete_management(output_feature_class)  # Delete if exists to avoid errors
            # Copy the feature class to the geodatabase
            arcpy.CopyFeatures_management(input_feature_class, output_feature_class)
            arcpy.AddMessage(f"Copied {input_feature_class} to {output_feature_class}")
        arcpy.AddMessage("Copying completed successfully.")
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
