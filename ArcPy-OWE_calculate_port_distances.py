import arcpy

def find_closest_port_to_windfarms(windfarm_layer, port_layer):
    """Finds the closest port to each wind farm and returns a mapping of wind farm FID to port name and geometry."""
    windfarm_to_port_info = {}  # Dictionary to store port name and geometry for each wind farm

    # Iterate through each wind farm feature
    with arcpy.da.SearchCursor(windfarm_layer, ["OID@", "SHAPE@"]) as windfarm_cursor:
        for windfarm_row in windfarm_cursor:
            windfarm_fid, windfarm_geom = windfarm_row
            closest_port_name = None
            closest_port_distance = float('inf')
            closest_port_geometry = None

            # Perform spatial join for the current wind farm feature
            arcpy.analysis.SpatialJoin(windfarm_layer, port_layer, "in_memory/spatial_join_temp",
                                        "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "CLOSEST", "", windfarm_fid)
            
            # Iterate through the spatial join result to find the closest port
            with arcpy.da.SearchCursor("in_memory/spatial_join_temp", ["Port_Name", "NEAR_DIST", "SHAPE@"]) as join_cursor:
                for join_row in join_cursor:
                    port_name, distance, port_geometry = join_row
                    if distance < closest_port_distance:
                        closest_port_name = port_name
                        closest_port_distance = distance
                        closest_port_geometry = port_geometry
            
            # Store the closest port information for the current wind farm feature
            windfarm_to_port_info[windfarm_fid] = {"PortName": closest_port_name, "Distance": closest_port_distance, "PortGeometry": closest_port_geometry}

    # Display the dictionary using arcpy.AddMessage
    for windfarm_fid, port_info in windfarm_to_port_info.items():
        arcpy.AddMessage(f"Wind farm FID {windfarm_fid}: Closest port - {port_info['PortName']}, Distance - {port_info['Distance']}")

    return windfarm_to_port_info

def update_turbine_distances(turbine_layer, windfarm_to_port_info):
    """Updates turbines with the distance and name to their associated closest port."""
    # Check and add "PortName" and "Distance" fields if they don't exist
    field_names = [field.name for field in arcpy.ListFields(turbine_layer)]
    if "PortName" not in field_names:
        arcpy.AddField_management(turbine_layer, "PortName", "TEXT")
    if "Distance" not in field_names:
        arcpy.AddField_management(turbine_layer, "Distance", "DOUBLE")
    
    with arcpy.da.UpdateCursor(turbine_layer, ["FeatureFID", "PortName", "Distance", "SHAPE@"]) as cursor:
        for row in cursor:
            windfarm_fid = row[0]
            turbine_geom = row[3]
            if windfarm_fid in windfarm_to_port_info:
                port_info = windfarm_to_port_info[windfarm_fid]
                port_name = port_info["PortName"]
                port_geom = port_info["PortGeometry"]
                distance = turbine_geom.distanceTo(port_geom)
                row[1] = port_name
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
        windfarm_to_port_info = find_closest_port_to_windfarms(windfarm_layer, port_layer)
        
        # Update turbine distances
        update_turbine_distances(turbine_layer, windfarm_to_port_info)
    else:
        if not port_layer:
            arcpy.AddError("No port layer found in the map.")
        if not windfarm_layer:
            arcpy.AddError("No windfarm layer found in the map.")
        if not turbine_layer:
            arcpy.AddError("No turbine layer found in the map.")
