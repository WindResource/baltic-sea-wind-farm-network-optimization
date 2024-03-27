import arcpy

def find_closest_port_to_windfarms(windfarm_layer, port_layer):
    """Manually finds the closest port to each wind farm and returns a mapping of windfarm FID to port geometry."""
    # Dictionary to store the closest port geometry for each windfarm
    windfarm_to_port_geom = {}

    # Cursors to iterate through windfarm and port layers
    with arcpy.da.SearchCursor(windfarm_layer, ["OID@", "SHAPE@"]) as windfarm_cursor, \
        arcpy.da.SearchCursor(port_layer, ["OID@", "SHAPE@"]) as port_cursor:
        
        # Convert port_cursor to a list to reuse it for each windfarm
        ports = list(port_cursor)

        for wf_row in windfarm_cursor:
            windfarm_fid, windfarm_geom = wf_row
            closest_port_geom = None
            min_distance = float('inf')

            for p_row in ports:
                port_geom = p_row[1]
                distance = windfarm_geom.distanceTo(port_geom)
                if distance < min_distance:
                    min_distance = distance
                    closest_port_geom = port_geom
            
            # Map the closest port geometry to the windfarm
            windfarm_to_port_geom[windfarm_fid] = closest_port_geom

    return windfarm_to_port_geom

def update_turbine_distances(turbine_layer, windfarm_to_port_geom):
    """Updates turbines with the distance to their associated closest port."""
    with arcpy.da.UpdateCursor(turbine_layer, ["FeatureFID", "PortName", "Distance", "SHAPE@"]) as cursor:
        for row in cursor:
            windfarm_fid = row[0]
            turbine_geom = row[3]
            if windfarm_fid in windfarm_to_port_geom:
                port_geom = windfarm_to_port_geom[windfarm_fid]
                distance = turbine_geom.distanceTo(port_geom)
                # Update with actual port name and distance
                row[1] = "Closest Port"  # Placeholder, adjust as needed
                row[2] = distance
                cursor.updateRow(row)

if __name__ == "__main__":
    # Setup and obtain layers as previously described
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Initialize layers
    port_layer = windfarm_layer = turbine_layer = None

    # Fetch feature layers from the active map
    for layer in map.listLayers():
        if layer.isFeatureLayer:
            if "SelectedPorts" in layer.name:
                port_layer = layer
            elif layer.name.startswith('WFA'):
                windfarm_layer = layer
            elif layer.name.startswith('WTC'):
                turbine_layer = layer
                
    # Proceed if all layers are found
    if port_layer and windfarm_layer and turbine_layer:
        # Identify closest ports for each wind farm
        windfarm_to_port_geom = find_closest_port_to_windfarms(windfarm_layer, port_layer)
        
        # Update turbine distances
        update_turbine_distances(turbine_layer, windfarm_to_port_geom)
    else:
        if not port_layer:
            arcpy.AddError("No port layer found in the map.")
        if not windfarm_layer:
            arcpy.AddError("No windfarm layer found in the map.")
        if not turbine_layer:
            arcpy.AddError("No turbine layer found in the map.")
