import arcpy
import os
from typing import Tuple

def calculate_distance(point1: arcpy.PointGeometry, point2: arcpy.PointGeometry) -> float:
    """Calculate the geodetic distance between two point geometries."""
    return point1.distanceTo(point2)

def update_turbine_attributes(turbine_layer: arcpy._mp.Layer, port_name: str, distance: float):
    """Update turbine attributes with PortName and Distance."""
    # Update attribute values for each turbine point
    with arcpy.da.UpdateCursor(turbine_layer, ["FeatureFID", "PortName", "Distance"]) as cursor:
        for row in cursor:
            # Update the PortName and Distance fields for turbines associated with the windfarm
            if row[0] == port_name:
                row[1] = port_name
                row[2] = distance
                cursor.updateRow(row)

def find_closest_port(port_layer: arcpy._mp.Layer, windfarm_layer: arcpy._mp.Layer) -> Tuple[str, float]:
    """Find the closest port to the windfarm and return its name and distance."""
    # Get the windfarm geometry (assuming there's only one feature)
    windfarm_geometry = None
    windfarm_id_field = None
    with arcpy.da.SearchCursor(windfarm_layer, ["SHAPE@", "FeatureFID"]) as cursor:
        for row in cursor:
            windfarm_geometry = row[0]
            windfarm_id_field = row[1]
            break

    if not windfarm_geometry or not windfarm_id_field:
        arcpy.AddError("No windfarm features found.")
        return None, None

    # Calculate the centroid of the windfarm
    windfarm_centroid = arcpy.PointGeometry(windfarm_geometry.centroid)

    # Initialize variables to store the closest port and distance
    closest_port_name = None
    closest_distance = float('inf')

    # Iterate through port features
    with arcpy.da.SearchCursor(port_layer, ["SHAPE@", "PORT_NAME"]) as cursor:
        for row in cursor:
            port_geometry = row[0]
            port_name = row[1]

            # Calculate the distance between windfarm centroid and port geometry centroid
            distance = calculate_distance(windfarm_centroid, arcpy.PointGeometry(port_geometry.centroid))

            # Update the closest port if the current distance is smaller
            if distance < closest_distance:
                closest_distance = distance
                closest_port_name = port_name

    return closest_port_name, closest_distance

if __name__ == "__main__":
    # Get the current project
    aprx = arcpy.mp.ArcGISProject("CURRENT")

    # Get the active map
    map = aprx.activeMap

    # Get the feature layers from the active map
    port_layer = None
    windfarm_layer = None
    turbine_layers = []
    for layer in map.listLayers():
        if layer.isFeatureLayer:
            if "SelectedPorts" in layer.name:
                port_layer = layer
            elif layer.name.startswith('WFA'):
                windfarm_layer = layer
            elif layer.name.startswith('WTC'):
                turbine_layers.append(layer)

    if not port_layer:
        arcpy.AddError("No port layer found in the map.")
    elif not windfarm_layer:
        arcpy.AddError("No windfarm layer found in the map.")
    elif not turbine_layers:
        arcpy.AddError("No turbine layers found in the map.")
    else:
        # Find the closest port for each windfarm
        closest_port_name, closest_distance = find_closest_port(port_layer, windfarm_layer)

        if closest_port_name:
            # Update turbine attributes with PortName and Distance
            for turbine_layer in turbine_layers:
                update_turbine_attributes(turbine_layer, closest_port_name, closest_distance)

            # Print the result
            arcpy.AddMessage(f"Closest port is {closest_port_name}")
