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
            if attempt <= max_retries:
                time.sleep(wait_time)
            else:
                raise e

def create_polyline_feature_layer(npy_file_path, workspace_folder, layer_name):
    """
    Create a feature layer with polylines connecting the coordinates using the .npy data directly
    and add it to the current project map.
    
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
    Create a point feature layer from the .npy data and add it to the current project map.
    
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

if __name__ == "__main__":
    workspace_folder = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\datasets"
    combined_folder = os.path.join(workspace_folder, 'results', 'combined')
    feature_layer_folder = os.path.join(combined_folder, 'features')
    
    npy_file_path_ec1 = os.path.join(combined_folder, 'ec1_ids_c.npy')
    npy_file_path_ec2 = os.path.join(combined_folder, 'ec2_ids_c.npy')
    npy_file_path_ec3 = os.path.join(combined_folder, 'ec3_ids_c.npy')
    npy_file_path_onc = os.path.join(combined_folder, 'onc_ids_c.npy')
    npy_file_path_wf = os.path.join(combined_folder, 'wf_ids_c.npy')
    npy_file_path_eh = os.path.join(combined_folder, 'eh_ids_c.npy')
    npy_file_path_onss = os.path.join(combined_folder, 'onss_ids_c.npy')

    # Generate point feature layers for wind farms, offshore substations, and onshore substations
    create_point_feature_layer(npy_file_path_wf, feature_layer_folder, 'C_WindFarms')
    create_point_feature_layer(npy_file_path_eh, feature_layer_folder, 'C_EnergyHubs')
    create_point_feature_layer(npy_file_path_onss, feature_layer_folder, 'C_OnshoreSubstations')
    
    # Generate feature layer for export cables 1
    create_polyline_feature_layer(npy_file_path_ec1, feature_layer_folder, 'C_ExportCables1')

    # Generate feature layer for export cables 2
    create_polyline_feature_layer(npy_file_path_ec2, feature_layer_folder, 'C_ExportCables2')

    # Generate feature layer for export cables 3
    create_polyline_feature_layer(npy_file_path_ec3, feature_layer_folder, 'C_ExportCables3')

    # Generate feature layer for onshore cables
    create_polyline_feature_layer(npy_file_path_onc, feature_layer_folder, 'C_OnshoreCables')