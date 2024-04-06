import arcpy
import os

def process_feature_service(output_folder: str, country_name: str = None) -> None:
    """
    Process the feature service by selecting features based on the specified country,
    convert them to point features, project to WGS 1984, and save the output as a shapefile.

    Parameters:
        output_folder (str): The folder where the output shapefile will be saved.
        country_name (str): The name of the country to select features for. If None, process all Baltic Sea countries.

    Returns:
        None
    """
    
    # Feature service URL
    feature_service_url = "https://services.arcgis.com/hRUr1F8lE8Jq2uJo/ArcGIS/rest/services/World_Port_Index/FeatureServer/0"

    # WGS 1984 WKID
    wgs84 = 4326  # WGS 1984

    # Create a feature layer from the feature service
    feature_layer = arcpy.management.MakeFeatureLayer(feature_service_url, "World_Port_Index").getOutput(0)

    # Define ISO codes for Baltic Sea countries in alphabetical order
    baltic_sea_countries = ["DE", "DK", "EE", "FI", "LV", "LT", "PL", "SE"]
    
    # If no country name is provided, process all Baltic Sea countries
    if not country_name:
        countries_to_process = baltic_sea_countries
    else:
        countries_to_process = [country_name]

    # Select features based on the country codes of all Baltic Sea countries
    query = "COUNTRY IN ('" + "','".join(countries_to_process) + "')"
    arcpy.management.SelectLayerByAttribute(feature_layer, "NEW_SELECTION", query)

    # Check if any features were selected
    result = arcpy.management.GetCount(feature_layer)
    count = int(result.getOutput(0))

    if count > 0:
        # Convert the feature layer to a point feature layer
        arcpy.management.FeatureToPoint(feature_layer, f"in_memory\\BalticSea__Points", "INSIDE")

        # Project the point feature layer to WGS 1984
        arcpy.management.Project(f"in_memory\\BalticSea_Points", f"in_memory\\BalticSea_Points_Projected", wgs84)
        
        # Create a new shapefile in the output folder
        output_shapefile = os.path.join(output_folder, "BalticSea_SelectedPorts.shp")

        # Check if the output shapefile already exists and delete it
        if arcpy.Exists(output_shapefile):
            arcpy.management.Delete(output_shapefile)        

        arcpy.management.CopyFeatures(f"in_memory\\BalticSea_Points_Projected", output_shapefile)

        # Use arcpy.mp to add the layer to the map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map_object = aprx.activeMap

        # Add the layer to the map
        map_object.addLayer(output_shapefile)

    else:
        arcpy.AddMessage(f"No features found for Baltic Sea countries")


if __name__ == "__main__":
    # Input parameters
    port_folder: str = arcpy.GetParameterAsText(0)  # User-specified output folder
    country_name: str = arcpy.GetParameterAsText(1)  # User input parameter for the country name

    # Call the main processing function
    process_feature_service(port_folder, country_name)
