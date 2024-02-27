import arcpy
import os

def create_wind_turbine_shapefile(input_folder: str, turbine_spacing: float, output_folder: str, map_frame_name: str) -> None:
    """
    Create a shapefile feature class containing wind turbine points with WGS 1984 Web Mercator (auxiliary sphere)
    coordinate system and add it to the project map.

    Parameters:
    - input_folder (str): The folder containing the input shapefiles representing the wind farm areas.
    - turbine_spacing (float): The desired spacing between wind turbines in the same units as the input shapefiles.
    - output_folder (str): The name of the output shapefile feature class to store wind turbine locations.
    - map_frame_name (str): The name of the map frame in ArcGIS Pro where the wind turbines will be visualized.

    Returns:
    - None
    """

    # Check if input folder exists
    if not os.path.exists(input_folder):
        arcpy.AddError(f"Input folder '{input_folder}' does not exist.")
        return

    # Create a new point feature class for wind turbine locations
    output_feature_class_name = "WindTurbines.shp"
    output_feature_class = os.path.join(output_folder, output_feature_class_name)

    # Set spatial reference for WGS 1984 Web Mercator (auxiliary sphere)
    spatial_reference = arcpy.SpatialReference(3857)  # 3857 is the WKID for WGS 1984 Web Mercator (auxiliary sphere)

    # Create the point feature class with the specified spatial reference
    arcpy.management.CreateFeatureclass(output_folder, output_feature_class_name, "POINT", spatial_reference=spatial_reference)

    # Add fields to store turbine information
    arcpy.management.AddFields(output_feature_class, [
        ["TurbineID", "TEXT", "Turbine ID"],
        ["Capacity", "DOUBLE", "Capacity"],
        ["XCoord", "DOUBLE", "X Coordinate"],
        ["YCoord", "DOUBLE", "Y Coordinate"]
    ])

    # Set workspace to the input folder
    arcpy.env.workspace = input_folder

    # Get a list of all shapefiles in the input folder
    shapefiles = arcpy.ListFeatureClasses()

    if not shapefiles:
        arcpy.AddError("No shapefiles found in the input folder.")
        return

    # Iterate over all shapefiles in the input folder
    for input_shapefile in shapefiles:
        arcpy.AddMessage(f"Processing shapefile: {input_shapefile}")

        # Use search cursor to get the extent of the input polygon
        with arcpy.da.SearchCursor(input_shapefile, ["SHAPE@", "SHAPE@XY"]) as cursor:
            for row in cursor:
                extent = row[0].extent

        # Generate a grid of points within the bounding box of the polygon
        with arcpy.da.InsertCursor(output_feature_class, ["SHAPE@", "TurbineID", "Capacity", "XCoord", "YCoord"]) as cursor:
            num_turbines_x = int(extent.width / turbine_spacing)
            num_turbines_y = int(extent.height / turbine_spacing)

            print(f"Bounding Box Dimensions: Width = {extent.width}, Height = {extent.height}")
            print(f"Calculated Number of Turbines: X = {num_turbines_x}, Y = {num_turbines_y}")

            for i in range(num_turbines_x):
                for j in range(num_turbines_y):
                    x_coord = extent.XMin + i * turbine_spacing
                    y_coord = extent.YMin + j * turbine_spacing

                    turbine_id = f"Turbine_{i}_{j}"
                    capacity = 0.0  # You can set the capacity based on your requirements

                    cursor.insertRow((
                        arcpy.Point(x_coord, y_coord),
                        turbine_id,
                        capacity,
                        x_coord,
                        y_coord
                    ))

            arcpy.AddMessage(f"{num_turbines_x * num_turbines_y} turbines created.")


        arcpy.AddMessage(f"Shapefile '{input_shapefile}' successfully processed.")

        # Add the point feature class to the specified map frame
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map_obj = aprx.listMaps(map_frame_name)[0]
        map_obj.addDataFromPath(output_feature_class)

if __name__ == "__main__":
    # Get the input folder, output folder, map frame name, and turbine spacing from the user input
    input_folder: str = arcpy.GetParameterAsText(0)
    output_folder: str = arcpy.GetParameterAsText(1)
    turbine_spacing: float = float(arcpy.GetParameterAsText(2))
    map_frame_name: str = arcpy.GetParameterAsText(3)

    # Validate input parameters
    if not os.path.isdir(output_folder):
        arcpy.AddError("Output folder is not valid.")
    else:
        # Create wind turbine shapefile and add wind turbine points to the map
        create_wind_turbine_shapefile(input_folder, turbine_spacing, output_folder, map_frame_name)

        # Set the output message
        arcpy.AddMessage("Wind turbine shapefile created and added to the map successfully.")
