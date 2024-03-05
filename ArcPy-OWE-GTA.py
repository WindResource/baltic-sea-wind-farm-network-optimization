import arcpy
import os

def clear_shapefile(file_path):
    """
    Attempt to remove a shapefile from the currently active map frame and then unlock and delete
    the shapefile and its associated lock file.

    Parameters:
    - file_path (str): The path to the shapefile.

    Returns:
    - None
    """
    try:
        # Get a reference to the currently active map frame
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map_obj = aprx.activeMap

        if not map_obj:
            arcpy.AddError("No map frame is currently active.")
            return

        # Clear the shapefile from the map
        for layer in map_obj.listLayers():
            if layer.isFeatureLayer and layer.dataSource == file_path:
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
    # Define the output spatial reference (WKID 32633 - WGS 1984 UTM Zone 33N)
    output_spatial_reference = arcpy.SpatialReference(32633)

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

    # Get the ArcGIS Pro project
    aprx = arcpy.mp.ArcGISProject("CURRENT")

    # Get the currently active map frame
    map_obj = aprx.activeMap

    if not map_obj:
        arcpy.AddError("No map frame is currently active.")
        return created_shapefiles

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

                # Create a feature layer with the specified SQL expression
                feature_layer = arcpy.management.MakeFeatureLayer(input_shapefile, "temp_layer", where_clause=fid_sql_expression)

                # Project the feature layer to the desired spatial reference and create the new shapefile
                output_shapefile = os.path.join(output_folder, f"WFA_{country}_{status}_FID{feature_fid}.shp")
                arcpy.management.Project(feature_layer, output_shapefile, output_spatial_reference)

                created_shapefiles.append(output_shapefile)

                # Add the shapefile to the map
                map_obj.addDataFromPath(output_shapefile)

    # Refresh the map to apply changes
    aprx.save()

    return created_shapefiles

if __name__ == "__main__":
    # Get the input shapefile, output folder, country, status parameters from the user input
    input_shapefile: str = arcpy.GetParameterAsText(0)
    output_folder: str = arcpy.GetParameterAsText(1)
    selected_country: str = arcpy.GetParameterAsText(2)
    selected_approved: bool = arcpy.GetParameter(3)
    selected_construction: bool = arcpy.GetParameter(4)
    selected_planned: bool = arcpy.GetParameter(5)
    selected_production: bool = arcpy.GetParameter(6)

    # Validate input parameters
    if not arcpy.Exists(input_shapefile):
        arcpy.AddError("Input shapefile does not exist.")
    elif not os.path.isdir(output_folder):
        arcpy.AddError("Output folder is not valid.")
    else:
        # Clear existing shapefiles from the map and delete them
        for existing_shapefile_path in arcpy.ListFeatureClasses("*", "", output_folder):
            clear_shapefile(existing_shapefile_path)

        # Execute the main function to create shapefiles
        created_shapefiles: list = create_shapefiles(
            input_shapefile, output_folder, selected_country,
            selected_approved, selected_construction, selected_planned, selected_production
        )

        # Set the output message
        arcpy.AddMessage("Shapefiles created and added to the map successfully.")
