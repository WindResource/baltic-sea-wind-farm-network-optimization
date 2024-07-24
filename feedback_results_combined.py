import arcpy
import numpy as np
import os
import time

def add_fields_with_retry(feature_class, fields, max_retries=3, wait_time=0.5):
    """
    Adds fields to a feature class with a retry mechanism in case of failure.

    Parameters:
    - feature_class: The feature class to which fields will be added.
    - fields: The fields to be added.
    - max_retries: Maximum number of retry attempts.
    - wait_time: Time to wait between retries in seconds.
    """
    for attempt in range(max_retries):
        try:
            arcpy.management.AddFields(feature_class, fields)
            return
        except Exception as e:
            if attempt < max_retries:
                time.sleep(wait_time)
            else:
                raise e

def create_polyline_feature_layer(npy_file_path, workspace_folder, layer_name):
    """
    Creates a polyline feature layer from .npy data and adds it to the current project map.

    Parameters:
    - npy_file_path: The path to the .npy file containing cable data.
    - workspace_folder: The path to the workspace folder where the feature class will be stored.
    - layer_name: The name of the layer to be created in the current map.
    """
    # Load the cable data from the .npy file
    cable_data = np.load(npy_file_path)
    
    # Define the fields for the feature class
    fields = [
        ['EC_ID', 'LONG'],
        ['Comp_1_ID', 'LONG'],
        ['Comp_2_ID', 'LONG'],
        ['Lon_1', 'DOUBLE'],
        ['Lat_1', 'DOUBLE'],
        ['Lon_2', 'DOUBLE'],
        ['Lat_2', 'DOUBLE'],
        ['Distance', 'DOUBLE'],
        ['Capacity', 'DOUBLE'],
        ['Cost', 'DOUBLE']
    ]
    
    # Create the feature class in the output workspace folder to store the polylines
    lines_path = os.path.join(workspace_folder, f"{layer_name}.shp")
    if arcpy.Exists(lines_path):
        arcpy.Delete_management(lines_path)
    arcpy.management.CreateFeatureclass(workspace_folder, layer_name, 'POLYLINE', spatial_reference=4326)
    
    # Add fields with retry logic
    add_fields_with_retry(lines_path, fields)

    # Insert the polylines into the feature class
    with arcpy.da.InsertCursor(lines_path, [field[0] for field in fields] + ['SHAPE@']) as insert_cursor:
        for row in cable_data:
            row_data = [row[field[0].lower()] for field in fields]
            lon_1 = float(row['lon_1'])
            lat_1 = float(row['lat_1'])
            lon_2 = float(row['lon_2'])
            lat_2 = float(row['lat_2'])
            point_1 = arcpy.Point(lon_1, lat_1)
            point_2 = arcpy.Point(lon_2, lat_2)
            array = arcpy.Array([point_1, point_2])
            polyline = arcpy.Polyline(array)
            insert_cursor.insertRow(row_data + [polyline])

    # Add the feature class to the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap
    map.addDataFromPath(lines_path)

    print(f'Feature layer {layer_name} added successfully to the current map.')

def create_point_feature_layer(npy_file_path, workspace_folder, layer_name):
    """
    Creates a point feature layer from .npy data and adds it to the current project map.

    Parameters:
    - npy_file_path: The path to the .npy file containing point data.
    - workspace_folder: The path to the workspace folder where the feature class will be stored.
    - layer_name: The name of the layer to be created in the current map.
    """
    # Load the point data from the .npy file
    point_data = np.load(npy_file_path)
    
    # Create the feature class in the output workspace folder to store the points
    points_path = os.path.join(workspace_folder, f"{layer_name}.shp")
    if arcpy.Exists(points_path):
        arcpy.Delete_management(points_path)
    arcpy.management.CreateFeatureclass(workspace_folder, layer_name, 'POINT', spatial_reference=4326)
    
    # Define the fields for the feature class
    fields = [
        ['ID', 'LONG'],
        ['ISO', 'TEXT'],
        ['Capacity', 'DOUBLE'],
        ['Cost', 'DOUBLE']
    ]
    
    # Add fields with retry logic
    add_fields_with_retry(points_path, fields)

    # Insert the points into the feature class
    with arcpy.da.InsertCursor(points_path, ['SHAPE@', 'ID', 'ISO', 'Capacity', 'Cost']) as insert_cursor:
        for row in point_data:
            point = arcpy.Point(float(row['lon']), float(row['lat']))
            id = int(row['id'])
            iso = str(row['iso'])
            capacity = float(row['capacity'])
            cost = float(row['cost'])
            insert_cursor.insertRow((point, id, iso, capacity, cost))

    # Add the feature class to the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap
    map.addDataFromPath(points_path)

    print(f'Feature layer {layer_name} added successfully to the current map.')

def process_feature_layers(npy_file_paths, feature_layer_folder):
    """
    Processes and adds all .npy files in the given folder as feature layers.

    Parameters:
    - npy_file_paths: List of paths to .npy files.
    - feature_layer_folder: The base folder where feature layers will be saved.
    """
    for file_path in npy_file_paths:
        file_name = os.path.basename(file_path).split('.')[0]
        # Determine if the file should be processed as point or polyline based on its name
        if any(identifier in file_name for identifier in ['eh', 'onss', 'wf']):
            create_point_feature_layer(file_path, feature_layer_folder, file_name)
        elif any(identifier in file_name for identifier in ['ec1', 'ec2', 'ec3', 'onc']):
            create_polyline_feature_layer(file_path, feature_layer_folder, file_name)

if __name__ == "__main__":
    # Define the paths to the workspace and folders
    workspace_folder = f"C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\datasets\\results\\combined\\process"
    combined_folder = os.path.join(workspace_folder)
    feature_layer_folder = os.path.join(combined_folder, 'features')

    # List all .npy files in the combined folder
    npy_file_paths = [os.path.join(combined_folder, f) for f in os.listdir(combined_folder) if f.endswith('.npy')]
    
    # Process the files if any are found
    if npy_file_paths:
        if not os.path.exists(feature_layer_folder):
            os.makedirs(feature_layer_folder)
        process_feature_layers(npy_file_paths, feature_layer_folder)
    else:
        print("No .npy files found in the combined folder.")