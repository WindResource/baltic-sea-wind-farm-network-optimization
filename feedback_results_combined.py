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
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map_obj = aprx.activeMap

    # Check if the layer already exists in the map
    if any(layer.name == layer_name for layer in map_obj.listLayers()):
        print(f'Layer {layer_name} already exists in the map. Skipping creation.')
        return

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
    map_obj.addDataFromPath(lines_path)

    print(f'Feature layer {layer_name} added successfully to the current map.')

def create_point_feature_layer(npy_file_path, workspace_folder, layer_name, include_rate=False):
    """
    Creates a point feature layer from .npy data and adds it to the current project map.

    Parameters:
    - npy_file_path: The path to the .npy file containing point data.
    - workspace_folder: The path to the workspace folder where the feature class will be stored.
    - layer_name: The name of the layer to be created in the current map.
    - include_rate: Boolean indicating whether to include the 'Rate' field.
    """
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map_obj = aprx.activeMap

    # Check if the layer already exists in the map
    if any(layer.name == layer_name for layer in map_obj.listLayers()):
        print(f'Layer {layer_name} already exists in the map. Skipping creation.')
        return

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

    if include_rate:
        fields.append(['Rate', 'DOUBLE'])
    
    # Add fields with retry logic
    add_fields_with_retry(points_path, fields)

    # Insert the points into the feature class
    field_names = ['SHAPE@', 'ID', 'ISO', 'Capacity', 'Cost']
    if include_rate:
        field_names.append('Rate')

    with arcpy.da.InsertCursor(points_path, field_names) as insert_cursor:
        for row in point_data:
            point = arcpy.Point(float(row['lon']), float(row['lat']))
            id = int(row['id'])
            iso = str(row['iso'])
            capacity = float(row['capacity'])
            cost = float(row['cost'])
            if include_rate:
                rate = float(row['rate'])
                insert_cursor.insertRow((point, id, iso, capacity, cost, rate))
            else:
                insert_cursor.insertRow((point, id, iso, capacity, cost))

    # Add the feature class to the current map
    map_obj.addDataFromPath(points_path)

    print(f'Feature layer {layer_name} added successfully to the current map.')

def create_polygon_feature_layer_from_points(wfa_layer, wf_layer, workspace_folder, layer_name):
    """
    Creates a new polygon feature layer from WFA polygons containing WF points within them.

    Parameters:
    - wfa_layer: The WFA polygon layer.
    - wf_layer: The WF point layer.
    - workspace_folder: The path to the workspace folder where the feature class will be stored.
    - layer_name: The name of the new polygon layer to be created.
    """
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map_obj = aprx.activeMap

    # Check if the layer already exists in the map
    if any(layer.name == layer_name for layer in map_obj.listLayers()):
        print(f'Layer {layer_name} already exists in the map. Skipping creation.')
        return

    # Path for the new feature class
    polygons_path = os.path.join(workspace_folder, f"{layer_name}.shp")
    if arcpy.Exists(polygons_path):
        arcpy.Delete_management(polygons_path)
    arcpy.management.CreateFeatureclass(workspace_folder, layer_name, 'POLYGON', spatial_reference=4326)
    
    # Copy WFA polygons to the new feature class
    arcpy.management.CopyFeatures(wfa_layer, polygons_path)
    
    # Get the OID field name
    oid_field = arcpy.Describe(polygons_path).OIDFieldName
    
    # Find WFA polygons that contain WF points
    with arcpy.da.UpdateCursor(polygons_path, ['SHAPE@', oid_field]) as cursor:
        for row in cursor:
            polygon = row[0]
            # Create a temporary layer for the points within the current polygon
            arcpy.management.MakeFeatureLayer(wf_layer, "temp_wf_layer")
            arcpy.management.SelectLayerByLocation("temp_wf_layer", "WITHIN", polygon)
            # If no points are found within the polygon, delete the polygon
            if int(arcpy.management.GetCount("temp_wf_layer").getOutput(0)) == 0:
                cursor.deleteRow()
            arcpy.management.Delete("temp_wf_layer")

    # Add the new feature class to the current map
    map_obj.addDataFromPath(polygons_path)

    print(f'Feature layer {layer_name} created successfully with polygons containing WF points.')

def process_feature_layers(npy_file_paths, feature_layer_folder):
    """
    Processes and adds all .npy files in the given folder as feature layers.

    Parameters:
    - npy_file_paths: List of paths to .npy files.
    - feature_layer_folder: The base folder where feature layers will be saved.
    """
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map_obj = aprx.activeMap

    for file_path in npy_file_paths:
        file_name = os.path.basename(file_path).split('.')[0]
        # Determine if the file should be processed as point or polyline based on its name
        if 'wf' in file_name:
            create_point_feature_layer(file_path, feature_layer_folder, file_name, include_rate=True)
        elif any(identifier in file_name for identifier in ['eh', 'onss']):
            create_point_feature_layer(file_path, feature_layer_folder, file_name)
        elif any(identifier in file_name for identifier in ['ec1', 'ec2', 'ec3', 'onc']):
            create_polyline_feature_layer(file_path, feature_layer_folder, file_name)

    # Additional processing for creating WFA polygon layer
    
    # Get the first layer in the map that starts with 'WFA'
    wfa_layer = next((layer for layer in map_obj.listLayers() if layer.name.startswith('WFA')), None)
    if wfa_layer is None:
        arcpy.AddError("No layer starting with 'WFA' found in the current map.")
        return
    
    # Process each WF layer and create corresponding WFA layer
    wf_layers = [layer for layer in map_obj.listLayers() if 'wf_' in layer.name.lower()]
    for wf_layer in wf_layers:
        new_layer_name = wf_layer.name.replace('wf', 'wfa')
        create_polygon_feature_layer_from_points(wfa_layer, wf_layer, feature_layer_folder, new_layer_name)

if __name__ == "__main__":
    # Define the paths to the workspace and folders
    workspace_folder = f"C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\datasets\\results\\combined\\MF-C-I"
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