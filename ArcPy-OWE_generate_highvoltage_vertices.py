import arcpy
import pandas as pd
import pyproj
import time

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

def excel_to_shapefile(excel_file: str, highvoltage_vertices_folder: str) -> None:
    """
    Convert data from an Excel file to a shapefile.

    Parameters:
        excel_file (str): Path to the Excel file.
        highvoltage_vertices_folder (str): Path to the output folder for the shapefile.
    """
    start_time = time.time()
    try:
        # Read Excel data using pandas
        df = pd.read_excel(excel_file)

        # Define the output shapefile path
        output_shapefile = highvoltage_vertices_folder + "\\highvoltage_vertices.shp"

        # Define the spatial reference for EPSG:32633
        spatial_ref = arcpy.SpatialReference(32633)

        # Create a new shapefile to store the point features with EPSG:32633 spatial reference
        arcpy.CreateFeatureclass_management(highvoltage_vertices_folder, "highvoltage_vertices.shp", "POINT", spatial_reference=spatial_ref)

        # Define fields to store attributes
        fields = [
            ("Xcoord", "DOUBLE"),
            ("Ycoord", "DOUBLE"),
            ("Type", "TEXT"),
            ("Voltage", "TEXT"),
            ("Frequency", "TEXT")
        ]

        # Add fields to the shapefile
        for field_name, field_type in fields:
            arcpy.AddField_management(output_shapefile, field_name, field_type)

        # Convert lon and lat to UTM (WKID 32633)
        lon_array = df['lon'].values
        lat_array = df['lat'].values
        x_array, y_array = lon_lat_to_utm(lon_array, lat_array)

        # Create a list to store the features
        features = []

        # Loop through data to create features
        with arcpy.da.InsertCursor(output_shapefile, ["SHAPE@XY", "Xcoord", "Ycoord", "Type", "Voltage", "Frequency"]) as cursor:
            for i, row in df.iterrows():
                voltage, frequency = row['voltage'], row['frequency']
                typ = row['typ'].capitalize()
                x, y = x_array[i], y_array[i]

                # Check if voltage is null
                if pd.isnull(voltage):
                    voltage = ""

                # Check if frequency is null
                if pd.isnull(frequency):
                    frequency = ""

                # Insert the row with the geometry and attributes
                cursor.insertRow([(x, y), x, y, typ, voltage, frequency])

        # Use arcpy.mp to add the layer to the map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map_object = aprx.activeMap

        # Add the layer to the map
        map_object.addDataFromPath(output_shapefile)

        end_time = time.time()
        arcpy.AddMessage(f"Total processing time: {end_time - start_time} seconds")

    except Exception as e:
        arcpy.AddMessage(f"Error occurred: {e}")

if __name__ == "__main__":
    # Get user parameters
    highvoltage_vertices = arcpy.GetParameterAsText(0)
    highvoltage_vertices_folder = arcpy.GetParameterAsText(1)

    # Call the function to convert Excel to shapefile
    excel_to_shapefile(highvoltage_vertices, highvoltage_vertices_folder)
