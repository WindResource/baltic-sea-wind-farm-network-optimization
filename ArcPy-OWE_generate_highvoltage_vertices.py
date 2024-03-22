import arcpy
import pandas as pd
import pyproj
import time
import os

def lon_lat_to_utm(lon_array, lat_array):
    """
    Convert longitude and latitude coordinates to UTM coordinates.

    Parameters:
        lon_array (numpy.ndarray): Array of longitude values.
        lat_array (numpy.ndarray): Array of latitude values.

    Returns:
        tuple: Tuple containing arrays of UTM x-coordinates and y-coordinates.
    """
    # Define the projection from WGS84 (EPSG:4326) to UTM Zone 33N (EPSG:32633)
    wgs84 = pyproj.Proj(init='epsg:4326')
    utm33n = pyproj.Proj(init='epsg:32633')

    try:
        # Perform the transformation
        x_array, y_array = pyproj.transform(wgs84, utm33n, lon_array, lat_array)
        return x_array, y_array
    except Exception as e:
        print(f"Error occurred during coordinate transformation: {e}")
        return None, None

def identify_countries(point_features, feature_layer_url):
    """
    Identify the countries based on point features using a feature service.

    Parameters:
        point_features (str): Path to the point features.
        feature_layer_url (str): URL of the feature layer containing country boundaries.

    Returns:
        list: List of country names.
    """
    try:
        # Create feature layer from URL
        countries_layer = arcpy.management.MakeFeatureLayer(feature_layer_url, "countries_layer").getOutput(0)

        # Check if the target feature class exists
        if not arcpy.Exists(point_features):
            return []

        # Perform a spatial join between the point features and the country polygons
        arcpy.analysis.SpatialJoin(point_features, countries_layer, "in_memory\\point_country_join", 
                                    join_type="KEEP_COMMON", match_option="COMPLETELY_WITHIN")

        # Extract the country names from the spatial join result
        country_names = []
        with arcpy.da.SearchCursor("in_memory\\point_country_join", ["COUNTRY"]) as cursor:
            for row in cursor:
                country_names.append(row[0])

        return country_names

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def excel_to_shapefile(excel_file: str, highvoltage_vertices_folder: str, feature_layer_url: str) -> None:
    """
    Convert data from an Excel file to a shapefile.

    Parameters:
        excel_file (str): Path to the Excel file.
        highvoltage_vertices_folder (str): Path to the output folder for the shapefile.
        feature_layer_url (str): URL of the feature layer containing country boundaries.
    """
    start_time = time.time()
    try:
        arcpy.AddMessage("Reading Excel data...")
        # Read Excel data using pandas
        df = pd.read_excel(excel_file)

        arcpy.AddMessage("Creating output shapefile...")
        # Define the output shapefile path
        output_shapefile = os.path.join(highvoltage_vertices_folder, "highvoltage_vertices.shp")

        # Define the spatial reference for EPSG:32633
        spatial_ref = arcpy.SpatialReference(32633)

        # Create a new shapefile to store the point features with EPSG:32633 spatial reference
        arcpy.management.CreateFeatureclass(highvoltage_vertices_folder, "highvoltage_vertices.shp", "POINT", spatial_reference=spatial_ref)

        arcpy.AddMessage("Adding fields to shapefile...")
        # Define fields to store attributes
        fields = [
            ("Xcoord", "DOUBLE"),
            ("Ycoord", "DOUBLE"),
            ("Type", "TEXT"),
            ("Voltage", "TEXT"),
            ("Frequency", "TEXT"),
            ("Country", "TEXT")
        ]

        # Add fields to the shapefile
        for field_name, field_type in fields:
            arcpy.management.AddField(output_shapefile, field_name, field_type)

        # Convert lon and lat to UTM (WKID 32633)
        arcpy.AddMessage("Converting longitude and latitude to UTM...")
        lon_array = df['lon'].values
        lat_array = df['lat'].values
        x_array, y_array = lon_lat_to_utm(lon_array, lat_array)

        arcpy.AddMessage("Creating point features and adding to feature class...")
        # Open an insert cursor to add features to the output shapefile
        with arcpy.da.InsertCursor(output_shapefile, ["SHAPE@XY", "Xcoord", "Ycoord", "Type", "Voltage", "Frequency", "Country"]) as cursor:
            for i, row in enumerate(df.iterrows()):
                voltage, frequency = row[1]['voltage'], row[1]['frequency']
                typ = row[1]['typ'].capitalize()
                x, y = x_array[i], y_array[i]

                # Check if voltage is null
                if pd.isnull(voltage):
                    voltage = ""

                # Check if frequency is null
                if pd.isnull(frequency):
                    frequency = ""

                # Insert the row with the geometry and attributes
                cursor.insertRow([(x, y), x, y, typ, voltage, frequency, ""])

        arcpy.AddMessage("Identifying countries...")
        # Identify countries for all points
        country_names = identify_countries(output_shapefile, feature_layer_url)

        arcpy.AddMessage("Updating country names...")
        # Update the 'Country' field in the shapefile
        with arcpy.da.UpdateCursor(output_shapefile, "Country") as cursor:
            for i, row in enumerate(cursor):
                row[0] = country_names[i]
                cursor.updateRow(row)

        arcpy.AddMessage("Adding shapefile to the map...")
        # Add the shapefile to the map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map_object = aprx.activeMap
        map_object.addDataFromPath(output_shapefile)

        end_time = time.time()
        arcpy.AddMessage(f"Total processing time: {end_time - start_time} seconds")

    except Exception as e:
        arcpy.AddMessage(f"An error occurred: {e}")

if __name__ == "__main__":
    # Get user parameters
    highvoltage_vertices = arcpy.GetParameterAsText(0)
    highvoltage_vertices_folder = arcpy.GetParameterAsText(1)
    feature_layer_url = "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/World_Countries_(Generalized)/FeatureServer/0"

    # Call the function to convert Excel to shapefile
    excel_to_shapefile(highvoltage_vertices, highvoltage_vertices_folder, feature_layer_url)
