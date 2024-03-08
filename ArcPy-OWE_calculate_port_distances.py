import arcpy
import os
from typing import Tuple

def calculate_polygon_centroid(polygon_geometry):
    """Calculate the centroid of a polygon geometry."""
    if polygon_geometry.isMultipart:
        centroid = polygon_geometry.envelope.centroid
    else:
        centroid = polygon_geometry.centroid
    return centroid

def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """Calculate the distance between two point geometries."""
    return ((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)**0.5

def find_closest_port(port_file: str, windfarm: str) -> Tuple[str, float]:
    """Find the closest port to the windfarm and return its name and distance."""
    # Open the windfarm and port shapefiles
    windfarm_cursor = arcpy.da.SearchCursor(windfarm, ["SHAPE@"])
    port_cursor = arcpy.da.SearchCursor(port_file, ["SHAPE@", "PORT_NAME"])

    # Get the windfarm geometry (assuming there's only one feature)
    windfarm_row = next(windfarm_cursor, None)
    if not windfarm_row:
        arcpy.AddError("No windfarm features found.")
        quit()
    windfarm_geometry = windfarm_row[0]

    # Calculate the centroid of the windfarm
    windfarm_centroid = calculate_polygon_centroid(windfarm_geometry)

    # Initialize variables to store the closest port and distance
    closest_port = None
    closest_distance = float('inf')

    # Iterate through port features
    for port_row in port_cursor:
        port_geometry = port_row[0]
        port_name = port_row[1]

        # Check if port geometry is None
        if port_geometry is None:
            arcpy.AddWarning(f"Ignoring port {port_name} with null geometry.")
            continue

        # Calculate the distance between windfarm centroid and port geometry centroid
        distance = calculate_distance(
            (windfarm_centroid.X, windfarm_centroid.Y),
            (port_geometry.centroid.X, port_geometry.centroid.Y)
        )

        # Update the closest port if the current distance is smaller
        if distance < closest_distance:
            closest_distance = distance
            closest_port = port_name

        # Add a message for troubleshooting
        arcpy.AddMessage(f"Checking port: {port_name}")

    # Close the cursors
    del windfarm_cursor
    del port_cursor

    return closest_port, closest_distance

if __name__ == "__main__":
    # Get user input parameters using arcpy.GetParameterAsText()
    windfarm_folder: str = arcpy.GetParameterAsText(0)
    turbine_folder: str = arcpy.GetParameterAsText(1)
    port_folder: str = arcpy.GetParameterAsText(2)

    # Set the workspace to the folder containing port shapefiles
    arcpy.env.workspace = port_folder
    
    # Get the first shapefile in the folder containing port shapefiles
    port_path = arcpy.ListFiles("*.shp")
    if not port_path:
        arcpy.AddError("No port shapefiles found in the specified folder.")
        quit()
    
    port_path = os.path.join(port_folder, port_path[0])
    arcpy.AddMessage(f"Port shapefile: {port_path}")

    # Set the workspace to the folder containing windfarm shapefiles
    arcpy.env.workspace = windfarm_folder

    # Iterate through all windfarm shapefiles in the specified folder
    for windfarm_file in arcpy.ListFiles("*.shp"):
        windfarm_path = os.path.join(windfarm_folder, windfarm_file)

        arcpy.AddMessage(f"Processing windfarm shapefile: {windfarm_path}")

        # Find the closest port for each windfarm
        closest_port_name, closest_distance_value = find_closest_port(port_path, windfarm_path)

        # Print the result
        arcpy.AddMessage(f"Result for {os.path.basename(windfarm_path)}: Closest port is {closest_port_name}, distance is {closest_distance_value}")
