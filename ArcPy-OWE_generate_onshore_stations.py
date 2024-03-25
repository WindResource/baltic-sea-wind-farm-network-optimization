import arcpy
import os

def process_high_voltage_stations(highvoltage_vertices_folder: str, iso_country_code: str, onshore_station_folder: str) -> None:
    """
    Selects high voltage substations and stations based on ISO country code,
    exports the selected features to a new shapefile in a specified output folder, and adds the layer to the current map.

    Parameters:
        highvoltage_vertices_folder (str): Folder containing the input shapefiles.
        iso_country_code (str): ISO country code to select substations and stations for.
        onshore_station_folder (str): Folder where the output shapefile will be saved.
    """
    try:
        # Find the first shapefile in the given folder
        for file in os.listdir(highvoltage_vertices_folder):
            if file.endswith(".shp"):
                vertices_feature_class = os.path.join(highvoltage_vertices_folder, file)
                break
        else:
            raise Exception("No shapefile found in the specified folder.")

        # Create a feature layer from the high voltage vertices data
        vertices_layer = arcpy.management.MakeFeatureLayer(vertices_feature_class, "HighVoltageVertices").getOutput(0)

        # Define the selection query to include both Substation and Station types
        query = f"(Type = 'Substation' OR Type = 'Station') AND ISO = '{iso_country_code}'"
        arcpy.management.SelectLayerByAttribute(vertices_layer, "NEW_SELECTION", query)

        # Output shapefile path
        output_shapefile = os.path.join(onshore_station_folder, f"{iso_country_code}_Substations_Stations.shp")

        # Check if the output shapefile already exists and delete it
        if arcpy.Exists(output_shapefile):
            arcpy.management.Delete(output_shapefile)

        # Copy the selected features to a new shapefile
        arcpy.management.CopyFeatures(vertices_layer, output_shapefile)

        # Create a feature layer from the shapefile
        output_layer = arcpy.management.MakeFeatureLayer(output_shapefile, f"{iso_country_code}_Substations_Stations_Layer").getOutput(0)

        # Use arcpy.mp to add the layer to the map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map_object = aprx.activeMap

        # Add the layer to the map
        map_object.addLayer(output_layer)

        arcpy.AddMessage(f"Substations and stations for ISO country code {iso_country_code} have been selected, exported, and added to the current map.")

    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(str(e))

if __name__ == "__main__":
    # Input parameters from user
    highvoltage_vertices_folder = arcpy.GetParameterAsText(0)  # Input folder for the shapefiles
    iso_country_code = arcpy.GetParameterAsText(1)  # ISO country code
    onshore_station_folder = arcpy.GetParameterAsText(2)  # Output folder for the shapefile

    # Process the high voltage stations
    process_high_voltage_stations(highvoltage_vertices_folder, iso_country_code, onshore_station_folder)
