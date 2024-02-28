import arcpy
import os
import math

def calculate_meters_to_decimal_degrees(latitude):
    """
    Calculate the meters to decimal degrees conversion factor for a given latitude.

    Parameters:
    - latitude (float): The latitude of the point in decimal degrees.

    Returns:
    - Tuple[float, float]: Conversion factors for latitude (y-direction) and longitude (x-direction).
    """
    # Calculate the conversion factor based on the latitude
    meters_per_degree_y = 111132.92 - 559.82 * math.cos(2 * math.radians(latitude)) + 1.175 * math.cos(4 * math.radians(latitude)) - 0.0023 * math.cos(6 * math.radians(latitude))

    # For longitude (x-direction), we assume a constant conversion factor
    # This assumes the shapefile covers a relatively small area, so the variation in longitude is negligible
    meters_per_degree_x = 111320.0

    return meters_per_degree_y, meters_per_degree_x

def create_wind_turbine_shapefile(input_folder: str, turbine_spacing: float, output_folder: str, map_frame_name: str) -> None:
    """
    Create a shapefile feature class containing wind turbine points with WGS 1984 coordinate system
    and add it to the project map.

    Parameters:
    - input_folder (str): The folder containing the input shapefiles representing the wind farm areas.
    - turbine_spacing (float): The desired spacing between wind turbines in meters.
    - output_folder (str): The name of the output shapefile feature class to store wind turbine locations.
    - map_frame_name (str): The name of the map frame in ArcGIS Pro where the wind turbines will be visualized.

    Returns:
    - None
    """

    # Check if input folder exists
    if not os.path.exists(input_folder):
        arcpy.AddError(f"Input folder '{input_folder}' does not exist.")
        return

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
                shape, centroid = row[0], row[1]

        # Calculate meters to decimal degrees conversion factors for latitude (y) and longitude (x)
        meters_per_degree_y, meters_per_degree_x = calculate_meters_to_decimal_degrees(centroid[1])

        # Convert turbine_spacing from meters to decimal degrees
        spacing_decimal_degrees_y = turbine_spacing / meters_per_degree_y
        spacing_decimal_degrees_x = turbine_spacing / meters_per_degree_x

        # Create a bounding box that encompasses the entire polygon
        bounding_box = shape.extent

        # Create a new point feature class for wind turbine locations
        output_feature_class_name = f"WindTurbines_{os.path.splitext(input_shapefile)[0]}.shp"
        output_feature_class = os.path.join(output_folder, output_feature_class_name)

        # Set spatial reference for WGS 1984
        spatial_reference = arcpy.SpatialReference(4326)  # 4326 is the WKID for WGS 1984

        # Create the point feature class with the specified spatial reference
        arcpy.management.CreateFeatureclass(output_folder, output_feature_class_name, "POINT", spatial_reference=spatial_reference)

        # Add fields to store turbine information
        arcpy.management.AddFields(output_feature_class, [
            ["TurbineID", "TEXT", "Turbine ID"],
            ["Capacity", "DOUBLE", "Capacity"],
            ["XCoord", "DOUBLE", "Longitude"],
            ["YCoord", "DOUBLE", "Latitude"]
        ])

        # Calculate the number of turbines outside the inner loop
        num_turbines_x = int(bounding_box.width / spacing_decimal_degrees_x)
        num_turbines_y = int(bounding_box.height / spacing_decimal_degrees_y)

        # Print bounding box dimensions and calculated number of turbines
        print(f"Bounding Box Dimensions: Width = {bounding_box.width}, Height = {bounding_box.height}")
        print(f"Calculated Number of Turbines: X = {num_turbines_x}, Y = {num_turbines_y}")

        # Generate a grid of points within the bounding box of the polygon
        with arcpy.da.InsertCursor(output_feature_class, ["SHAPE@", "TurbineID", "Capacity", "XCoord", "YCoord"]) as cursor:
            for i in range(num_turbines_x):
                for j in range(num_turbines_y):
                    x_coord = bounding_box.XMin + i * spacing_decimal_degrees_x
                    y_coord = bounding_box.YMin + j * spacing_decimal_degrees_y

                    # Check if the point is within the polygon
                    if shape.contains(arcpy.Point(x_coord, y_coord)):
                        # Print turbine coordinates
                        print(f"Turbine Coordinates: Longitude = {x_coord}, Latitude = {y_coord}")

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

    arcpy.AddMessage("Wind turbine shapefiles created and added to the map successfully.")


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
        # Create wind turbine shapefiles and add wind turbine points to the map
        create_wind_turbine_shapefile(input_folder, turbine_spacing, output_folder, map_frame_name)

        # Set the output message
        arcpy.AddMessage("Wind turbine shapefiles created and added to the map successfully.")
