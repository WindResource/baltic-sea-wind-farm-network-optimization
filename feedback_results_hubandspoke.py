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
    arcpy.management.AddField(lines_path, 'EC_ID', 'LONG')
    arcpy.management.AddField(lines_path, 'Distance', 'DOUBLE')
    arcpy.management.AddField(lines_path, 'Capacity', 'LONG')
    arcpy.management.AddField(lines_path, 'Cost', 'DOUBLE')
    
    # Create polylines by connecting points with the same EC_ID
    points_dict = {}
    for row in ec_data:
        ec_id = int(row['ec_id'])
        point = (float(row['lon']), float(row['lat']))
        distance = float(row['distance'])
        capacity = float(row['capacity'])
        cost = float(row['cost'])
        
        if ec_id not in points_dict:
            points_dict[ec_id] = []
        points_dict[ec_id].append((point, distance, capacity, cost))
    
    # Insert the polylines into the feature class
    with arcpy.da.InsertCursor(lines_path, ['EC_ID', 'SHAPE@', 'Distance', 'Capacity', 'Cost']) as insert_cursor:
        for ec_id, points in points_dict.items():
            if len(points) == 2:
                array = arcpy.Array([arcpy.Point(*points[0][0]), arcpy.Point(*points[1][0])])
                polyline = arcpy.Polyline(array)
                insert_cursor.insertRow((ec_id, polyline, points[0][1], points[0][2], points[0][3]))

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
    arcpy.management.AddField(points_path, 'ID', 'LONG')
    arcpy.management.AddField(points_path, 'ISO', 'TEXT')
    arcpy.management.AddField(points_path, 'Capacity', 'DOUBLE')
    arcpy.management.AddField(points_path, 'Cost', 'DOUBLE')

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
    
    npy_file_path_ec1 = os.path.join(hubspoke_folder, 'ec1_ids_hs.npy')
    npy_file_path_ec2 = os.path.join(hubspoke_folder, 'ec2_ids_hs.npy')
    npy_file_path_wf = os.path.join(hubspoke_folder, 'wf_ids_hs.npy')
    npy_file_path_eh = os.path.join(hubspoke_folder, 'eh_ids_hs.npy')
    npy_file_path_onss = os.path.join(hubspoke_folder, 'onss_ids_hs.npy')

    # Generate feature layer for export cables 1
    create_export_cable_feature_layer(npy_file_path_ec1, workspace_folder, 'HS_ExportCables1')

    # Generate feature layer for export cables 2
    create_export_cable_feature_layer(npy_file_path_ec2, workspace_folder, 'HS_ExportCables2')

    # Generate point feature layers for wind farms, offshore substations, and onshore substations
    create_point_feature_layer(npy_file_path_wf, workspace_folder, 'HS_WindFarms')
    create_point_feature_layer(npy_file_path_eh, workspace_folder, 'HS_EnergyHubs')
    create_point_feature_layer(npy_file_path_onss, workspace_folder, 'HS_OnshoreSubstations')
