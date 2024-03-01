import arcpy
import os

def clear_shapefile(file_path, map_frame_name):
    """
    Attempt to remove a shapefile from the specified map frame and then unlock and delete
    the shapefile and its associated lock file.

    Parameters:
    - file_path (str): The path to the shapefile.
    - map_frame_name (str): The name of the map frame in ArcGIS Pro where the shapefile should be removed.

    Returns:
    - None
    """
    try:
        # Get a reference to the map object based on the map frame name
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map_obj = None
        for map_frame in aprx.listMaps():
            if map_frame.name == map_frame_name:
                map_obj = map_frame
                break

        if not map_obj:
            arcpy.AddError(f"Map frame '{map_frame_name}' not found.")
            return

        # Clear the shapefile from the map
        for layer in map_obj.listLayers():
            if layer.isFeatureLayer and layer.name == os.path.splitext(os.path.basename(file_path))[0]:
                map_obj.removeLayer(layer)

        # Attempt to unlock and delete the shapefile
        if arcpy.Exists(file_path):
            arcpy.Delete_management(file_path)
        else:
            arcpy.AddMessage(f"The shapefile {file_path} does not exist.")

        # Attempt to unlock and delete the lock file
        lock_file_path = file_path + ".lock"
        if arcpy.Exists(lock_file_path):
            arcpy.Delete_management(lock_file_path)
        else:
            arcpy.AddMessage(f"The lock file {lock_file_path} does not exist.")

    except arcpy.ExecuteError as e:
        arcpy.AddMessage(f"Failed to clear {file_path}: {e}")
    except Exception as e:
        arcpy.AddMessage(f"An unexpected error occurred: {e}")

def create_wind_turbine_shapefile(input_folder: str, turbine_spacing: float, output_folder: str, map_frame_name: str, utm_zone: int, turbine_capacity: float, turbine_diameter: float) -> None:
    """
    Create a shapefile feature class containing wind turbine points with a UTM projection
    and add it to the project map.

    Parameters:
    - input_folder (str): The folder containing the input shapefiles representing the wind farm areas.
    - turbine_spacing (float): The desired spacing between wind turbines in terms of turbine diameters.
    - output_folder (str): The name of the output shapefile feature class to store wind turbine locations.
    - map_frame_name (str): The name of the map frame in ArcGIS Pro where the wind turbines will be visualized.
    - utm_zone (int): The UTM zone for the projection.
    - turbine_capacity (float): The capacity of each wind turbine in MW.
    - turbine_diameter (float): The diameter of each wind turbine.

    Returns:
    - None
    """

    try:
        # Validate input folder
        if not os.path.exists(input_folder):
            arcpy.AddError(f"Input folder '{input_folder}' does not exist.")
            return

        # Set workspace to the input folder
        arcpy.env.workspace = input_folder

        # Get a reference to the map object based on the map frame name
        map_obj = next((map_frame for map_frame in arcpy.mp.ArcGISProject("CURRENT").listMaps() if map_frame.name == map_frame_name), None)

        if not map_obj:
            arcpy.AddError(f"Map frame '{map_frame_name}' not found.")
            return

        # Set the spatial reference to the specified UTM Zone
        utm_wkid = 32600 + utm_zone  # UTM Zone 33N is WKID 32633
        utm_spatial_ref = arcpy.SpatialReference(utm_wkid)

        for input_shapefile in arcpy.ListFeatureClasses():
            arcpy.AddMessage(f"Processing shapefile: {input_shapefile}")

            # Get extent and centroid
            shape, centroid = arcpy.da.SearchCursor(input_shapefile, ["SHAPE@", "SHAPE@XY"]).next()

            # Create bounding box
            bounding_box = shape.extent

            # Create point feature class with spatial reference
            output_feature_class = arcpy.management.CreateFeatureclass(
                output_folder,
                f"WTC_{os.path.splitext(input_shapefile)[0]}.shp",
                "POINT",
                spatial_reference=utm_spatial_ref
            )

            # Add fields in the desired order
            arcpy.management.AddFields(output_feature_class, [
                ["TurbineID", "TEXT", "Turbine ID"],
                ["XCoord", "DOUBLE", "Longitude"],
                ["YCoord", "DOUBLE", "Latitude"],
                ["Capacity", "DOUBLE", "Capacity"],
                ["Diameter", "DOUBLE", "Diameter"]
            ])

            # Calculate the spacing in meters based on the turbine diameter
            spacing = turbine_spacing * turbine_diameter

            # Generate grid of points
            with arcpy.da.InsertCursor(output_feature_class, ["SHAPE@", "TurbineID", "XCoord", "YCoord", "Capacity", "Diameter"]) as cursor:
                x, y = bounding_box.XMin, bounding_box.YMin
                turbine_count = 0
                total_capacity = 0

                while y < bounding_box.YMax:
                    while x < bounding_box.XMax:
                        if shape.contains(arcpy.Point(x, y)):
                            turbine_id, capacity, diameter = f"Turbine_{turbine_count}", turbine_capacity, turbine_diameter
                            cursor.insertRow((arcpy.Point(x, y), turbine_id, x, y, capacity, diameter))
                            turbine_count += 1
                            total_capacity += turbine_capacity

                        x += spacing

                    x, y = bounding_box.XMin, y + spacing

            # Delete the 'Id' column from the attribute table
            arcpy.management.DeleteField(output_feature_class, "Id")

            arcpy.AddMessage(f"'{input_shapefile}': Number of turbines {turbine_count}, Total capacity {total_capacity} MW.")
            map_obj.addDataFromPath(output_feature_class)

        arcpy.AddMessage("Wind turbine shapefiles created and added to the map successfully.")

    except arcpy.ExecuteError as e:
        arcpy.AddMessage(f"Failed to create wind turbine shapefiles: {e}")
    except Exception as e:
        arcpy.AddMessage(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Get the input folder, output folder, map frame name, turbine spacing in diameters, UTM zone, turbine capacity, and turbine diameter from the user input
    input_folder: str = arcpy.GetParameterAsText(0)
    output_folder: str = arcpy.GetParameterAsText(1)
    map_frame_name: str = arcpy.GetParameterAsText(2)
    utm_zone: int = int(arcpy.GetParameterAsText(3))
    turbine_capacity: float = float(arcpy.GetParameterAsText(4))
    turbine_diameter: float = float(arcpy.GetParameterAsText(5))
    turbine_spacing: float = float(arcpy.GetParameterAsText(6))

    # Validate input parameters
    if not os.path.isdir(output_folder):
        arcpy.AddError("Output folder is not valid.")
    else:
        # Clear existing shapefiles from the map and delete them
        for existing_shapefile_path in arcpy.ListFeatureClasses("*", "", output_folder):
            clear_shapefile(existing_shapefile_path, map_frame_name)
        
        # Create wind turbine shapefiles and add wind turbine points to the map
        create_wind_turbine_shapefile(input_folder, turbine_spacing, output_folder, map_frame_name, utm_zone, turbine_capacity, turbine_diameter)

        # Set the output message
        arcpy.AddMessage("Wind turbine shapefiles created and added to the map successfully.")