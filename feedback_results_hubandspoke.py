import arcpy
import numpy as np
import os

def create_export_cable_feature_layer(npy_file_path, workspace_folder, layer_name):
    """
    Create a feature layer with polylines connecting the coordinates of the export cables using the .npy data directly
    and add it to the current project map.
    
    Parameters:
    - npy_file_path: The path to the .npy file containing export cable data.
    - workspace_folder: The path to the workspace folder where the feature class will be stored.
    - layer_name: The name of the layer to be created in the current map.
    """
    # Load the export cable data from the .npy file
    ec_data = np.load(npy_file_path)
    
    # Create the feature class in the output workspace folder to store the polylines
    lines_path = os.path.join(workspace_folder, f"{layer_name}.shp")
    if arcpy.Exists(lines_path):
        arcpy.Delete_management(lines_path)
    arcpy.management.CreateFeatureclass(workspace_folder, layer_name, 'POLYLINE', spatial_reference=4326)
    arcpy.management.AddFields(lines_path, [
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
    ])

    # Insert the polylines into the feature class
    with arcpy.da.InsertCursor(lines_path, ['EC_ID', 'Comp_1_ID', 'Comp_2_ID', 'SHAPE@', 'Lon_1', 'Lat_1', 'Lon_2', 'Lat_2', 'Distance', 'Capacity', 'Cost']) as insert_cursor:
        for row in ec_data:
            ec_id = int(row['ec_id'])
            comp_1_id = int(row['comp_1_id'])
            comp_2_id = int(row['comp_2_id'])
            lon_1 = float(row['lon_1'])
            lat_1 = float(row['lat_1'])
            lon_2 = float(row['lon_2'])
            lat_2 = float(row['lat_2'])
            distance = float(row['distance'])
            capacity = float(row['capacity'])
            cost = float(row['cost'])
            point_1 = arcpy.Point(lon_1, lat_1)
            point_2 = arcpy.Point(lon_2, lat_2)
            array = arcpy.Array([point_1, point_2])
            polyline = arcpy.Polyline(array)
            insert_cursor.insertRow((ec_id, comp_1_id, comp_2_id, polyline, lon_1, lat_1, lon_2, lat_2, distance, capacity, cost))

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
    arcpy.management.AddFields(points_path, [
        ['ID', 'LONG'],
        ['ISO', 'TEXT'],
        ['Capacity', 'DOUBLE'],
        ['Cost', 'DOUBLE']
    ])

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
    hubspoke_folder = os.path.join(workspace_folder, 'results', 'hubspoke')
    feature_layer_folder = os.path.join(hubspoke_folder, 'features')
    
    npy_file_path_ec1 = os.path.join(hubspoke_folder, 'ec1_ids_hs.npy')
    npy_file_path_ec2 = os.path.join(hubspoke_folder, 'ec2_ids_hs.npy')
    npy_file_path_wf = os.path.join(hubspoke_folder, 'wf_ids_hs.npy')
    npy_file_path_eh = os.path.join(hubspoke_folder, 'eh_ids_hs.npy')
    npy_file_path_onss = os.path.join(hubspoke_folder, 'onss_ids_hs.npy')

    # Generate point feature layers for wind farms, offshore substations, and onshore substations
    create_point_feature_layer(npy_file_path_wf, feature_layer_folder, 'HS_WindFarms')
    create_point_feature_layer(npy_file_path_eh, feature_layer_folder, 'HS_EnergyHubs')
    create_point_feature_layer(npy_file_path_onss, feature_layer_folder, 'HS_OnshoreSubstations')
    
    # Generate feature layer for export cables 1
    create_export_cable_feature_layer(npy_file_path_ec1, feature_layer_folder, 'HS_ExportCables1')

    # Generate feature layer for export cables 2
    create_export_cable_feature_layer(npy_file_path_ec2, feature_layer_folder, 'HS_ExportCables2')
