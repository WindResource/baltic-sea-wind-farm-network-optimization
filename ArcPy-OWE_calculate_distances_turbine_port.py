import arcpy
import numpy as np

def calculate_distances_turbine_port():
    """Calculates distances between turbines and closest ports."""
    # Fetch layers from the active map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap
    port_layer = windfarm_layer = turbine_layer = None

    for layer in map.listLayers():
        if layer.isFeatureLayer:
            if "SelectedPorts" in layer.name:
                port_layer = layer
            elif layer.name.startswith('WFA'):
                windfarm_layer = layer
            elif layer.name.startswith('WTC'):
                turbine_layer = layer

    # Check if required layers are found
    required_layers = [("SelectedPorts", port_layer), ("WFA", windfarm_layer), ("WTC", turbine_layer)]
    for layer_name, layer_var in required_layers:
        if not layer_var:
            arcpy.AddError(f"No layer named '{layer_name}' found in the current map.")
            exit()

    # Deselect all currently selected features in both layers and add processing message
    for layer in (port_layer, windfarm_layer, turbine_layer):
        arcpy.SelectLayerByAttribute_management(layer, "CLEAR_SELECTION")
        arcpy.AddMessage(f"Processing layer: {layer.name}")

    # Proceed if all layers are found
    if port_layer and windfarm_layer and turbine_layer:
        # Check and add "PortName" and "Distance" fields if they don't exist in turbine layer
        field_names = [field.name for field in arcpy.ListFields(turbine_layer)]
        if "PortName" not in field_names:
            arcpy.AddField_management(turbine_layer, "PortName", "TEXT")
        if "Distance" not in field_names:
            arcpy.AddField_management(turbine_layer, "Distance", "DOUBLE")
            
        # Get point coordinates for turbines and ports
        turbine_points = np.array([(row[0].firstPoint.X, row[0].firstPoint.Y) for row in arcpy.da.SearchCursor(turbine_layer, "SHAPE@")])
        port_points = np.array([(row[0].firstPoint.X, row[0].firstPoint.Y) for row in arcpy.da.SearchCursor(port_layer, "SHAPE@")])
        
        # Compute distances using Euclidean distance formula
        distances = np.sqrt(np.sum((turbine_points[:, None] - port_points) ** 2, axis=2))

        # Find indices of closest ports for each turbine
        closest_port_indices = np.argmin(distances, axis=1)
        closest_port_names = [row[0] for row in arcpy.da.SearchCursor(port_layer, "PORT_NAME")]

        # Dictionary to store port name and geometry for each wind farm
        windfarm_to_port_info = {}

        # Cursor to iterate through windfarm layer
        with arcpy.da.SearchCursor(windfarm_layer, ["OID@", "SHAPE@"]) as windfarm_cursor:
            for wf_row in windfarm_cursor:
                windfarm_fid, windfarm_geom = wf_row
                closest_port_index = closest_port_indices[windfarm_fid]
                closest_port_name = closest_port_names[closest_port_index]
                
                # Display closest port name
                arcpy.AddMessage(f"Closest port to wind farm FID {windfarm_fid}: {closest_port_name}")
                
                # Map the closest port name to the windfarm
                windfarm_to_port_info[windfarm_fid] = closest_port_name

                # Update turbine distances
                with arcpy.da.UpdateCursor(turbine_layer, ["FeatureFID", "PortName", "Distance", "SHAPE@"]) as cursor:
                    for row in cursor:
                        if row[0] == windfarm_fid:
                            row[1] = closest_port_name
                            row[2] = round(windfarm_geom.distanceTo(row[3]))
                            cursor.updateRow(row)
    else:
        if not port_layer:
            arcpy.AddError("No port layer found in the map.")
        if not windfarm_layer:
            arcpy.AddError("No windfarm layer found in the map.")
        if not turbine_layer:
            arcpy.AddError("No turbine layer found in the map.")

# Call the function
if __name__ == "__main__":
    calculate_distances_turbine_port()
