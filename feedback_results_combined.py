import arcpy
import numpy as np
import os
import time

def add_fields_with_retry(feature_class, fields, wait_time=0.5):
    """
    Adds fields to a feature class with a retry mechanism in case of failure.

    Parameters:
    - feature_class: The feature class to which fields will be added.
    - fields: The fields to be added.
    - wait_time: Time to wait between retries in seconds.
    """
    existing_fields = [f.name for f in arcpy.ListFields(feature_class)]
    fields_to_add = [field for field in fields if field[0] not in existing_fields]
    
    if not fields_to_add:
        arcpy.AddMessage(f"All fields already exist in {feature_class}. Skipping field addition.")
        return

    while True:
        try:
            arcpy.management.AddFields(feature_class, fields_to_add)
            # Check if fields are added
            existing_fields = [f.name for f in arcpy.ListFields(feature_class)]
            if all(field[0] in existing_fields for field in fields_to_add):
                return
        except Exception as e:
            arcpy.AddMessage(f"Error adding fields: {e}")
        time.sleep(wait_time)

def insert_rows_with_retry(insert_cursor, rows, wait_time=0.5):
    """
    Inserts rows into a feature class with a retry mechanism in case of failure.

    Parameters:
    - insert_cursor: The insert cursor for the feature class.
    - rows: The rows to be inserted.
    - wait_time: Time to wait between retries in seconds.
    """
    while True:
        try:
            for row in rows:
                insert_cursor.insertRow(row)
            return
        except Exception as e:
            arcpy.AddMessage(f"Error inserting rows: {e}")
        time.sleep(wait_time)

def create_polyline_feature_layer(npy_file_path, workspace_folder, layer_name, results_folder):
    """
    Creates a polyline feature layer from .npy data and adds it to the current project map.

    Parameters:
    - npy_file_path: The path to the .npy file containing cable data.
    - workspace_folder: The path to the workspace folder where the feature class will be stored.
    - layer_name: The name of the layer to be created in the current map.
    - results_folder: The name of the results folder to append to the layer name.
    """
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map_obj = aprx.activeMap
    layer_name = f"{layer_name}_{results_folder}"

    # Check if the layer already exists in the map
    if any(layer.name == layer_name for layer in map_obj.listLayers()):
        arcpy.AddMessage(f'Layer {layer_name} already exists in the map. Skipping creation.')
        return

    # Load the cable data from the .npy file
    cable_data = np.load(npy_file_path, allow_pickle=True)
    
    # Skip if the data is empty
    if len(cable_data) == 0:
        arcpy.AddMessage(f"No data in {npy_file_path}. Skipping creation of {layer_name}.")
        return

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

    # Prepare rows for insertion
    rows = []
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
        rows.append(row_data + [polyline])

    # Insert the polylines into the feature class with retry logic
    with arcpy.da.InsertCursor(lines_path, [field[0] for field in fields] + ['SHAPE@']) as insert_cursor:
        insert_rows_with_retry(insert_cursor, rows)

    # Add the feature class to the current map
    map_obj.addDataFromPath(lines_path)

    arcpy.AddMessage(f'Feature layer {layer_name} added successfully to the current map.')

def create_point_feature_layer(npy_file_path, workspace_folder, layer_name, results_folder, include_rate=False):
    """
    Creates a point feature layer from .npy data and adds it to the current project map.

    Parameters:
    - npy_file_path: The path to the .npy file containing point data.
    - workspace_folder: The path to the workspace folder where the feature class will be stored.
    - layer_name: The name of the layer to be created in the current map.
    - results_folder: The name of the results folder to append to the layer name.
    - include_rate: Boolean indicating whether to include the 'Rate' field.
    """
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map_obj = aprx.activeMap
    layer_name = f"{layer_name}_{results_folder}"

    # Check if the layer already exists in the map
    if any(layer.name == layer_name for layer in map_obj.listLayers()):
        arcpy.AddMessage(f'Layer {layer_name} already exists in the map. Skipping creation.')
        return

    # Load the point data from the .npy file
    point_data = np.load(npy_file_path, allow_pickle=True)
    
    # Skip if the data is empty
    if len(point_data) == 0:
        arcpy.AddMessage(f"No data in {npy_file_path}. Skipping creation of {layer_name}.")
        return
    
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

    # Prepare rows for insertion
    rows = []
    for row in point_data:
        point = arcpy.Point(float(row['lon']), float(row['lat']))
        id = int(row['id'])
        iso = str(row['iso'])
        capacity = float(row['capacity'])
        cost = float(row['cost'])
        if include_rate:
            rate = float(row['rate'])
            rows.append((point, id, iso, capacity, cost, rate))
        else:
            rows.append((point, id, iso, capacity, cost))

    # Insert the points into the feature class with retry logic
    field_names = ['SHAPE@', 'ID', 'ISO', 'Capacity', 'Cost']
    if include_rate:
        field_names.append('Rate')

    with arcpy.da.InsertCursor(points_path, field_names) as insert_cursor:
        insert_rows_with_retry(insert_cursor, rows)

    # Add the feature class to the current map
    map_obj.addDataFromPath(points_path)

    arcpy.AddMessage(f'Feature layer {layer_name} added successfully to the current map.')

