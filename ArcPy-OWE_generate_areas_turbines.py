import arcpy
import os

def generate_turbine_areas(output_folder: str, countries_input: str = None, status: str = "Planned") -> str:
    """
    Create a single shapefile for selected countries and status based on the input shapefile, utilizing in-memory workspaces.
    The created shapefile is added to the current map in ArcGIS Pro.

    Parameters:
    - output_folder (str): Path to the output folder where the shapefile will be saved.
    - countries_input (str): Semicolon-separated string of selected countries. If None or empty, all 8 Baltic Sea countries will be selected.
    - status (str): The selected status to filter by. Default is 'Planned'.

    Returns:
    - str: Path to the created shapefile.
    """
    # Default to all Baltic Sea countries if countries_input is None or empty
    if not countries_input:
        countries = ['Denmark', 'Estonia', 'Finland', 'Germany', 'Latvia', 'Lithuania', 'Poland', 'Sweden']
    else:
        countries = countries_input.split(';')

    wkid = 4326  # WGS 1984

    # Get the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Get the first feature layer in the map that starts with 'windfarmspoly'
    wf_layer = None
    for layer in map.listLayers():
        if layer.isFeatureLayer:
            if layer.name.startswith('windfarmspoly'):
                wf_layer = layer
                break

    if wf_layer is None:
        arcpy.AddError("No layer starting with 'windfarmspoly' found in the current map.")
        return

    arcpy.AddMessage(f"Processing layer: {wf_layer.name}")

    # Processing for EEZ
    arcpy.management.SelectLayerByAttribute(wf_layer, "NEW_SELECTION", f"country IN {tuple(countries)} AND status = '{status}'")
    arcpy.management.CopyFeatures(wf_layer, "in_memory\\selected_wf_layer")

    # Iterate through features and select those that meet the longitude condition
    with arcpy.da.UpdateCursor("in_memory\\selected_wf_layer", ['SHAPE@X']) as cursor:
        for row in cursor:
            if row[0] < 9:  # Check if longitude is greater than 9
                cursor.deleteRow()

    # Define the output shapefile path
    output_shapefile = os.path.join(output_folder, f"WFA_BalticSea_{status}.shp")

    # Copy the selected features to a new shapefile
    arcpy.management.CopyFeatures("in_memory\\selected_wf_layer", output_shapefile)

    # Add the shapefile to the current map in ArcGIS Pro
    map.addDataFromPath(output_shapefile)

    # Return the path to the created shapefile
    return output_shapefile

if __name__ == "__main__":
    windfarm_folder = arcpy.GetParameterAsText(0)   # The path to the output folder
    countries = arcpy.GetParameterAsText(1)  # The selected countries (as a semicolon-separated string)

    # Call the function with default status as 'Planned'
    output_shapefile = generate_turbine_areas(windfarm_folder, countries)

    if output_shapefile:
        arcpy.AddMessage(f"Shapefile created and saved to: {output_shapefile}")
        arcpy.AddMessage("Shapefile added to the current map.")
    else:
        arcpy.AddMessage("No shapefile was created.")
