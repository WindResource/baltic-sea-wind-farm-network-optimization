import arcpy
import os
import numpy as np

def generate_offshore_substation_coordinates(output_folder: str, spacing: float) -> None:
    """
    Generates a point feature class for offshore substations based on the feature class in the current map.
    Each point represents a substation, placed according to specified spacing.

    Parameters:
    - output_folder: Path where the output shapefile will be saved.
    - spacing: Desired spacing between substations, in kilometers.
    """
    
    # Set the spatial reference to a UTM Zone using its Well-Known ID (WKID)
    utm_wkid = 32633  # Example: UTM Zone 33N
    utm_spatial_ref = arcpy.SpatialReference(utm_wkid)

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
    output_feature_class_name = input_layer.name.replace('OSSA', 'OSSC') + ".shp"
    output_feature_class = os.path.join(output_folder, output_feature_class_name)
    
    # Reproject input_layer to UTM
    input_layer = arcpy.management.Project(input_layer, os.path.join("in_memory", "reprojected_layer"), utm_spatial_ref)[0]

    # Create the output feature class for substations
    arcpy.CreateFeatureclass_management(output_folder, output_feature_class_name, "POINT", spatial_reference=utm_spatial_ref)

    # Add fields to store substation attributes
    arcpy.AddFields_management(output_feature_class, [
        ["StationID", "TEXT", "", "", 50, "Substation ID"],
        ["XCoord", "DOUBLE", "", "", "", "Longitude"],
        ["YCoord", "DOUBLE", "", "", "", "Latitude"]
    ])

    # Prepare to insert new substation point features
    insert_cursor_fields = ["SHAPE@", "StationID", "XCoord", "YCoord", "Territory", "ISO"]
    insert_cursor = arcpy.da.InsertCursor(output_feature_class, insert_cursor_fields)

    # Add fields 'TERRITORY1' and 'ISO_TER1' if they do not exist
    existing_fields = [field.name for field in arcpy.ListFields(output_feature_class)]
    for field_name in ["Territory", "ISO"]:
        if field_name not in existing_fields:
            arcpy.AddField_management(output_feature_class, field_name, "TEXT")
    
    # Initialize substation index counter
    substation_index = 1

    # Generate points within the bounding box of the input layer's extent
    # considering the specified spacing using NumPy
    with arcpy.da.SearchCursor(input_layer, ["SHAPE@", "TERRITORY1", "ISO_TER1"]) as cursor:
        for row in cursor:
            shape = row[0]
            territory = row[1]
            iso_territory = row[2]
            extent = shape.extent
            # Convert extent to numpy array for easier manipulation
            extent = np.array([extent.XMin, extent.YMin, extent.XMax, extent.YMax])
            # Calculate number of points in x and y directions
            num_points_x = int((extent[2] - extent[0]) / (spacing * 1000))
            num_points_y = int((extent[3] - extent[1]) / (spacing * 1000))
            # Generate grid of x and y coordinates
            x_coords = np.linspace(extent[0], extent[2], num_points_x)
            y_coords = np.linspace(extent[1], extent[3], num_points_y)
            # Generate meshgrid of x and y coordinates
            xx, yy = np.meshgrid(x_coords, y_coords)
            # Flatten meshgrid to get 1D arrays
            flat_x = xx.flatten()
            flat_y = yy.flatten()
            # Create points and insert them into feature class
            for x, y in zip(flat_x, flat_y):
                point = arcpy.Point(x, y)
                if shape.contains(point):
                    substation_id = f"{iso_territory}_{substation_index}"  # Generate substation ID
                    substation_index += 1  # Increment substation index
                    insert_cursor.insertRow((point, substation_id, round(x, 6), round(y, 6), territory, iso_territory))  # Rounding coordinates to avoid precision issues
            # Reset substation index for next shape
            substation_index = 0



    # Add the generated shapefile to the current map
    map.addDataFromPath(output_feature_class)
        
if __name__ == "__main__":
    output_folder = str(arcpy.GetParameterAsText(0))  # Output folder path
    spacing = float(arcpy.GetParameterAsText(1))  # Spacing in kilometers

    # Ensure the output directory exists, create it if not
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Call the function with user inputs
    generate_offshore_substation_coordinates(output_folder, spacing)
