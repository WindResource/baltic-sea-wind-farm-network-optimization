import arcpy

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
            if "SelectedPorts" in layer.name:
                port_layer = layer
            elif layer.name.startswith('OSSC'):  # Assuming substation layer names start with 'OSSC'
                substation_layer = layer

    # Check if necessary layers are found
    if not port_layer:
        raise ValueError("No port layer found in the map.")
    if not substation_layer:
        raise ValueError("No substation layer found in the map.")

    # Add fields if they don't exist in the substation layer
    field_names = [field.name for field in arcpy.ListFields(substation_layer)]
    if "PortName" not in field_names:
        arcpy.AddField_management(substation_layer, "PortName", "TEXT")
    if "Distance" not in field_names:
        arcpy.AddField_management(substation_layer, "Distance", "DOUBLE")

    # Cursor to iterate through substation features
    with arcpy.da.UpdateCursor(substation_layer, ["SHAPE@", "PortName", "Distance"]) as substation_cursor:
        for substation_row in substation_cursor:
            substation_geom, _, _ = substation_row
            min_distance = float('inf')  # Initialize minimum distance to a large value
            closest_port_name = ""
            closest_port_geom = None

            # Cursor to iterate through port layer for each substation feature
            with arcpy.da.SearchCursor(port_layer, ["PORT_NAME", "SHAPE@"]) as port_cursor:
                for port_row in port_cursor:
                    port_name, port_geom = port_row
                    distance = substation_geom.distanceTo(port_geom)
                    if distance < min_distance:
                        min_distance = distance
                        closest_port_name = port_name
                        closest_port_geom = port_geom
            
            # Update fields in substation layer with closest port information
            substation_row[1] = closest_port_name
            substation_row[2] = round(min_distance)
            substation_cursor.updateRow(substation_row)

if __name__ == "__main__":
    calculate_distances_oss_port()
