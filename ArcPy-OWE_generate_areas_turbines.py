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

    # Get the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Get the first feature layer in the map that starts with 'windfarmspoly'
    input_layer = None
    for layer in map.listLayers():
        if layer.isFeatureLayer:
            if layer.name.startswith('windfarmspoly'):
                input_layer = layer
                break

    if input_layer is None:
        arcpy.AddError("No layer starting with 'windfarmspoly' found in the current map.")
        return
    
    # Deselect all currently selected features
    arcpy.SelectLayerByAttribute_management(input_layer, "CLEAR_SELECTION")
    
    arcpy.AddMessage(f"Processing layer: {input_layer.name}")

    # Get the path of the feature class
    feature_class_path = input_layer.dataSource

    # Define the output spatial reference (WKID 32633 - WGS 1984 UTM Zone 33N)
    output_spatial_reference = arcpy.SpatialReference(32633)

    # Create a list to hold selected features
    selected_features = []

    # Iterate through features and select those that match the selected countries and status
    with arcpy.da.SearchCursor(feature_class_path, ['SHAPE@', 'country', 'status']) as cursor:
        for row in cursor:
            if row[1] in countries and row[2] == status:
                selected_features.append(row[0])
    
    # Check if there are any selected features
    if selected_features:
        # Create a temporary feature class to hold the selected features
        temp_feature_class = os.path.join(arcpy.env.scratchGDB, "temp_selected_features")
        arcpy.CopyFeatures_management(selected_features, temp_feature_class)
        
        # Define the output shapefile path
        output_shapefile = os.path.join(output_folder, f"WFA_BalticSea_{status}.shp")

        # Project and export the selected features to a new shapefile
        arcpy.management.Project(temp_feature_class, output_shapefile, output_spatial_reference)

        # Add the shapefile to the current map in ArcGIS Pro
        map.addDataFromPath(output_shapefile)

        # Return the path to the created shapefile
        return output_shapefile
    else:
        arcpy.AddWarning(f"No features found for selected countries '{countries_input}' with status '{status}'. No shapefile created.")
        return ""

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
