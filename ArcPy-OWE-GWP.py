import arcpy
import os

def create_wind_turbine_matrices(input_folder: str, turbine_spacing: float, output_folder: str, map_frame_name: str) -> None:
    """
    Create a point feature class representing wind turbine locations within specified polygons.

    Parameters:
    - input_folder (str): The folder containing the input shapefiles representing the wind farm areas.
    - turbine_spacing (float): The desired spacing between wind turbines in the same units as the input shapefiles.
    - output_folder (str): The name of the output point feature class to store wind turbine locations.
    - map_frame_name (str): The name of the map frame in ArcGIS Pro where the wind turbines will be visualized.

    Returns:
    - None
    """

    # Check if input folder exists, if not, create it
    if not os.path.exists(input_folder):
        os.makedirs(input_folder)
        arcpy.AddMessage(f"Input folder '{input_folder}' created.")

    # Set workspace to the input folder
    arcpy.env.workspace = input_folder

    # Get turbine_spacing from user input
    turbine_spacing = float(arcpy.GetParameterAsText(3))  # Assuming it is the 4th parameter

    # Get a list of all shapefiles in the input folder
    shapefiles = arcpy.ListFeatureClasses()

    if not shapefiles:
        arcpy.AddError("No shapefiles found in the input folder.")
        return

    # Iterate over all shapefiles in the input folder
    for input_shapefile in shapefiles:
        arcpy.AddMessage(f"Processing shapefile: {input_shapefile}")

        # Create a point feature class for each shapefile
        spatial_reference = arcpy.Describe(input_shapefile).spatialReference
        arcpy.AddMessage(f"Spatial Reference: {spatial_reference.name if spatial_reference else 'None'}")

        output_feature_class_name = f"{os.path.splitext(os.path.basename(input_shapefile))[0]}_WindTurbines"
        output_feature_class = os.path.join(output_folder, output_feature_class_name)

        arcpy.AddMessage(f"Output Feature Class Name: {output_feature_class_name}")
        arcpy.AddMessage(f"Output Feature Class: {output_feature_class}")

        # Use search cursor to get the boundary of the input polygon
        with arcpy.da.SearchCursor(input_shapefile, ["SHAPE@", "SHAPE@XY"]) as cursor:
            for row in cursor:
                boundary = row[0].boundary()
                centroid_x, centroid_y = row[1]

        # Generate a grid of points within the polygon
        with arcpy.da.InsertCursor(output_feature_class, ["SHAPE@", "TurbineID", "Capacity"]) as cursor:
            for part in boundary:
                for i in range(int(part.count / 2)):
                    # Calculate the number of turbines in each direction based on the input shapefile's extent
                    num_turbines_x = int(part.length / turbine_spacing)
                    num_turbines_y = int(part.length / turbine_spacing)

                    for i in range(num_turbines_x):
                        for j in range(num_turbines_y):
                            distance_along_line = i * turbine_spacing
                            point = part.positionAlongLine(distance_along_line).firstPoint

                            turbine_id = f"Turbine_{i}_{j}"
                            capacity = 0.0  # You can set the capacity based on your requirements
                            cursor.insertRow((
                                arcpy.Point(point.X, point.Y),
                                turbine_id,
                                capacity
                            ))

        arcpy.AddMessage(f"Shapefile '{input_shapefile}' successfully imported.")

        # Add the point feature class to the specified map frame
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map_obj = aprx.listMaps(map_frame_name)[0]
        map_obj.addDataFromPath(output_feature_class)

        # Update the input shapefile's attribute table with wind turbine information
        fields = ["TurbineID", "Capacity", "SHAPE@"]
        with arcpy.da.UpdateCursor(input_shapefile, fields) as update_cursor:
            for row in update_cursor:
                turbine_id = row[0]
                capacity = row[1]
                turbine_point = row[2].centroid if row[2] else None  # Use centroid if available

                if turbine_point:
                    # Add turbine information to the input shapefile's attribute table
                    update_cursor.updateRow((turbine_id, capacity, turbine_point))

if __name__ == "__main__":
    # Get the input folder, output folder, map frame name, and turbine spacing from the user input
    input_folder: str = arcpy.GetParameterAsText(0)
    output_folder: str = arcpy.GetParameterAsText(1)
    map_frame_name: str = arcpy.GetParameterAsText(2)
    turbine_spacing: float = float(arcpy.GetParameterAsText(3))

    # Validate input parameters
    if not os.path.isdir(output_folder):
        arcpy.AddError("Output folder is not valid.")
    else:
        # Create wind turbine matrices and add them to the map for all shapefiles in the input folder
        create_wind_turbine_matrices(input_folder, turbine_spacing=turbine_spacing, output_folder=output_folder, map_frame_name=map_frame_name)

        # Set the output message
        arcpy.AddMessage("Shapefiles and wind turbine matrices created and added to the map successfully.")
