import arcpy
import pandas as pd
import time
import os
from datetime import datetime

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
    arcpy.analysis.PairwiseBuffer("in_memory\\eez_layer", "in_memory\\eez_buffer", "200 Kilometers")

    # Select point features within the buffer
    arcpy.analysis.PairwiseClip(point_features, "in_memory\\eez_buffer", "in_memory\\point_features")
    
    # Perform the first spatial join between the point features and the projected country polygons using "WITHIN" criteria
    arcpy.analysis.SpatialJoin("in_memory\\point_features", "in_memory\\countries_projected", "in_memory\\point_country_join_first",
                                join_type="KEEP_ALL", match_option="WITHIN")
    
    # Perform the second spatial join between the points with null country values and country polygons within a certain distance using "CLOSEST" criteria
    arcpy.analysis.SpatialJoin("in_memory\\point_country_join_first", "in_memory\\eez_layer", "in_memory\\point_country_join_second",
                                join_type="KEEP_ALL", match_option="CLOSEST", search_radius="2 Kilometers")
    
    # Add the Country and ISO fields to the original point features
    arcpy.management.AddFields("in_memory\\point_features", [("Country", "TEXT"),("ISO", "TEXT"),("OnSS_ID", "TEXT")])

    # Determine the unique identifier field in the point features
    point_features_fields = [f.name for f in arcpy.ListFields("in_memory\\point_features")]
    unique_id_field = "OBJECTID" if "OBJECTID" in point_features_fields else arcpy.Describe("in_memory\\point_features").OIDFieldName
    
    # Update the "Country" and "ISO" fields from the first spatial join
    with arcpy.da.UpdateCursor("in_memory\\point_country_join_first", [unique_id_field, "COUNTRY", "ISO_CC"]) as update_cursor_first:
        country_iso_mapping_first = {row[0]: (row[1], row[2]) for row in update_cursor_first}

    with arcpy.da.UpdateCursor("in_memory\\point_features", [unique_id_field, "Country", "ISO"]) as update_cursor:
        for update_row in update_cursor:
            if update_row[0] in country_iso_mapping_first:
                country_value, iso_cc_value = country_iso_mapping_first[update_row[0]]
                update_row[1] = country_value if country_value else "Unknown"
                update_row[2] = iso_cc_value if iso_cc_value else "Unknown"
                update_cursor.updateRow(update_row)

    # Update the "Country" and "ISO" fields from the second spatial join  
    with arcpy.da.UpdateCursor("in_memory\\point_country_join_second", [unique_id_field, "TERRITORY1", "ISO_TER1"]) as update_cursor_second:
        country_iso_mapping_second = {row[0]: (row[1], row[2]) for row in update_cursor_second}

    with arcpy.da.UpdateCursor("in_memory\\point_features", [unique_id_field, "Country", "ISO", "Type"]) as update_cursor:
        for update_row in update_cursor:
            if update_row[0] in country_iso_mapping_second:
                country_value, iso_cc_value = country_iso_mapping_second[update_row[0]]
                if (update_row[1] == "Unknown" or update_row[2] == "Unknown"):  # Check if Country or ISO is Unknown
                    if update_row[3] in ['Station', 'Substation', 'Sub_station'] and (country_value or iso_cc_value):
                        update_row[1] = country_value
                        update_row[2] = iso_mp.get(iso_cc_value, "Unknown")
                        update_cursor.updateRow(update_row)
                    else:
                        update_cursor.deleteRow()
                elif update_row[3] not in ['Station', 'Substation', 'Sub_station']:
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

    # Generate a timestamp to include in the output shapefile name
    timestamp = datetime.now().strftime(f"%y%m%d_%H%M%S")
    output_shapefile_name = f"OnSS_BalticSea_{timestamp}.shp"

    # Create a new shapefile to store the point features with EPSG:4326 spatial reference
    output_shapefile = os.path.join(highvoltage_vertices_folder, output_shapefile_name)
    
    # Create the shapefile
    arcpy.management.CreateFeatureclass(highvoltage_vertices_folder, output_shapefile_name, "POINT", spatial_reference=spatial_ref)

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

            # Filter for station, substation, and sub_station types
            if typ.lower() in ['station', 'substation', 'sub_station']:
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
