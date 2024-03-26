import arcpy
import os

def create_wind_turbine_shapefile(output_folder: str, turbine_capacity: float, turbine_diameter: float, turbine_spacing: float) -> None:
    """
    Generates a point feature class for wind turbines based on the feature class in the current map.
    Each point represents a wind turbine, placed according to specified spacing, and includes attributes for identification and characteristics.

    Parameters:
    - output_folder: Path where the output shapefile will be saved.
    - turbine_capacity: Capacity of each wind turbine in megawatts (MW).
    - turbine_diameter: Diameter of each wind turbine in meters.
    - turbine_spacing: Desired spacing between turbines, in terms of turbine diameters.
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

        # Create one output feature class for all turbine points
        output_feature_class = os.path.join(output_folder, "AllWindTurbines.shp")
        arcpy.CreateFeatureclass_management(output_folder, "AllWindTurbines.shp", "POINT", spatial_reference=utm_spatial_ref)

        # Add necessary fields to the output feature class
        arcpy.AddFields_management(output_feature_class, [
            ["TurbineID", "TEXT", "", "", 50, "Turbine ID"],
            ["XCoord", "DOUBLE", "", "", "", "Longitude"],
            ["YCoord", "DOUBLE", "", "", "", "Latitude"],
            ["Capacity", "DOUBLE", "", "", "", "Capacity (MW)"],
            ["Diameter", "DOUBLE", "", "", "", "Diameter (m)"],
            ["FeatureFID", "LONG", "", "", "", "Feature FID"],
            ["Country", "TEXT", "", "", 100, "Country"],
            ["Name", "TEXT", "", "", 100, "Name"],
            ["Status", "TEXT", "", "", 50, "Status"]
        ])

        # Prepare to insert new turbine point features
        insert_cursor_fields = ["SHAPE@", "TurbineID", "XCoord", "YCoord", "Capacity", "Diameter", "FeatureFID", "Country", "Name", "Status"]
        insert_cursor = arcpy.da.InsertCursor(output_feature_class, insert_cursor_fields)

        # Iterate through each feature in the input layer
        search_fields = ["SHAPE@", "OID@", "Country", "Name", "Status"]
        with arcpy.da.SearchCursor(input_layer, search_fields) as feature_cursor:
            for feature_index, (shape, fid, country, name, status) in enumerate(feature_cursor):
                # Reset turbine index for each feature
                turbine_index = 0
                
                # Calculate the spacing in meters
                spacing = turbine_spacing * turbine_diameter
                
                # Generate points within the feature's bounding box
                bounding_box = shape.extent
                y = bounding_box.YMin
                while y <= bounding_box.YMax:
                    x = bounding_box.XMin
                    while x <= bounding_box.XMax:
                        point = arcpy.Point(x, y)
                        if shape.contains(point):  # Check if the point is inside the feature's polygon
                            turbine_id = f"Turbine_{feature_index}_{turbine_index}"
                            turbine_index += 1
                            
                            # Insert the new turbine point with its attributes
                            row_values = (point, turbine_id, x, y, turbine_capacity, turbine_diameter, fid, country, name, status)
                            insert_cursor.insertRow(row_values)
                        x += spacing
                    y += spacing

                arcpy.AddMessage(f"Processed feature with FID {fid}, Country {country}, Name {name}, and Status {status} with turbines.")
        
        # Add the generated shapefile to the current map
        map.addDataFromPath(output_feature_class)

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to process the shapefile: {e}")
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Example user inputs
    turbine_folder = arcpy.GetParameterAsText(0)  # The folder where the output shapefile will be saved
    turbine_capacity = float(arcpy.GetParameterAsText(1))  # Capacity of each wind turbine in MW
    turbine_diameter = float(arcpy.GetParameterAsText(2))  # Diameter of each wind turbine in meters
    turbine_spacing = float(arcpy.GetParameterAsText(3))  # Desired spacing between turbines, in terms of turbine diameters

    # Ensure the output directory exists, create it if not
    if not os.path.exists(turbine_folder):
        os.makedirs(turbine_folder)

    # Call the main function with the parameters collected from the user
    create_wind_turbine_shapefile(turbine_folder, turbine_capacity, turbine_diameter, turbine_spacing)

    arcpy.AddMessage("Wind turbine point features creation complete.")
