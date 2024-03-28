import arcpy
import os

def generate_turbine_areas(output_folder: str, country: str, status: str) -> str:
    """
    Create a single shapefile for a selected status and country based on the input shapefile, utilizing in-memory workspaces.
    The created shapefile is added to the current map in ArcGIS Pro.

    Parameters:
    - output_folder (str): Path to the output folder where the shapefile will be saved.
    - country (str): The selected country.
    - status (str): The selected status to filter by.

    Returns:
    - str: Path to the created shapefile.
    """
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
        arcpy.AddError("No feature layer starting with windfarmspoly found in the current map.")
        return ""

    arcpy.AddMessage(f"Processing layer: {input_layer.name}")

    # Define the output spatial reference (WKID 32633 - WGS 1984 UTM Zone 33N)
    output_spatial_reference = arcpy.SpatialReference(32633)

    # Create a SQL expression to select features by country and status
    sql_expression = (f"{arcpy.AddFieldDelimiters(input_layer, 'Country')} = '{country}' AND " +
                        f"{arcpy.AddFieldDelimiters(input_layer, 'Status')} = '{status}'")

    # Select features that match the country and status
    arcpy.management.SelectLayerByAttribute(input_layer, "NEW_SELECTION", sql_expression)

    # Check if there are any selected features
    if int(arcpy.GetCount_management(input_layer)[0]) > 0:
        # Define the output shapefile path
        output_shapefile = os.path.join(output_folder, f"WFA_{country}_{status}.shp")

        # Project and export the selected features to a new shapefile
        arcpy.management.Project(input_layer, output_shapefile, output_spatial_reference)

        # Add the shapefile to the current map in ArcGIS Pro
        map.addDataFromPath(output_shapefile)

        # Return the path to the created shapefile
        return output_shapefile
    else:
        arcpy.AddWarning(f"No features found for country '{country}' with status '{status}'. No shapefile created.")
        return ""

# Example usage placeholders, to be replaced with actual parameters in a real script
if __name__ == "__main__":
    windfarm_folder = arcpy.GetParameterAsText(0)   # The path to the output folder
    country = arcpy.GetParameterAsText(1)         # The selected country
    status = arcpy.GetParameterAsText(2)          # The selected status
    
    # Call the function
    output_shapefile = generate_turbine_areas(windfarm_folder, country, status)
    
    if output_shapefile:
        arcpy.AddMessage(f"Shapefile created and saved to: {output_shapefile}")
        arcpy.AddMessage("Shapefile added to the current map.")
    else:
        arcpy.AddMessage("No shapefile was created.")
