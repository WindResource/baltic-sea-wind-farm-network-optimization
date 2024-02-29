import arcpy
import os

def create_wind_turbine_shapefile(input_folder: str, turbine_spacing: float, output_folder: str, map_frame_name: str) -> None:
    """
    Create a shapefile feature class containing wind turbine points with a UTM projection
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

    # Set the spatial reference to UTM Zone 33N
    utm_wkid = 32633

    # Set the spatial reference to UTM Zone 33N
    utm_spatial_ref = arcpy.SpatialReference(utm_wkid)

    # Iterate over all shapefiles in the input folder
    for input_shapefile in shapefiles:
        arcpy.AddMessage(f"Processing shapefile: {input_shapefile}")

        # Use search cursor to get the extent of the input polygon
        with arcpy.da.SearchCursor(input_shapefile, ["SHAPE@", "SHAPE@XY"]) as cursor:
            for row in cursor:
                shape, centroid = row[0], row[1]

        # Create a bounding box that encompasses the entire polygon
        bounding_box = shape.extent

        # Create the point feature class with the specified spatial reference in UTM
        output_feature_class = arcpy.management.CreateFeatureclass(
            out_path=output_folder,
            out_name=f"WindTurbines_{os.path.splitext(input_shapefile)[0]}.shp",
            geometry_type="POINT",
            spatial_reference=utm_spatial_ref
        )

        # Add fields to store turbine information
        arcpy.management.AddFields(output_feature_class, [
            ["TurbineID", "TEXT", "Turbine ID"],
            ["Capacity", "DOUBLE", "Capacity"],
            ["XCoord", "DOUBLE", "Longitude"],
            ["YCoord", "DOUBLE", "Latitude"]
        ])

        # Generate a grid of points within the bounding box of the polygon
        with arcpy.da.InsertCursor(output_feature_class, ["SHAPE@", "TurbineID", "Capacity", "XCoord", "YCoord"]) as cursor:
            # Start from the minimum coordinates of the bounding box
            x_coord = bounding_box.XMin
            y_coord = bounding_box.YMin
            turbine_count = 0

            while y_coord < bounding_box.YMax:
                while x_coord < bounding_box.XMax:
                    # Check if the point is within the polygon
                    if shape.contains(arcpy.Point(x_coord, y_coord)):
                        turbine_id = f"Turbine_{turbine_count}"
                        capacity = 0.0  # You can set the capacity based on your requirements

                        cursor.insertRow((
                            arcpy.Point(x_coord, y_coord),
                            turbine_id,
                            capacity,
                            x_coord,
                            y_coord
                        ))

                        turbine_count += 1

                    x_coord += turbine_spacing

                x_coord = bounding_box.XMin
                y_coord += turbine_spacing

        arcpy.AddMessage(f"{turbine_count} turbines created for shapefile '{input_shapefile}'.")

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