def create_polygon_feature_layer_from_points(wfa_layer, wf_layer, workspace_folder, layer_name, results_folder):
    """
    Creates a new polygon feature layer from WFA polygons containing WF points within them.

    Parameters:
    - wfa_layer: The WFA polygon layer.
    - wf_layer: The WF point layer.
    - workspace_folder: The path to the workspace folder where the feature class will be stored.
    - layer_name: The name of the new polygon layer to be created.
    - results_folder: The name of the results folder to append to the layer name.
    """
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map_obj = aprx.activeMap
    layer_name = f"{layer_name}_{results_folder}"

    # Check if the layer already exists in the map
    if any(layer.name == layer_name for layer in map_obj.listLayers()):
        arcpy.AddMessage(f'Layer {layer_name} already exists in the map. Skipping creation.')
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

    arcpy.AddMessage(f'Feature layer {layer_name} created successfully with polygons containing WF points.')

def process_feature_layers(npy_file_paths, feature_layer_dir, results_folder):
    """
    Processes and adds all .npy files in the given folder as feature layers.

    Parameters:
    - npy_file_paths: List of paths to .npy files.
    - feature_layer_dir: The base folder where feature layers will be saved.
    - results_folder: The name of the results folder to append to the layer name.
    """
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map_obj = aprx.activeMap

    # Get the names of existing layers in the map
    existing_layer_names = [layer.name for layer in map_obj.listLayers()]

    # List to track added WF layers
    added_wf_layers = []

    for file_path in npy_file_paths:
        file_name = os.path.basename(file_path).split('.')[0]
        # Check if the layer already exists in the map
        layer_name = f"{file_name}_{results_folder}"
        if layer_name in existing_layer_names:
            arcpy.AddMessage(f'Layer {layer_name} already exists in the map. Skipping creation.')
            continue

        # Determine if the file should be processed as point or polyline based on its name
        if 'wf' in file_name:
            create_point_feature_layer(file_path, feature_layer_dir, file_name, results_folder, include_rate=True)
            added_wf_layers.append(layer_name)
        elif any(identifier in file_name for identifier in ['eh', 'onss']):
            create_point_feature_layer(file_path, feature_layer_dir, file_name, results_folder)
        elif any(identifier in file_name for identifier in ['ec1', 'ec2', 'ec3', 'onc']):
            create_polyline_feature_layer(file_path, feature_layer_dir, file_name, results_folder)

    # Additional processing for creating WFA polygon layer
    
    # Get the first layer in the map that starts with 'WFA'
    wfa_layer = next((layer for layer in map_obj.listLayers() if layer.name.startswith('WFA')), None)
    if wfa_layer is None:
        arcpy.AddError("No layer starting with 'WFA' found in the current map.")
        return
    
    # Process each WF layer and create corresponding WFA layer
    for wf_layer_name in added_wf_layers:
        wf_layer = next((layer for layer in map_obj.listLayers() if layer.name == wf_layer_name), None)
        if wf_layer:
            new_layer_name = wf_layer_name.replace('wf', 'wfa')
            create_polygon_feature_layer_from_points(wfa_layer, wf_layer, feature_layer_dir, new_layer_name, results_folder)

if __name__ == "__main__":
    # Define the paths to the workspace and folders
    workspace_dir = f"C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\datasets\\results\\combined"
    
    results_folder = 'MF-D-I-DE2200'
    results_dir = os.path.join(workspace_dir, results_folder)

    # Define the feature_layer_dir
    feature_layer_dir = os.path.join(results_dir, 'features')

    # List all .npy files in the results folder
    npy_file_paths = [os.path.join(results_dir, f) for f in os.listdir(results_dir) if f.endswith('.npy')]
    
    # Process the files if any are found
    if npy_file_paths:
        if not os.path.exists(feature_layer_dir):
            os.makedirs(feature_layer_dir)
        process_feature_layers(npy_file_paths, feature_layer_dir, results_folder)
    else:
        arcpy.AddMessage("No .npy files found in the results folder.")