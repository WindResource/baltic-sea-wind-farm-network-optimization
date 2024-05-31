import arcpy
import os

def generate_offshore_substation_areas(output_folder):
    """
    Creates a new EEZ shapefile for selected countries, erases the part of the polygon features that are west of the 9-degree longitude,
    erases the pairwise buffered areas of the selected countries and HELCOM Marine Protected Areas (MPA) from the EEZ shapefile,
    and adds the generated shapefile to the current ArcGIS map.

    Parameters:
    output_folder (str): The folder path where the new EEZ shapefile will be saved.
    """
    buffer_distance = 10 # km
    
    # Define ISO 2 char and ISO 3 char for Baltic Sea countries
    iso_eez_country_code = ['DNK', 'EST', 'FIN', 'DEU', 'LVA', 'LTU', 'POL', 'SWE']

    # URLs for feature layers
    countries_feature_layer_url = "https://services2.arcgis.com/VNo0ht0YPXJoI4oE/ArcGIS/rest/services/World_Countries_Specifically_Europe/FeatureServer/0"
    helcom_mpa_feature_layer_url = "https://maps.helcom.fi/arcgis/rest/services/MADS/Custom_webapps/MapServer/2"
    wkid = 4326  # WGS 1984

    # Get the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Find the EEZ layer in the current map
    eez_layer = None
    for layer in map.listLayers():
        if layer.name.startswith('eez_v12'):
            eez_layer = layer
            break
    if eez_layer is None:
        arcpy.AddError("No EEZ layer found. Ensure a layer starting with 'eez_v12' is loaded in the map.")
        return

    # Find the first WFA layer in the current map
    wfa_layer = None
    for layer in map.listLayers():
        if layer.name.startswith('WFA'):
            wfa_layer = layer
            break
    if wfa_layer is None:
        arcpy.AddError("No layer starting with 'WFA' found in the current map.")
        return

    # Create a feature layer from the WFA layer
    wfa_feature_layer = arcpy.management.MakeFeatureLayer(wfa_layer, "wfa_feature_layer").getOutput(0)
    
    # Select the countries for the specified ISO codes
    countries_layer = arcpy.management.MakeFeatureLayer(countries_feature_layer_url, "countries_layer").getOutput(0)
    arcpy.management.SelectLayerByAttribute(countries_layer, "NEW_SELECTION", f"ISO_CC IN {tuple(iso_eez_country_code)}")
    
    # Create a feature layer for HELCOM MPA
    helcom_mpa_layer = arcpy.management.MakeFeatureLayer(helcom_mpa_feature_layer_url, "helcom_mpa_layer").getOutput(0)
    
    # Select the EEZ features for the specified ISO codes
    arcpy.management.SelectLayerByAttribute(eez_layer, "NEW_SELECTION", f"ISO_TER1 IN {tuple(iso_eez_country_code)}")

    # Create a polygon representing the area west of 9 degrees longitude
    west_of_9_deg_polygon = arcpy.Polygon(arcpy.Array([arcpy.Point(-10, 90), arcpy.Point(-10, -90), arcpy.Point(9, -90), arcpy.Point(9, 90), arcpy.Point(-10, 90)]), arcpy.SpatialReference(wkid))

    # Save the west of 9 degrees polygon to a shapefile
    west_of_9_deg_layer_path = os.path.join(output_folder, "west_of_9_deg_layer.shp")
    arcpy.management.CopyFeatures(west_of_9_deg_polygon, west_of_9_deg_layer_path)
    
    # Erase the part of the EEZ layer that is west of 9 degrees longitude
    east_eez_layer_path = os.path.join(output_folder, "east_eez_layer.shp")
    arcpy.AddMessage("Erasing west of 9 degrees from EEZ...")
    arcpy.analysis.Erase(eez_layer, west_of_9_deg_layer_path, east_eez_layer_path)

    # Create a buffer around the selected countries
    buffer_layer_path = os.path.join(output_folder, "buffered_country.shp")
    arcpy.AddMessage("Buffering selected country...")
    arcpy.analysis.PairwiseBuffer(countries_layer, buffer_layer_path, f"{float(buffer_distance)} Kilometers")

    # Erase the buffered areas from the EEZ layer
    temp_erased_eez_path = os.path.join(output_folder, "temp_erased_eez.shp")
    arcpy.AddMessage("Erasing buffered country from EEZ...")
    arcpy.analysis.Erase(east_eez_layer_path, buffer_layer_path, temp_erased_eez_path)

    # Erase the HELCOM MPA areas from the EEZ layer
    final_erased_eez_path = os.path.join(output_folder, "final_erased_eez.shp")
    arcpy.AddMessage("Erasing HELCOM MPA from EEZ...")
    arcpy.analysis.Erase(temp_erased_eez_path, helcom_mpa_layer, final_erased_eez_path)

    # Erase the WFA areas from the EEZ layer
    final_erased_eez_with_wfa_path = os.path.join(output_folder, "final_erased_eez_with_wfa.shp")
    arcpy.AddMessage("Erasing WFA layer from EEZ...")
    arcpy.analysis.Erase(final_erased_eez_path, wfa_feature_layer, final_erased_eez_with_wfa_path)
    
    # Save the final output shapefile
    output_feature_class = os.path.join(output_folder, "EHA_BalticSea.shp")
    arcpy.AddMessage("Saving final output shapefile...")
    arcpy.management.CopyFeatures(final_erased_eez_with_wfa_path, output_feature_class)
    arcpy.AddMessage(f"Successfully processed and saved new EEZ shapefile for all selected Baltic Sea countries at {output_feature_class}.")

    # Add the generated shapefile to the current map
    map.addDataFromPath(output_feature_class)

if __name__ == "__main__":
    output_folder = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\offshore_substation_folder"
    generate_offshore_substation_areas(output_folder)
