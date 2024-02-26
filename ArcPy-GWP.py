import arcpy
import os

def create_shapefiles(input_shapefile: str, output_folder: str, country: str, approved: bool, construction: bool, planned: bool, production: bool) -> list:
    """
    Create shapefiles for each selected status and country based on the input shapefile.

    Parameters:
    - input_shapefile (str): Path to the input shapefile.
    - output_folder (str): Path to the output folder where the shapefiles will be saved.
    - country (str): The selected country.
    - approved (bool): True if the Approved status is selected, False otherwise.
    - construction (bool): True if the Construction status is selected, False otherwise.
    - planned (bool): True if the Planned status is selected, False otherwise.
    - production (bool): True if the Production status is selected, False otherwise.

    Returns:
    - list: List of paths to the created shapefiles.
    """
    # Create a list of selected statuses
    selected_statuses = []
    if approved:
        selected_statuses.append("Approved")
    if construction:
        selected_statuses.append("Construction")
    if planned:
        selected_statuses.append("Planned")
    if production:
        selected_statuses.append("Production")

    # Initialize a list to store paths of created shapefiles
    created_shapefiles = []

    # Iterate through selected statuses and create shapefile for each
    for status in selected_statuses:
        # Create a SQL expression to select features for the specified combination
        sql_expression = (
            arcpy.AddFieldDelimiters(input_shapefile, "Country") + " = '{}' AND " +
            arcpy.AddFieldDelimiters(input_shapefile, "Status") + " = '{}'").format(country, status)

        # Create a search cursor to get unique FID values
        with arcpy.da.SearchCursor(input_shapefile, "FID", where_clause=sql_expression) as cursor:
            for row in cursor:
                # Get the FID value
                feature_fid = row[0]

                # Create a new SQL expression for the specific FID
                fid_sql_expression = "{} = {}".format(arcpy.AddFieldDelimiters(input_shapefile, "FID"), feature_fid)

                # Create the new shapefile for the specified combination and FID
                output_shapefile = os.path.join(output_folder, f"OWF_{country}_{status}_FID_{feature_fid}.shp")
                arcpy.Select_analysis(input_shapefile, output_shapefile, fid_sql_expression)

                created_shapefiles.append(output_shapefile)

    return created_shapefiles

def add_all_shapefiles_to_map(shapefile_paths: list, map_frame_name: str) -> None:
    """
    Add all shapefiles from the specified list to the map.

    Parameters:
    - shapefile_paths (list): List of paths to shapefiles.
    - map_frame_name (str): Name of the map frame to which shapefiles will be added.
    """
    aprx = arcpy.mp.ArcGISProject("CURRENT")

    # Check if the map with the specified name exists
    map_list = aprx.listMaps(map_frame_name)

    if not map_list:
        arcpy.AddError(f"Map '{map_frame_name}' not found in the project.")
        return

    map_object = map_list[0]

    # Define unique colors for each status
    status_colors = {
        "Approved": (0, 255, 0),
        "Construction": (255, 0, 0),
        "Planned": (0, 0, 255),
        "Production": (255, 255, 0),
    }

    # Iterate through the shapefiles and add each to the map
    for shapefile_path in shapefile_paths:
        # Extract the status from the shapefile path
        status = os.path.basename(shapefile_path).split("_")[2]

        if status in status_colors:
            # Add the shapefile to the map
            layer = map_object.addDataFromPath(shapefile_path)
            # Set the color for the status
            layer.color = status_colors[status]
        else:
            arcpy.AddWarning(f"Status '{status}' is not recognized.")
            
            # Refresh the map to apply changes
            aprx.save()

if __name__ == "__main__":
    # Get the input shapefile, output folder, country, status parameters, and map frame name from the user input
    input_shapefile: str = arcpy.GetParameterAsText(0)
    output_folder: str = arcpy.GetParameterAsText(1)
    selected_country: str = arcpy.GetParameterAsText(2)
    selected_approved: bool = arcpy.GetParameter(3)
    selected_construction: bool = arcpy.GetParameter(4)
    selected_planned: bool = arcpy.GetParameter(5)
    selected_production: bool = arcpy.GetParameter(6)
    map_frame_name: str = arcpy.GetParameterAsText(7)

    # Validate input parameters
    if not arcpy.Exists(input_shapefile):
        arcpy.AddError("Input shapefile does not exist.")
    elif not os.path.isdir(output_folder):
        arcpy.AddError("Output folder is not valid.")
    else:
        # Execute the main function to create shapefiles
        created_shapefiles: list = create_shapefiles(
            input_shapefile, output_folder, selected_country,
            selected_approved, selected_construction, selected_planned, selected_production
        )

        # Add all shapefiles to the map
        add_all_shapefiles_to_map(created_shapefiles, map_frame_name)

        # Set the output message
        arcpy.AddMessage("Shapefiles created and added to the map successfully.")
