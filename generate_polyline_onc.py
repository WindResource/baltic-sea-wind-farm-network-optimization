import arcpy
import pandas as pd
import time
import os

def parse_wkt(wkt: str):
    """
    Parse WKT string to get the coordinates for polyline creation.
    """
    # Remove the 'SRID=4326;LINESTRING(' prefix and the closing ')'
    wkt = wkt.replace('SRID=4326;LINESTRING(', '').rstrip(')')
    # Split the coordinate pairs
    coordinates = wkt.split(',')
    # Convert to list of arcpy.Point objects
    points = [arcpy.Point(float(coord.split()[0]), float(coord.split()[1])) for coord in coordinates]
    return points

def get_max_voltage(voltage_str):
    """
    Get the maximum voltage from the voltage string. If the voltage string is empty or NaN, return 0.
    """
    if pd.isnull(voltage_str) or voltage_str == '':
        return 0
    try:
        if isinstance(voltage_str, (int, float)):
            return int(voltage_str)
        voltages = list(map(int, str(voltage_str).split(';')))
        return max(voltages)
    except ValueError:
        return 0

def excel_to_polyline_shapefile(excel_file: str, output_folder: str) -> None:
    """
    Convert data from an Excel file to a polyline shapefile.

    Parameters:
        excel_file (str): Path to the Excel file.
        output_folder (str): Path to the output folder for the shapefile.
    """
    # Define the spatial reference for EPSG:4326 (WGS84)
    spatial_ref = arcpy.SpatialReference(4326)  
    start_time = time.time()

    arcpy.AddMessage("Reading Excel data...")
    # Read Excel data using pandas
    df = pd.read_excel(excel_file)

    # Create a new shapefile to store the polyline features with EPSG:4326 spatial reference
    temp_shapefile = os.path.join(output_folder, "Temp_HighVoltage_Links.shp")
    # Check if the shapefile already exists, delete it if it does
    if arcpy.Exists(temp_shapefile):
        arcpy.Delete_management(temp_shapefile)
    # Create the shapefile
    arcpy.management.CreateFeatureclass(output_folder, "Temp_HighVoltage_Links.shp", "POLYLINE", spatial_reference=spatial_ref)

    # Define fields to store attributes
    fields = [
        ("Voltage", "TEXT"),
        ("MaxVoltage", "LONG")
    ]

    # Add fields to the shapefile
    arcpy.management.AddFields(temp_shapefile, fields)

    # Open an insert cursor to add features to the temporary shapefile
    with arcpy.da.InsertCursor(temp_shapefile, ["SHAPE@", "Voltage", "MaxVoltage"]) as cursor:
        for row in df.itertuples():
            # Extract the necessary data for the polyline
            voltage = row.voltage if pd.notnull(row.voltage) else '0'
            max_voltage = get_max_voltage(voltage)

            # Parse the WKT string to get polyline points
            points = parse_wkt(row.wkt_srid_4326)

            # Create a polyline geometry
            polyline = arcpy.Polyline(arcpy.Array(points), spatial_ref)

            # Insert the row with the geometry and attributes
            cursor.insertRow([polyline, voltage, max_voltage])

    arcpy.AddMessage("Performing spatial join...")

    # Retrieve the OnSS layer
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map_object = aprx.activeMap
    onss_layer = next(layer for layer in map_object.listLayers() if layer.name.startswith("OnSS"))

    # Create an output shapefile for the spatial join result
    output_shapefile = os.path.join(output_folder, "HighVoltage_Links.shp")
    if arcpy.Exists(output_shapefile):
        arcpy.Delete_management(output_shapefile)

    # Perform spatial join to filter polylines within 50 km of any onshore substation point
    arcpy.analysis.SpatialJoin(
        target_features=temp_shapefile,
        join_features=onss_layer,
        out_feature_class=output_shapefile,
        join_type="KEEP_COMMON",
        match_option="WITHIN_A_DISTANCE",
        search_radius="25 Kilometers",
        distance_field_name="DISTANCE"
    )

    arcpy.AddMessage("Adding shapefile to the map...")
    # Add the shapefile to the map
    map_object.addDataFromPath(output_shapefile)

    # Cleanup temporary shapefile
    arcpy.Delete_management(temp_shapefile)

    end_time = time.time()
    arcpy.AddMessage(f"Total processing time: {end_time - start_time} seconds")

if __name__ == "__main__":
    # Get user parameters
    excel_file = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Data\\gridkit_europe\\gridkit_europe-highvoltage-links1.xlsx"
    output_folder = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\highvoltage_links_folder"

    # Call the function to convert Excel to polyline shapefile
    excel_to_polyline_shapefile(excel_file, output_folder)