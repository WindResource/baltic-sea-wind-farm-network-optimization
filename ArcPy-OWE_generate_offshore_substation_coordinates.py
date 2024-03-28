import arcpy
import os

def generate_offshore_substation_coordinates(output_folder: str, spacing: float) -> None:
    """
    Generates a point feature class for offshore substations based on the feature class in the current map.
    Each point represents a substation, placed according to specified spacing.

    Parameters:
    - output_folder: Path where the output shapefile will be saved.
    - spacing: Desired spacing between turbines, in kilometers.
    """
    
    # Set the spatial reference to a UTM Zone using its Well-Known ID (WKID)
    utm_wkid = 32633  # Example: UTM Zone 33N
    utm_spatial_ref = arcpy.SpatialReference(utm_wkid)

    try:
        # Get the current map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map = aprx.activeMap

        # Get the first layer in the map that starts with 'OSSA'
        input_layer = None
        for layer in map.listLayers():
            if layer.name.startswith('OSSA'):
                input_layer = layer
                break
        
        if input_layer is None:
            arcpy.AddError("No layer starting with 'OSSA' found in the current map.")
            return

        arcpy.AddMessage(f"Processing layer: {input_layer.name}")

        # Output feature class name based on the input layer
        output_feature_class_name = input_layer.name.replace('OSSA', 'OSS') + ".shp"
        output_feature_class = os.path.join(output_folder, output_feature_class_name)

        # Create the output feature class for substations
        arcpy.CreateFeatureclass_management(output_folder, output_feature_class_name, "POINT", spatial_reference=utm_spatial_ref)

        # Add fields to store substation attributes
        arcpy.AddFields_management(output_feature_class, [
            ["StationID", "TEXT", "", "", 50, "Substation ID"],
            ["XCoord", "DOUBLE", "", "", "", "Longitude"],
            ["YCoord", "DOUBLE", "", "", "", "Latitude"]
        ])

        # Prepare to insert new substation point features
        insert_cursor_fields = ["SHAPE@", "StationID", "XCoord", "YCoord"]
        insert_cursor = arcpy.da.InsertCursor(output_feature_class, insert_cursor_fields)

        # Convert spacing from kilometers to meters (1 km = 1000 m)
        spacing_meters = spacing * 1000

        # Initialize a counter for substation ID numbering
        substation_index = 0

        # Generate points within the bounding box of the input layer's extent
        # considering the specified spacing
        with arcpy.da.SearchCursor(input_layer, ["SHAPE@"]) as cursor:
            for shape, in cursor:
                bounding_box = shape.extent
                y = bounding_box.YMin
                while y <= bounding_box.YMax:
                    x = bounding_box.XMin
                    while x <= bounding_box.XMax:
                        # Check if the point is inside the feature's polygon (consider only offshore areas)
                        point = arcpy.Point(x, y)
                        if shape.contains(point):
                            substation_id = f"Substation_{substation_index}"
                            substation_index += 1
                            
                            # Insert the new substation point with its attributes
                            row_values = (point, substation_id, x, y)
                            insert_cursor.insertRow(row_values)
                            
                        x += spacing_meters
                    y += spacing_meters

                #arcpy.AddMessage(f"Generated substations for feature with Substation ID {substation_id}.")

        # Add the generated shapefile to the current map
        map.addDataFromPath(output_feature_class)
        
    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to generate offshore substation coordinates: {e}")
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Example user inputs
    output_folder = str(arcpy.GetParameterAsText(0))  # Output folder path
    spacing = float(arcpy.GetParameterAsText(1))  # Spacing in kilometers

    # Ensure the output directory exists, create it if not
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Call the function with user inputs
    generate_offshore_substation_coordinates(output_folder, spacing)
