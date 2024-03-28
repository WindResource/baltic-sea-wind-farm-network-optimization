import arcpy

def generate_offshore_substation_areas(country_name, output_folder, buffer_distance):
    """
    Creates a new EEZ shapefile for a specified country, erases the pairwise buffered areas of the specified country from the EEZ shapefile,
    and adds the generated shapefile to the current ArcGIS map.

    Parameters:
    country_name (str): The name of the country for which to generate the offshore substation areas.
    output_folder (str): The folder path where the new EEZ shapefile will be saved.
    buffer_distance (float): The buffer distance in kilometers.
    """
    feature_layer_url = "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/World_Countries_(Generalized)/FeatureServer/0"
    utm_wkid = 32633  # UTM Zone 33N

    try:
        # Create feature layer from URL
        countries_layer = arcpy.management.MakeFeatureLayer(feature_layer_url, "countries_layer").getOutput(0)
        
        # Select the specified country
        arcpy.management.SelectLayerByAttribute(countries_layer, "NEW_SELECTION", f"ISO = '{country_name}'")
        
        # Convert the feature layer to a polygon feature layer and project it
        arcpy.management.CopyFeatures(countries_layer, "in_memory\\selected_country")
        arcpy.management.Project("in_memory\\selected_country", "in_memory\\selected_country_projected", utm_wkid)

        # Ensure the EEZ layer is available
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map = aprx.activeMap
        input_layer = None
        for layer in map.listLayers():
            if layer.name.startswith('eez_v12'):
                input_layer = layer
                break

        if input_layer is None:
            arcpy.AddError("No EEZ layer found. Ensure a layer starting with 'eez_v12' is loaded in the map.")
            return

        # Pairwise buffer the selected country and pairwise erase from the EEZ layer
        buffer_layer = "in_memory\\buffered_country"
        erased_layer = "in_memory\\erased_eez"
        arcpy.analysis.PairwiseBuffer("in_memory\\selected_country_projected", buffer_layer, buffer_distance, "Kilometers")
        arcpy.analysis.PairwiseErase(input_layer, buffer_layer, erased_layer)

        # Save the output to a new shapefile
        output_feature_class = f"{output_folder}\\new_eez_shapefile_for_{country_name.replace(' ', '_')}.shp"
        arcpy.management.CopyFeatures(erased_layer, output_feature_class)

        arcpy.AddMessage(f"Successfully processed and saved new EEZ shapefile for {country_name} at {output_feature_class}.")

        # Add the generated shapefile to the current map
        map.addDataFromPath(output_feature_class)

    except Exception as e:
        arcpy.AddError(f"Error in generating offshore substation areas: {e}")

if __name__ == "__main__":
    country_name = arcpy.GetParameterAsText(0)
    output_folder = arcpy.GetParameterAsText(1)
    buffer_distance = float(arcpy.GetParameterAsText(2))  # Convert buffer distance to float
    generate_offshore_substation_areas(country_name, output_folder, buffer_distance)
