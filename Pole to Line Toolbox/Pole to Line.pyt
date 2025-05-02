# -*- coding: utf-8 -*-

import arcpy
import os

class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "HT Points to HT Line tool"
        self.alias = "HT Points to HT Line tool"

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Points to Line tool"
        self.description = ""

    def getParameterInfo(self):
        """Define the tool parameters."""
        params = [
            arcpy.Parameter(
                displayName = "Input HT Points Layer",
                name = "Input HT Points Layer",
                datatype = "DEFeatureClass",
                parameterType = "Required",
                direction = "Input"),
            arcpy.Parameter(
                displayName = "Output HT Line Layer",
                name = "Output HT Line Layer",
                datatype = "DEFeatureClass",
                parameterType = "Required",
                direction = "Output")
            
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
        input_points_layer = parameters[0].valueAsText
        output_lines_layer = parameters[1].valueAsText

        # Create output feature class
        try:
            if arcpy.Exists(output_lines_layer):
                arcpy.Delete_management(output_lines_layer)  # Delete if exists to avoid errors

            # Get spatial reference from input layer
            spatial_ref = arcpy.Describe(input_points_layer).spatialReference

            # get the workspace, so that we can create the feature class in the same place.
            output_workspace = os.path.dirname(output_lines_layer)
            output_name = os.path.basename(output_lines_layer)

            arcpy.CreateFeatureclass_management(
                out_path=output_workspace,
                out_name=output_name,
                geometry_type="POLYLINE",
                spatial_reference=spatial_ref
            )
            
            # Add necessary fields
            arcpy.AddField_management(output_lines_layer, "feedername", "TEXT")
            arcpy.AddField_management(output_lines_layer, "HT_Pole_ID", "TEXT")
            arcpy.AddField_management(output_lines_layer, "Connect_Through_ID", "TEXT")
            arcpy.AddField_management(output_lines_layer, "Conductor_Type", "TEXT")
            arcpy.AddField_management(output_lines_layer, "Conductor_Size", "TEXT")
            # Read points into a dictionary {line_ID: point geometry}
            point_dict = {}
            with arcpy.da.SearchCursor(input_points_layer, ["ht_pole_id", "SHAPE@"]) as cursor:
                for ht_pole_id, shape in cursor:
                    if ht_pole_id is not None:
                        point_dict[ht_pole_id] = shape
            

            """ Create lines where line_ID matches connect_thru_ID"""
            #Opens the input layer table for searching and includes these field names
            with arcpy.da.SearchCursor(input_points_layer, ["ht_pole_id", "connect_through_id", 
                                                            "feedername", "ht_11kv_aluminium_conductor", 
                                                            "ht_11kv_aluminium_size","SHAPE@"]) as cursor:
                #Opens the output layer table for inserting these field names
                with arcpy.da.InsertCursor(output_lines_layer, ["SHAPE@", "HT_Pole_ID", "Connect_Through_ID", "feedername",
                                                               "Conductor_Type", "Conductor_Size"]) as insert_cursor: #changed fields to match added fields.
                    for ht_pole_id, connect_through_id, feedename, Conductor_Type, Conductor_Size, end_point in cursor:
                        if connect_through_id in point_dict and connect_through_id is not None:  # Ensure connection exists
                            start_point = point_dict[connect_through_id]  # Get start point geometry
                            polyline = arcpy.Polyline(arcpy.Array([start_point.firstPoint, end_point.firstPoint]))
                            insert_cursor.insertRow([polyline, ht_pole_id, connect_through_id, feedename, Conductor_Type, Conductor_Size])

        except arcpy.ExecuteError:
            arcpy.AddErrorMessage(arcpy.GetMessages(2))
        except Exception as e:
            arcpy.AddErrorMessage(str(e))

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
