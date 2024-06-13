import arcpy
import pandas as pd
import time
import os

def identify_countries(point_features):
    """
    Identify the countries based on point features using a predefined feature service URL.

    Parameters:
        point_features (str): Path to the point features.

    Returns:
        str: Path to the modified point features shapefile.
    """
    # Define ISO 2 char and ISO 3 char for Baltic Sea countries
    iso_eez_country_code = ['DNK', 'EST', 'FIN', 'DEU', 'LVA', 'LTU', 'POL', 'SWE']

    # Mapping between 3-letter and 2-letter ISO country codes
    iso_mp = { "DNK": "DK", "EST": "EE", "FIN": "FI", "DEU": "DE", "LVA": "LV", "LTU": "LT", "POL": "PL", "SWE": "SE" }

    feature_layer_url = "https://services2.arcgis.com/VNo0ht0YPXJoI4oE/ArcGIS/rest/services/World_Countries_Specifically_Europe/FeatureServer/0"
    wgs84 = arcpy.SpatialReference(4326)
    
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
    
    # Select EEZ countries
    arcpy.analysis.Select(eez_layer, "in_memory\\eez_layer", f"ISO_TER1 IN {tuple(iso_eez_country_code)}")

    # Create feature layer from URL
    countries_layer = arcpy.management.MakeFeatureLayer(feature_layer_url, "countries_layer").getOutput(0)
    # Select countries
    arcpy.analysis.Select(countries_layer, "in_memory\\countries_polygon", f"ISO_CC IN {tuple(iso_eez_country_code)}")
    # Project the feature layer to the specified UTM Zone
    arcpy.management.Project("in_memory\\countries_polygon", "in_memory\\countries_projected", wgs84)

    # Create a buffer around the EEZ layer boundary
    arcpy.analysis.PairwiseBuffer("in_memory\\eez_layer", "in_memory\\eez_buffer", "150 Kilometers")

    # Select point features within the buffer
    arcpy.analysis.PairwiseClip(point_features, "in_memory\\eez_buffer", "in_memory\\point_features")
    
    # Perform the first spatial join between the point features and the projected country polygons using "WITHIN" criteria
    arcpy.analysis.SpatialJoin("in_memory\\point_features", "in_memory\\countries_projected", "in_memory\\point_country_join_first",
                                join_type="KEEP_ALL", match_option="WITHIN")
    
    # Perform the second spatial join between the points with null country values and country polygons within a certain distance using "CLOSEST" criteria
    arcpy.analysis.SpatialJoin("in_memory\\point_features", "in_memory\\eez_layer", "in_memory\\point_country_join_second",
                                join_type="KEEP_ALL", match_option="CLOSEST", search_radius="2 Kilometers")
    
    # Add the Country and ISO fields to the original point features
    arcpy.management.AddFields("in_memory\\point_features", [("Country", "TEXT"),("ISO", "TEXT"),("OnSS_ID", "TEXT")])
    
    # Update the "Country" and "ISO" fields from the first spatial join
    with arcpy.da.UpdateCursor("in_memory\\point_features", ["Country", "ISO"]) as update_cursor:
        with arcpy.da.SearchCursor("in_memory\\point_country_join_first", ["COUNTRY", "ISO"]) as search_cursor:
            for update_row, (country_value, iso_cc_value) in zip(update_cursor, search_cursor):
                update_row[0] = country_value if country_value else "Unknown"
                update_row[1] = iso_cc_value if iso_cc_value else "Unknown"
                update_cursor.updateRow(update_row)

    # Update the "Country" and "ISO" fields from the second spatial join  
    with arcpy.da.UpdateCursor("in_memory\\point_features", ["Country", "ISO", "Type"]) as update_cursor:
        with arcpy.da.SearchCursor("in_memory\\point_country_join_second", ["TERRITORY1", "ISO_TER1"]) as search_cursor:
            for (country, ISO, type), (country_value, iso_cc_value) in zip(update_cursor, search_cursor):
                if (country == "Unknown" or ISO == "Unknown"):  # Check if Country or ISO is Unknown
                    if type in ['Station', 'Substation', 'Sub_station'] and (country_value or iso_cc_value):
                        country = country_value
                        ISO = iso_mp.get(iso_cc_value, "Unknown")
                        update_cursor.updateRow((country, ISO, 'Substation'))
                    else:
                        update_cursor.deleteRow()
                elif type not in ['Station', 'Substation', 'Sub_station']:
                    update_cursor.deleteRow()
                    
    # Generate OnSS_ID for substations
    onss_id = 0
    with arcpy.da.UpdateCursor("in_memory\\point_features", ["OnSS_ID"]) as update_cursor:
        for update_row in update_cursor:
            onss_id += 1
            update_row[0] = onss_id
            update_cursor.updateRow(update_row)
            
    # Copy features to in-memory
    arcpy.management.CopyFeatures("in_memory\\point_features", point_features)

    return point_features

