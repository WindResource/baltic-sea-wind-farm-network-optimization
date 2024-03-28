import arcpy
import os

def generate_windfarm_coordinates(output_folder: str) -> None:
    """
    Generates a point feature class for wind farm connection points based on the wind farm feature layer in the current map.
    Each point represents a wind farm connection point, the midpoint of the corresponding wind farm feature.

    Parameters:
    - output_folder: Path where the output shapefile will be saved.
    """
    
    # Set the spatial reference to a UTM Zone using its Well-Known ID (WKID)
    utm_wkid = 32633  # Example: UTM Zone 33N
    utm_spatial_ref = arcpy.SpatialReference(utm_wkid)

    try:
        # Get the current map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map = aprx.activeMap

        # Get the first layer in the map that starts with 'WFA'
        input_layer = None
        for layer in map.listLayers():
            if layer.name.startswith('WFA'):
                input_layer = layer
                break
        
        if input_layer is None:
            arcpy.AddError("No layer starting with 'WFA' found in the current map.")
            return

        arcpy.AddMessage(f"Processing layer: {input_layer.name}")

        # Modify output feature class name, WFC is wind farm connection
        output_feature_class_name = input_layer.name.replace('WFA', 'WFC') + ".shp"
        output_feature_class = os.path.join(output_folder, output_feature_class_name)

        # Create one output feature class for all wind farm connection point
        arcpy.CreateFeatureclass_management(output_folder, output_feature_class_name, "POINT", spatial_reference=utm_spatial_ref)

        # Add necessary fields to the output feature class
        arcpy.AddFields_management(output_feature_class, [
            ["FarmID", "TEXT", "", "", 50, "Wind Farm ID"]
        ])

        # Prepare to insert new connection point features
        insert_cursor_fields = ["SHAPE@", "FarmID"]
        insert_cursor = arcpy.da.InsertCursor(output_feature_class, insert_cursor_fields)

        # Iterate through each feature in the input layer
        search_fields = ["SHAPE@", "OID@"]  # We only need the geometry and object ID
        with arcpy.da.SearchCursor(input_layer, search_fields) as feature_cursor:
            for shape, oid in feature_cursor:
                # Calculate the midpoint of the feature
                midpoint = shape.centroid
                
                # Insert the new connection point with its attribute
                farm_id = f"Farm_{oid}"
                row_values = (midpoint, farm_id)
                insert_cursor.insertRow(row_values)
        
        # Add the generated shapefile to the current map
        map.addDataFromPath(output_feature_class)

        arcpy.AddMessage("Wind farm connection point features creation complete.")

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to process the shapefile: {e}")
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred: {e}")

# Test the function
if __name__ == "__main__":
    # Example output folder
    output_folder = arcpy.GetParameterAsText(0)  # The folder where the output shapefile will be saved

    # Ensure the output directory exists, create it if not
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Call the main function with the parameter collected from the user
    generate_windfarm_coordinates(output_folder)
