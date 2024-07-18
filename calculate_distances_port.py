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
    r = 6371 * 1e3  # Radius of Earth in meters
    distance = r * c  

    return distance

def calculate_distances_oss_port():
    """Calculate distances between substation points and nearest port points within Baltic Sea countries."""
    # Setup and obtain layers as previously described
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Initialize layers
    port_layer = None
    substation_layers = []
    wtc_layers = []

    # Fetch feature layers from the active map
    for layer in map.listLayers():
        if layer.isFeatureLayer:
            if "Port" in layer.name and not port_layer:
                port_layer = layer
            elif layer.name.startswith('OSSC') or layer.name.startswith('EHC'):
                substation_layers.append(layer)
            elif layer.name.startswith('WTC'):
                wtc_layers.append(layer)

    # Check if layers are found
    if not port_layer:
        arcpy.AddError("No layer named 'SelectedPorts' found in the current map.")
        exit()
    if not substation_layers and not wtc_layers:
        arcpy.AddError("No layers starting with 'OSSC', 'EHC', or 'WTC' found in the current map.")
        exit()

    # Function to process layers with specified hierarchy
    def process_layers(layers, hierarchy):
        for layer in layers:
            # Deselect all currently selected features in the substation layers
            arcpy.SelectLayerByAttribute_management(layer, "CLEAR_SELECTION")
            # Add a message for processing
            arcpy.AddMessage(f"Processing layer: {layer.name}")

            # Add fields if they don't exist in the substation layer
            field_names = [field.name for field in arcpy.ListFields(layer)]
            if "PortName" not in field_names:
                arcpy.AddField_management(layer, "PortName", "TEXT")
            if "Distance" not in field_names:
                arcpy.AddField_management(layer, "Distance", "DOUBLE")
            if "HarborSize" not in field_names:
                arcpy.AddField_management(layer, "HarborSize", "TEXT")
            
            # Define the list of Baltic Sea country codes
            baltic_sea_countries = ["DK", "EE", "FI", "DE", "LV", "LT", "PL", "SE"]

            for country_code in baltic_sea_countries:
                # Select substation features with the current country code
                arcpy.SelectLayerByAttribute_management(layer, "NEW_SELECTION", f"ISO = '{country_code}'")
                
                for size_selection in hierarchy:
                    arcpy.SelectLayerByAttribute_management(port_layer, "NEW_SELECTION", f"COUNTRY = '{country_code}' AND HARBORSIZE IN ({size_selection})")
                    
                    # Check if any ports were selected
                    if int(arcpy.GetCount_management(port_layer).getOutput(0)) > 0:
                        break

                # Get selected substation and port points
                substation_points = np.array([(row[0].firstPoint.Y, row[0].firstPoint.X) for row in arcpy.da.SearchCursor(layer, "SHAPE@")])
                port_data = [(row[0].firstPoint.Y, row[0].firstPoint.X, row[1], row[2]) for row in arcpy.da.SearchCursor(port_layer, ["SHAPE@", "PORT_NAME", "HARBORSIZE"])]
                
                # Initialize distances array
                distances = np.zeros((len(substation_points), len(port_data)))
                
                # Compute distances using Haversine formula
                for i, substation_point in enumerate(substation_points):
                    for j, port_point in enumerate(port_data):
                        distances[i, j] = haversine(substation_point[0], substation_point[1], port_point[0], port_point[1])

                # Find indices of closest ports for each substation
                closest_port_indices = np.argmin(distances, axis=1)

                # Cursor to update substation features
                with arcpy.da.UpdateCursor(layer, ["SHAPE@", "PortName", "Distance", "HarborSize"]) as substation_cursor:
                    for i, substation_row in enumerate(substation_cursor):
                        closest_port_index = closest_port_indices[i]
                        closest_port_distance = distances[i, closest_port_index]
                        closest_port_name = port_data[closest_port_index][2]
                        closest_port_harborsize = port_data[closest_port_index][3]

                        # Update fields in substation layer with closest port information
                        substation_row[1] = closest_port_name.lower().capitalize()
                        substation_row[2] = round(closest_port_distance)
                        substation_row[3] = closest_port_harborsize.lower().capitalize()
                        substation_cursor.updateRow(substation_row)

            # Clear the selection for the current substation layer
            arcpy.SelectLayerByAttribute_management(layer, "CLEAR_SELECTION")
    
    # Process OSSC and EHC layers with hierarchy for OSSC and EHC
    ossc_ehc_hierarchy = [
        "'L', 'M'",  # Group 1: L and M
        "'S', 'M', 'L'",  # Group 2: S, M, L
        "'V', 'S', 'M', 'L'"  # Group 3: V, S, M, L
    ]
    process_layers(substation_layers, ossc_ehc_hierarchy)

    # Process WTC layers with hierarchy for WTC
    wtc_hierarchy = [
        "'S', 'M', 'L'",  # Group 1: S, M, L
        "'V', 'S', 'M', 'L'"  # Group 2: V, S, M, L
    ]
    process_layers(wtc_layers, wtc_hierarchy)
    
    # Clear the selection for the port layer
    arcpy.SelectLayerByAttribute_management(port_layer, "CLEAR_SELECTION")

if __name__ == "__main__":
    calculate_distances_oss_port()