def excel_to_shapefile(excel_file: str, highvoltage_vertices_folder: str) -> None:
    """
    Convert data from an Excel file to a shapefile.

    Parameters:
        excel_file (str): Path to the Excel file.
        highvoltage_vertices_folder (str): Path to the output folder for the shapefile.
    """
    # Define the spatial reference for EPSG:4326 (WGS84)
    spatial_ref = arcpy.SpatialReference(4326)  
    start_time = time.time()

    arcpy.AddMessage("Reading Excel data...")
    # Read Excel data using pandas
    df = pd.read_excel(excel_file)

    # Create a new shapefile to store the point features with EPSG:4326 spatial reference
    output_shapefile = os.path.join(highvoltage_vertices_folder, "OnSS_BalticSea.shp")
    # Check if the shapefile already exists, delete it if it does
    if arcpy.Exists(output_shapefile):
        arcpy.Delete_management(output_shapefile)
    # Create the shapefile
    arcpy.management.CreateFeatureclass(highvoltage_vertices_folder, "OnSS_BalticSea.shp", "POINT", spatial_reference=spatial_ref)

    # Define fields to store attributes
    fields = [
        ("Longitude", "DOUBLE"),
        ("Latitude", "DOUBLE"),
        ("Type", "TEXT"),
        ("Voltage", "TEXT"),
        ("Frequency", "TEXT")
    ]

    # Add fields to the shapefile
    arcpy.management.AddFields(output_shapefile, fields)

    # Open an insert cursor to add features to the output shapefile
    with arcpy.da.InsertCursor(output_shapefile, ["SHAPE@XY", "Longitude", "Latitude", "Type", "Voltage", "Frequency"]) as cursor:
        for row in df.itertuples():
            longitude, latitude = row.lon, row.lat
            typ, voltage, frequency = row.typ.capitalize(), row.voltage, row.frequency

            # Check if voltage is null
            if pd.isnull(voltage):
                voltage = ""

            # Check if frequency is null
            if pd.isnull(frequency):
                frequency = ""

            # Insert the row with the geometry and attributes
            cursor.insertRow([(longitude, latitude), longitude, latitude, typ, voltage, frequency])

    arcpy.AddMessage("Identifying countries...")
    # Identify countries and add the country field to the point features
    output_shapefile = identify_countries(output_shapefile)

    arcpy.AddMessage("Adding shapefile to the map...")
    # Add the shapefile to the map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map_object = aprx.activeMap
    map_object.addDataFromPath(output_shapefile)

    end_time = time.time()
    arcpy.AddMessage(f"Total processing time: {end_time - start_time} seconds")


if __name__ == "__main__":
    # Get user parameters
    highvoltage_vertices = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Data\\gridkit_europe\\gridkit_europe-highvoltage-vertices1.xlsx"
    highvoltage_vertices_folder = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\onshore_station_folder"

    # Call the function to convert Excel to shapefile
    excel_to_shapefile(highvoltage_vertices, highvoltage_vertices_folder)
