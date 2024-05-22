import arcpy
import numpy as np
import os

def create_export_cable_feature_layer(npy_file_path, layer_name):
    """
    Create a feature layer with polylines connecting the coordinates of the export cables using the Coordinate Table To 2-Point Line tool
    and add it to the current project map.
    
    Parameters:
    - npy_file_path: The path to the .npy file containing export cable data.
    - layer_name: The name of the layer to be created in the current map.
    """
    # Load the export cable data from the .npy file
    ec_data = np.load(npy_file_path)
    
    # Create an in-memory table
    table = arcpy.management.CreateTable("in_memory", f"{layer_name}_table")

    # Add necessary fields
    arcpy.management.AddField(table, 'EC_ID', 'LONG')
    arcpy.management.AddField(table, 'Component_ID', 'LONG')
    arcpy.management.AddField(table, 'Longitude', 'DOUBLE')
    arcpy.management.AddField(table, 'Latitude', 'DOUBLE')
    arcpy.management.AddField(table, 'Capacity', 'DOUBLE')
    arcpy.management.AddField(table, 'Cost', 'DOUBLE')

    # Insert rows into the table
    with arcpy.da.InsertCursor(table, ['EC_ID', 'Component_ID', 'Longitude', 'Latitude', 'Capacity', 'Cost']) as cursor:
        for row in ec_data:
            cursor.insertRow((row['ec_id'], row['component_id'], row['lon'], row['lat'], row['capacity'], row['cost']))

    # Create the points from the table
    points = arcpy.management.XYTableToPoint(table, 'in_memory/points', 'Longitude', 'Latitude')

    # Create an in-memory feature class to store the polylines
    lines = arcpy.management.CreateFeatureclass('in_memory', layer_name, 'POLYLINE', spatial_reference=4326)
    arcpy.management.AddField(lines, 'EC_ID', 'LONG')
    arcpy.management.AddField(lines, 'Capacity', 'DOUBLE')
    arcpy.management.AddField(lines, 'Cost', 'DOUBLE')

    # Create polylines by connecting points with the same EC_ID
    with arcpy.da.SearchCursor(points, ['EC_ID', 'SHAPE@XY', 'Capacity', 'Cost']) as search_cursor:
        with arcpy.da.InsertCursor(lines, ['EC_ID', 'SHAPE@', 'Capacity', 'Cost']) as insert_cursor:
            points_dict = {}
            for ec_id, point, capacity, cost in search_cursor:
                if ec_id not in points_dict:
                    points_dict[ec_id] = []
                points_dict[ec_id].append((point, capacity, cost))
            for ec_id, points in points_dict.items():
                if len(points) == 2:
                    array = arcpy.Array([arcpy.Point(*points[0][0]), arcpy.Point(*points[1][0])])
                    polyline = arcpy.Polyline(array)
                    insert_cursor.insertRow((ec_id, polyline, points[0][1], points[0][2]))

    # Add the feature class to the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap
    map.addDataFromPath(lines)

    print(f'Feature layer {layer_name} added successfully to the current map.')

if __name__ == "__main__":
    # Example usage
    workspace_folder = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\datasets"
    npy_file_path_ec1 = os.path.join(workspace_folder, 'results', 'hubspoke', 'ec1_ids_hs.npy')
    npy_file_path_ec2 = os.path.join(workspace_folder, 'results', 'hubspoke', 'ec2_ids_hs.npy')

    # Generate feature layer for export cables 1
    create_export_cable_feature_layer(npy_file_path_ec1, 'ExportCables1')

    # Generate feature layer for export cables 2
    create_export_cable_feature_layer(npy_file_path_ec2, 'ExportCables2')
