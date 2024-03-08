import arcpy
import os
from typing import Tuple

def calculate_polygon_centroid(polygon_geometry):
    """Calculate the centroid of a polygon geometry."""
    if polygon_geometry.isMultipart:
        centroid = arcpy.PointGeometry(polygon_geometry.envelope.centroid)
    else:
        centroid = arcpy.PointGeometry(polygon_geometry.centroid)
    return centroid

def calculate_distance(point1: arcpy.PointGeometry, point2: arcpy.PointGeometry) -> float:
    """Calculate the geodetic distance between two point geometries."""
    return point1.distanceTo(point2)

def update_turbine_attributes(turbine_file: str, port_name: str, distance: float):
    """Update turbine attributes with PortName and Distance."""
    # Add new fields if they don't exist
    for field in ["PortName", "Distance"]:
        if field not in [f.name for f in arcpy.ListFields(turbine_file)]:
            arcpy.AddField_management(turbine_file, field, "TEXT" if field == "PortName" else "DOUBLE")

    # Update attribute values for each turbine point
    with arcpy.da.UpdateCursor(turbine_file, ["SHAPE@", "PortName", "Distance"]) as cursor:
        for row in cursor:
            # Update the PortName and Distance fields for each turbine point
            row[1] = port_name
            row[2] = distance
            cursor.updateRow(row)

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
    if windfarm_geometry.isMultipart:
        windfarm_centroid = arcpy.PointGeometry(windfarm_geometry.envelope.centroid)
    else:
        windfarm_centroid = arcpy.PointGeometry(windfarm_geometry.centroid)

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
        distance = calculate_distance(windfarm_centroid, arcpy.PointGeometry(port_geometry.centroid))

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

    # Iterate through all windfarm shapefiles in the specified folder
    arcpy.env.workspace = windfarm_folder
    for windfarm_file in arcpy.ListFiles("*.shp"):
        windfarm_path = os.path.join(windfarm_folder, windfarm_file)

        arcpy.AddMessage(f"Processing windfarm shapefile: {windfarm_path}")

        # Find the closest port for each windfarm
        closest_port_name, closest_distance_value = find_closest_port(port_path, windfarm_path)

        # Set the workspace to the folder containing turbine shapefiles
        arcpy.env.workspace = turbine_folder

        # Update turbine attributes with PortName and Distance
        turbine_file = os.path.join(turbine_folder, windfarm_file.replace("WFA_", "WTC_"))
        update_turbine_attributes(turbine_file, closest_port_name, closest_distance_value)

        # Print the result
        arcpy.AddMessage(f"Result for {os.path.basename(windfarm_path)}: Closest port is {closest_port_name}, distance is {closest_distance_value}")
