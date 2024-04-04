import arcpy
import numpy as np

def calculate_distances_turbine_port():
    """Calculate distances between turbine points and nearest port points."""
    # Setup and obtain layers as previously described
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Initialize layers
    port_layer = turbine_layer = None

    # Fetch feature layers from the active map
    for layer in map.listLayers():
        if layer.isFeatureLayer:
            if "SelectedPorts" in layer.name and not port_layer:
                port_layer = layer
            elif layer.name.startswith('WTC') and not turbine_layer:
                turbine_layer = layer

    # Check if layers are found
    required_layers = [("SelectedPorts", port_layer), ("OSSC", turbine_layer)]
    for layer_name, layer_var in required_layers:
        if not layer_var:
            arcpy.AddError(f"No layer named '{layer_name}' found in the current map.")
            exit()

    for layer in (port_layer, turbine_layer):
        # Deselect all currently selected features in both layers
        arcpy.SelectLayerByAttribute_management(layer, "CLEAR_SELECTION")
        # Add a message for processing
        arcpy.AddMessage(f"Processing layer: {layer.name}")

    # Add fields if they don't exist in the turbine layer
    field_names = [field.name for field in arcpy.ListFields(turbine_layer)]
    if "PortName" not in field_names:
        arcpy.AddField_management(turbine_layer, "PortName", "TEXT")
    if "Distance" not in field_names:
        arcpy.AddField_management(turbine_layer, "Distance", "DOUBLE")

    # Get point coordinates for faster calculations
    turbine_points = np.array([(row[0].firstPoint.X, row[0].firstPoint.Y) for row in arcpy.da.SearchCursor(turbine_layer, "SHAPE@")])
    port_points = np.array([(row[0].firstPoint.X, row[0].firstPoint.Y) for row in arcpy.da.SearchCursor(port_layer, "SHAPE@")])

    # Compute distances using Euclidean distance formula
    distances = np.sqrt(np.sum((turbine_points[:, None] - port_points) ** 2, axis=2))

    # Find indices of closest ports for each turbine
    closest_port_indices = np.argmin(distances, axis=1)
    closest_port_names = [row[0] for row in arcpy.da.SearchCursor(port_layer, "PORT_NAME")]

    # Cursor to update turbine features
    with arcpy.da.UpdateCursor(turbine_layer, ["SHAPE@", "PortName", "Distance"]) as turbine_cursor:
        for i, turbine_row in enumerate(turbine_cursor):
            # Round function
            def rnd(r):
                return round(r / int(1e3), 3)
            
            closest_port_index = closest_port_indices[i]
            closest_port_name = closest_port_names[closest_port_index]

            # Get geometry objects for current turbine and closest port
            turbine_geom = turbine_row[0]
            port_geom = arcpy.da.SearchCursor(port_layer, "SHAPE@", where_clause=f"PORT_NAME = '{closest_port_name}'").next()[0]

            # Calculate distance between turbine and closest port
            closest_port_distance = turbine_geom.distanceTo(port_geom)

            # Update fields in turbine layer with closest port information
            turbine_row[1] = closest_port_name
            turbine_row[2] = rnd(closest_port_distance)
            turbine_cursor.updateRow(turbine_row)

if __name__ == "__main__":
    calculate_distances_turbine_port()
