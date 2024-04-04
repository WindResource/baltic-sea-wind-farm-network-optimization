import arcpy

import arcpy
import numpy as np

def calculate_distances_oss_port():
    """Performs calculation to identify the closest port for each offshore substation within the specified search radius."""
    # Setup and obtain layers as previously described
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Initialize layers
    port_layer = substation_layer = None

    # Fetch feature layers from the active map
    for layer in map.listLayers():
        if layer.isFeatureLayer:
            if "SelectedPorts" in layer.name and not port_layer:
                port_layer = layer
            elif layer.name.startswith('OSSC') and not substation_layer:
                substation_layer = layer

    # Check if layers are found
    if not port_layer:
        arcpy.AddError("No layer named 'SelectedPorts' found in the current map.")
        exit()

    if not substation_layer:
        arcpy.AddError("No layer starting with 'OSSC' found in the current map.")
        exit()

    for layer in (port_layer, substation_layer):
        # Deselect all currently selected features in both layers
        arcpy.SelectLayerByAttribute_management(layer, "CLEAR_SELECTION")
        # Add a message for processing
        arcpy.AddMessage(f"Processing layer: {layer.name}")

    # Add fields if they don't exist in the substation layer
    field_names = [field.name for field in arcpy.ListFields(substation_layer)]
    if "PortName" not in field_names:
        arcpy.AddField_management(substation_layer, "PortName", "TEXT")
    if "Distance" not in field_names:
        arcpy.AddField_management(substation_layer, "Distance", "DOUBLE")

    # Get geometry arrays for faster calculations
    substation_geoms = np.array([(row[0].centroid.X, row[0].centroid.Y) for row in arcpy.da.SearchCursor(substation_layer, "SHAPE@")])
    port_geoms = np.array([(row[0].centroid.X, row[0].centroid.Y) for row in arcpy.da.SearchCursor(port_layer, "SHAPE@")])

    # Calculate distances using numpy
    distances = np.sqrt(np.sum((substation_geoms[:, None] - port_geoms) ** 2, axis=2))
    closest_port_indices = np.argmin(distances, axis=1)
    closest_port_names = [row[0] for row in arcpy.da.SearchCursor(port_layer, "PORT_NAME")]

    # Cursor to update substation features
    with arcpy.da.UpdateCursor(substation_layer, ["SHAPE@", "PortName", "Distance"]) as substation_cursor:
        for i, substation_row in enumerate(substation_cursor):
            closest_port_index = closest_port_indices[i]
            closest_port_distance = distances[i, closest_port_index]
            closest_port_name = closest_port_names[closest_port_index]

            # Update fields in substation layer with closest port information
            substation_row[1] = closest_port_name
            substation_row[2] = closest_port_distance
            substation_cursor.updateRow(substation_row)

if __name__ == "__main__":
    calculate_distances_oss_port()