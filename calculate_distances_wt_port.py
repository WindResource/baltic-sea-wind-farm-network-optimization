import arcpy
import numpy as np
from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    r = 6371 * 1e3 # Radius of Earth in meters
    distance = r * c

    return distance

def calculate_distances_oss_port():
    """Calculate distances between turbine points and nearest port points within Baltic Sea countries."""
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
    required_layers = [("SelectedPorts", port_layer), ("WTC", turbine_layer)]
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
    
    # Define the list of Baltic Sea country codes
    baltic_sea_countries = ["DK", "EE", "FI", "DE", "LV", "LT", "PL", "SE"]

    for country_code in baltic_sea_countries:
        # Select turbine features with the current country code
        arcpy.SelectLayerByAttribute_management(turbine_layer, "NEW_SELECTION", f"ISO = '{country_code}'")
        
        # Select port features with the current country code
        arcpy.SelectLayerByAttribute_management(port_layer, "NEW_SELECTION", f"COUNTRY = '{country_code}'")
        
        # Get selected turbine and port points
        turbine_points = np.array([(row[0].firstPoint.Y, row[0].firstPoint.X) for row in arcpy.da.SearchCursor(turbine_layer, "SHAPE@")])
        port_points = np.array([(row[0].firstPoint.Y, row[0].firstPoint.X) for row in arcpy.da.SearchCursor(port_layer, "SHAPE@")])
        
        # Initialize distances array
        distances = np.zeros((len(turbine_points), len(port_points)))
        
        # Continue with the distance calculation and updating as before
        # Compute distances using Haversine formula
        for i, turbine_point in enumerate(turbine_points):
            for j, port_point in enumerate(port_points):
                distances[i, j] = haversine(turbine_point[0], turbine_point[1], port_point[0], port_point[1])

        # Find indices of closest ports for each turbine
        closest_port_indices = np.argmin(distances, axis=1)
        closest_port_names = [row[0] for row in arcpy.da.SearchCursor(port_layer, "PORT_NAME")]

        # Cursor to update turbine features
        with arcpy.da.UpdateCursor(turbine_layer, ["SHAPE@", "PortName", "Distance"]) as turbine_cursor:
            for i, turbine_row in enumerate(turbine_cursor):
                closest_port_index = closest_port_indices[i]
                closest_port_distance = distances[i, closest_port_index]
                closest_port_name = closest_port_names[closest_port_index]

                # Update fields in turbine layer with closest port information
                turbine_row[1] = closest_port_name.lower().capitalize()
                turbine_row[2] = round(closest_port_distance)
                turbine_cursor.updateRow(turbine_row)

if __name__ == "__main__":
    calculate_distances_oss_port()