import arcpy

def generate_offshore_substation_areas(iso_country_code, iso_eez_country_code, output_folder, buffer_distance=15):
    """
    Creates a new EEZ shapefile for selected countries, erases the pairwise buffered areas of the selected countries and 
    HELCOM Marine Protected Areas (MPA) from the EEZ shapefile, and adds the generated shapefile to the current ArcGIS map.

    Parameters:
    iso_country_code (list): The list of ISO country codes for which to generate the offshore substation areas.
    iso_eez_country_code (list): The list of ISO country codes representing EEZs.
    output_folder (str): The folder path where the new EEZ shapefile will be saved.
    buffer_distance (float): The buffer distance in kilometers.
    """
    # Define ISO 2 char and ISO 3 char for Baltic Sea countries
    baltic_sea_iso_2 = ['DK', 'EE', 'FI', 'DE', 'LV', 'LT', 'PL', 'SE']
    baltic_sea_iso_3 = ['DNK', 'EST', 'FIN', 'DEU', 'LVA', 'LTU', 'POL', 'SWE']

    # URLs for feature layers
    countries_feature_layer_url = "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/World_Countries_(Generalized)/FeatureServer/0"
    helcom_mpa_feature_layer_url = "https://maps.helcom.fi/arcgis/rest/services/MADS/Biodiversity/MapServer/54"
    wkid = 4326  # WGS 1984

    # Check if ISO country codes are not provided by the user
    if not iso_country_code:
        iso_country_code = baltic_sea_iso_2
    if not iso_eez_country_code:
        iso_eez_country_code = baltic_sea_iso_3

    # Ensure iso_country_code and iso_eez_country_code are lists
    if isinstance(iso_country_code, str):
        iso_country_code = [iso_country_code]
    if isinstance(iso_eez_country_code, str):
        iso_eez_country_code = [iso_eez_country_code]

    # Ensure the EEZ layer is available in the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap
    eez_layer = None
    for layer in map.listLayers():
        if layer.name.startswith('eez_v12'):
            eez_layer = layer
            break
    if eez_layer is None:
        arcpy.AddError("No EEZ layer found. Ensure a layer starting with 'eez_v12' is loaded in the map.")
        return

    # Processing for country selection and buffering
    countries_layer = arcpy.management.MakeFeatureLayer(countries_feature_layer_url, "countries_layer").getOutput(0)
    arcpy.management.SelectLayerByAttribute(countries_layer, "NEW_SELECTION", f"ISO IN {tuple(iso_country_code)}")
    arcpy.management.CopyFeatures(countries_layer, "in_memory\\selected_country")
    arcpy.management.Project("in_memory\\selected_country", "in_memory\\selected_country_projected", wkid)
    
    # Processing for HELCOM MPA
    helcom_mpa_layer = arcpy.management.MakeFeatureLayer(helcom_mpa_feature_layer_url, "helcom_mpa_layer").getOutput(0)
    arcpy.management.CopyFeatures(helcom_mpa_layer, "in_memory\\helcom_mpa")
    arcpy.management.Project("in_memory\\helcom_mpa", "in_memory\\helcom_mpa_projected", wkid)
    
    # Processing for country selection and buffering
    arcpy.management.SelectLayerByAttribute(eez_layer, "NEW_SELECTION", f"ISO_TER1 IN {tuple(iso_eez_country_code)}")
    arcpy.management.CopyFeatures(eez_layer, "in_memory\\selected_eez_layer")
    arcpy.management.Project("in_memory\\selected_eez_layer", "in_memory\\selected_eez_layer_projected", wkid)
    
    # Create buffer for the selected country
    buffer_layer = "in_memory\\buffered_country"
    arcpy.analysis.Buffer("in_memory\\selected_country_projected", buffer_layer, f"{buffer_distance} Kilometers", "FULL", "ROUND", "NONE", None, "GEODESIC")

    # Pairwise erase for the buffered country from EEZ
    temp_erased_eez = "in_memory\\temp_erased_eez"
    arcpy.analysis.PairwiseErase("in_memory\\selected_eez_layer_projected", buffer_layer, temp_erased_eez)

    # Pairwise erase for HELCOM MPA from previously erased EEZ
    final_erased_eez = "in_memory\\final_erased_eez"
    arcpy.analysis.PairwiseErase(temp_erased_eez, "in_memory\\helcom_mpa_projected", final_erased_eez)

    # Save the output to a new shapefile
    output_feature_class = f"{output_folder}\\OSSA_All_Baltic_Countries.shp"
    arcpy.management.CopyFeatures(final_erased_eez, output_feature_class)

    arcpy.AddMessage(f"Successfully processed and saved new EEZ shapefile for all selected Baltic Sea countries at {output_feature_class}.")

    # Add the generated shapefile to the current map
    map.addDataFromPath(output_feature_class)


if __name__ == "__main__":
    iso_country_code = arcpy.GetParameterAsText(0)  # ISO 2 char
    iso_eez_country_code = arcpy.GetParameterAsText(1)  # ISO 3 char
    output_folder = arcpy.GetParameterAsText(2)
    buffer_distance = float(arcpy.GetParameterAsText(3))  # Ensure this is a float
    
    generate_offshore_substation_areas(iso_country_code, iso_eez_country_code, output_folder, buffer_distance)
