import numpy as np
import os

def haversine_distance_np(lon1, lat1, lon2, lat2):
    """
    Calculate the Haversine distance between two sets of coordinates.

    Parameters:
        lon1 (numpy.ndarray): Longitudes of the first set of coordinates.
        lat1 (numpy.ndarray): Latitudes of the first set of coordinates.
        lon2 (numpy.ndarray): Longitudes of the second set of coordinates.
        lat2 (numpy.ndarray): Latitudes of the second set of coordinates.

    Returns:
        numpy.ndarray: Array of Haversine distances.
    """
    # Convert latitude and longitude from degrees to radians
    lon1, lat1, lon2, lat2 = np.radians(lon1), np.radians(lat1), np.radians(lon2), np.radians(lat2)

    # Calculate differences in coordinates
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    # Apply Haversine formula
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))

    # Radius of the Earth in kilometers
    r = 6371.0

    # Calculate the distance
    distances = c * r

    return distances


def calculate_distances(output_folder: str):
    """
    Calculate the Haversine distances between OSS and OnSS datasets within 300 km.

    Parameters:
        output_folder (str): The folder path where the OSS and OnSS datasets and the results will be saved.
    """
    # OSS and OnSS file names
    oss_filename = "oss_data.npy"
    onss_filename = "onss_data.npy"

    # Construct full file paths
    oss_file = os.path.join(output_folder, oss_filename)
    onss_file = os.path.join(output_folder, onss_filename)

    # Load OSS and OnSS data
    oss_data = np.load(oss_file, allow_pickle=True)
    onss_data = np.load(onss_file, allow_pickle=True)

    # Extract coordinates and convert to floats
    oss_coords = oss_data[['Latitude', 'Longitude']].astype(float)
    onss_coords = onss_data[['Latitude', 'Longitude']].astype(float)

    # Convert coordinates from degrees to radians
    oss_coords_rad = np.radians(oss_coords)
    onss_coords_rad = np.radians(onss_coords)

    # Calculate differences in coordinates
    diff_coords = np.subtract.outer(oss_coords_rad, onss_coords_rad)

    # Calculate distance in degrees (considering Earth as a sphere)
    distance_deg = np.linalg.norm(diff_coords, axis=-1)

    # Convert distance in degrees to distance in kilometers
    # Average Earth radius is about 6371 km
    distance_km = distance_deg * 6371.0

    # Find indices of potential connections within 300 km
    oss_indices, onss_indices = np.where(distance_km <= 300)

    # Calculate Haversine distances for potential connections
    haversine_distances = haversine_distance_np(
        oss_coords.iloc[oss_indices, 1],  # oss_lon
        oss_coords.iloc[oss_indices, 0],  # oss_lat
        onss_coords.iloc[onss_indices, 1],  # onss_lon
        onss_coords.iloc[onss_indices, 0]   # onss_lat
    )

    # Create array with OSS and OnSS IDs and distances
    oss_ids = oss_data['OSS_ID'][oss_indices]
    onss_ids = onss_data['OnSS_ID'][onss_indices]
    distances_array = np.column_stack((oss_ids, onss_ids, haversine_distances))

    # Save distances to numpy and text files
    np.save(os.path.join(output_folder, 'distances.npy'), distances_array)
    np.savetxt(os.path.join(output_folder, 'distances.txt'), distances_array, fmt='%s', delimiter=',')

# Example usage:
output_folder = r"C:\Users\cflde\Documents\Graduation Project\ArcGIS Pro\BalticSea\Results\datasets"
calculate_distances(output_folder)
