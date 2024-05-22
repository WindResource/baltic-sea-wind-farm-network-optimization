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

if __name__ == "__main__":
    # Example usage
    workspace_folder = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\datasets"
    npy_file_path_ec1 = os.path.join(workspace_folder, 'results', 'hubspoke', 'ec1_ids_hs.npy')
    npy_file_path_ec2 = os.path.join(workspace_folder, 'results', 'hubspoke', 'ec2_ids_hs.npy')

    # Generate feature layer for export cables 1
    create_export_cable_feature_layer(npy_file_path_ec1, workspace_folder, 'ExportCables1')

    # Generate feature layer for export cables 2
    create_export_cable_feature_layer(npy_file_path_ec2, workspace_folder, 'ExportCables2')
