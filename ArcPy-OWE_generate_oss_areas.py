import arcpy

def generate_offshore_substation_areas(iso_country_code, output_folder, buffer_distance):
    """
    Creates a new EEZ shapefile for a specified country, erases the pairwise buffered areas of the specified country and 
    HELCOM Marine Protected Areas (MPA) from the EEZ shapefile, and adds the generated shapefile to the current ArcGIS map.

    Parameters:
    iso_country_code (str): The ISO country code for which to generate the offshore substation areas.
    output_folder (str): The folder path where the new EEZ shapefile will be saved.
    buffer_distance (float): The buffer distance in kilometers.
    """
    # URLs for feature layers
    countries_feature_layer_url = "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/World_Countries_(Generalized)/FeatureServer/0"
    helcom_mpa_feature_layer_url = "https://maps.helcom.fi/arcgis/rest/services/MADS/Biodiversity/MapServer/54"
    utm_wkid = 32633  # UTM Zone 33N, consider dynamically calculating this based on the country's location

    try:
        # Processing for country selection and buffering
        countries_layer = arcpy.management.MakeFeatureLayer(countries_feature_layer_url, "countries_layer").getOutput(0)
        arcpy.management.SelectLayerByAttribute(countries_layer, "NEW_SELECTION", f"ISO = '{iso_country_code}'")
        arcpy.management.CopyFeatures(countries_layer, "in_memory\\selected_country")
        arcpy.management.Project("in_memory\\selected_country", "in_memory\\selected_country_projected", utm_wkid)

        # Processing for HELCOM MPA
        helcom_mpa_layer = arcpy.management.MakeFeatureLayer(helcom_mpa_feature_layer_url, "helcom_mpa_layer").getOutput(0)
        arcpy.management.CopyFeatures(helcom_mpa_layer, "in_memory\\helcom_mpa")
        arcpy.management.Project("in_memory\\helcom_mpa", "in_memory\\helcom_mpa_projected", utm_wkid)

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

        # Create buffer for the selected country
        buffer_layer = "in_memory\\buffered_country"
        arcpy.analysis.Buffer("in_memory\\selected_country_projected", buffer_layer, f"{buffer_distance} Kilometers", "FULL", "ROUND", "NONE", None, "GEODESIC")

        # Pairwise erase for the buffered country from EEZ
        temp_erased_eez = "in_memory\\temp_erased_eez"
        arcpy.analysis.PairwiseErase(eez_layer, buffer_layer, temp_erased_eez)

        # Pairwise erase for HELCOM MPA from previously erased EEZ
        final_erased_eez = "in_memory\\final_erased_eez"
        arcpy.analysis.PairwiseErase(temp_erased_eez, "in_memory\\helcom_mpa_projected", final_erased_eez)

        # Save the output to a new shapefile
        output_feature_class = f"{output_folder}\\OSSA_{iso_country_code}.shp"
        arcpy.management.CopyFeatures(final_erased_eez, output_feature_class)

        arcpy.AddMessage(f"Successfully processed and saved new EEZ shapefile for {iso_country_code} at {output_feature_class}.")

        # Add the generated shapefile to the current map
        map.addDataFromPath(output_feature_class)

    except Exception as e:
        arcpy.AddError(f"Error in generating offshore substation areas: {e}")

if __name__ == "__main__":
    iso_country_code = arcpy.GetParameterAsText(0)
    output_folder = arcpy.GetParameterAsText(1)
    buffer_distance = float(arcpy.GetParameterAsText(2))  # Ensure this is a float
    generate_offshore_substation_areas(iso_country_code, output_folder, buffer_distance)
