import arcpy
import os

def create_wind_turbine_shapefile(input_folder: str, output_folder: str, turbine_capacity: float, turbine_diameter: float, turbine_spacing: float) -> None:
    """
    Generates a point feature class for wind turbines based on the areas defined in the shapefiles within a specified folder. 
    Each point represents a wind turbine, placed according to specified spacing, and includes attributes for identification and characteristics.

    Parameters:
    - input_folder: Path to the folder containing input shapefiles representing wind farm areas.
    - turbine_spacing: Desired spacing between turbines, in terms of turbine diameters.
    - output_folder: Path where the output shapefile will be saved.
    - turbine_capacity: Capacity of each wind turbine in megawatts (MW).
    - turbine_diameter: Diameter of each wind turbine in meters.
    """
    
    # Set the spatial reference to a UTM Zone using its Well-Known ID (WKID)
    utm_wkid = 32633  # Example: UTM Zone 33N
    utm_spatial_ref = arcpy.SpatialReference(utm_wkid)

    try:
        # Ensure the input folder exists
        if not os.path.exists(input_folder):
            arcpy.AddError(f"Input folder '{input_folder}' does not exist.")
            return

        # Set the ArcPy environment workspace to the input folder
        arcpy.env.workspace = input_folder
        
        # Get a reference to the currently active map frame
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map_obj = aprx.activeMap

        # Get the first shapefile in the folder to process
        shapefiles = arcpy.ListFeatureClasses()
        if not shapefiles:
            arcpy.AddError("No shapefiles found in the input folder.")
            return

        first_shapefile = shapefiles[0]
        arcpy.AddMessage(f"Processing shapefile: {first_shapefile}")

        # Create one output feature class for all turbine points
        output_feature_class = os.path.join(output_folder, "AllWindTurbines.shp")
        arcpy.management.CreateFeatureclass(output_folder, "AllWindTurbines.shp", "POINT", spatial_reference=utm_spatial_ref)

        # Add necessary fields to the output feature class
        arcpy.management.AddFields(output_feature_class, [
            ["TurbineID", "TEXT", "", "", 50, "Turbine ID"],
            ["XCoord", "DOUBLE", "", "", "", "Longitude"],
            ["YCoord", "DOUBLE", "", "", "", "Latitude"],
            ["Capacity", "DOUBLE", "", "", "", "Capacity (MW)"],
            ["Diameter", "DOUBLE", "", "", "", "Diameter (m)"],
            ["FeatureFID", "LONG", "", "", "", "Feature FID"],
            ["Country", "TEXT", "", "", 100, "Country"],
            ["Name", "TEXT", "", "", 100, "Name"]
        ])

        # Prepare to insert new turbine point features
        insert_cursor_fields = ["SHAPE@", "TurbineID", "XCoord", "YCoord", "Capacity", "Diameter", "FeatureFID", "Country", "Name"]
        insert_cursor = arcpy.da.InsertCursor(output_feature_class, insert_cursor_fields)

        # Iterate through each feature in the shapefile
        search_fields = ["SHAPE@", "OID@", "Country", "Name"]
        with arcpy.da.SearchCursor(first_shapefile, search_fields) as feature_cursor:
            for feature_index, (shape, fid, country, name) in enumerate(feature_cursor):
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
                            turbine_id = f"Turbine_{feature_index}_{len(list(arcpy.da.SearchCursor(output_feature_class, 'TurbineID')))}"
                            # Insert the new turbine point with its attributes
                            row_values = (point, turbine_id, x, y, turbine_capacity, turbine_diameter, fid, country, name)
                            insert_cursor.insertRow(row_values)
                        x += spacing
                    y += spacing

                arcpy.AddMessage(f"Processed feature with FID {fid}, Country {country}, and Name {name} with turbines.")

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to process the shapefile: {e}")
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Example user inputs
    windfarm_folder = arcpy.GetParameterAsText(0)  # The folder containing the input shapefiles representing the wind farm areas
    turbine_folder = arcpy.GetParameterAsText(1)  # The folder where the output shapefile will be saved
    turbine_capacity = float(arcpy.GetParameterAsText(2))  # Capacity of each wind turbine in MW
    turbine_diameter = float(arcpy.GetParameterAsText(3))  # Diameter of each wind turbine in meters
    turbine_spacing = float(arcpy.GetParameterAsText(4))  # Desired spacing between turbines, in terms of turbine diameters

    # Ensure the output directory exists, create it if not
    if not os.path.exists(turbine_folder):
        os.makedirs(turbine_folder)

    # Call the main function with the parameters collected from the user
    create_wind_turbine_shapefile(windfarm_folder, turbine_folder, turbine_capacity, turbine_diameter, turbine_spacing,)

    arcpy.AddMessage("Wind turbine point features creation complete.")
