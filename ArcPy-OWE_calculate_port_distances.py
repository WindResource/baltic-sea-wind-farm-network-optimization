import arcpy

def find_closest_port(wind_turbine_centroid, port_coords, port_names):
    """
    Find the closest port coordinate and name to a given wind turbine centroid.

    Parameters:
    - wind_turbine_centroid (tuple): Centroid coordinate of the wind turbine (x, y).
    - port_coords (list): List of port coordinates.
    - port_names (list): List of port names.

    Returns:
    - tuple: Coordinate of the closest port (x, y), and the name of the closest port.
    """
    distances = [arcpy.PointGeometry(wind_turbine_centroid).distanceTo(arcpy.PointGeometry(port_coord)) for port_coord in port_coords]
    min_index = distances.index(min(distances))
    closest_port_coord = port_coords[min_index]
    closest_port_name = port_names[min_index]
    return closest_port_coord, closest_port_name

def calculate_distance_and_port_name(wind_turbine_shapefile_path, port_shapefile_path):
    """
    Calculate the distance between wind turbine centroids and a single closest port coordinate.
    Also, add the PORT_NAME from the port shapefile to the wind turbine attribute table.

    Parameters:
    - wind_turbine_shapefile_path (str): Path to the shapefile containing wind turbine centroids.
    - port_shapefile_path (str): Path to the shapefile containing port coordinates.

    Returns:
    - dict: Dictionary mapping wind turbine IDs to a tuple containing distance and closest port name.
    """
    try:
        # Use SearchCursor to retrieve wind turbine centroids, port coordinates, and port names
        with arcpy.da.SearchCursor(wind_turbine_shapefile_path, ["SHAPE@XY", "TurbineID"]) as wind_turbine_cursor:
            wind_turbine_data = {row[1]: row[0] for row in wind_turbine_cursor}

        with arcpy.da.SearchCursor(port_shapefile_path, ["SHAPE@XY", "PORT_NAME"]) as port_cursor:
            port_coords = [row[0] for row in port_cursor]
            port_names = [row[1] for row in port_cursor]

        # Find the closest port to all wind turbine centroids (determined only once)
        closest_port_coord, closest_port_name = find_closest_port(list(wind_turbine_data.values())[0], port_coords, port_names)

        # Calculate the distance between each wind turbine centroid and the closest port
        distances_and_port_names_dict = {}
        for turbine_id, wind_turbine_centroid in wind_turbine_data.items():
            distance = arcpy.PointGeometry(wind_turbine_centroid).distanceTo(arcpy.PointGeometry(closest_port_coord))
            distances_and_port_names_dict[turbine_id] = (distance, closest_port_name)

        return distances_and_port_names_dict

    except arcpy.ExecuteError as e:
        arcpy.AddError(f"Failed to calculate distances and port names: {e}")
        return {}
    except Exception as e:
        arcpy.AddError(f"An unexpected error occurred: {e}")
        return {}
