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
    oss_coords = oss_data[['Latitude', 'Longitude']]
    onss_coords = onss_data[['Latitude', 'Longitude']]

    # Initialize dictionaries to store distances and corresponding indices
    distances_dict = {}
    oss_indices_dict = {}
    onss_indices_dict = {}

    # Iterate over each combination of OSS and OnSS coordinates
    for i in range(len(oss_coords)):
        for j in range(len(onss_coords)):
            # Calculate Haversine distance for current combination
            haversine_distance = haversine_distance_np(
                oss_coords[i][1],  # oss_lon
                oss_coords[i][0],  # oss_lat
                onss_coords[j][1],  # onss_lon
                onss_coords[j][0]   # onss_lat
            )
            # Round the distance to 3 decimals
            rounded_distance = np.round(haversine_distance, decimals=3)
            # If distance is within 300 km and not already stored, add it to the dictionaries
            if rounded_distance <= 300:
                key = (int(i), int(j))  # Convert indices to integers
                if key not in distances_dict:
                    distances_dict[key] = rounded_distance
                    oss_indices_dict[key] = int(i)  # Convert index to integer
                    onss_indices_dict[key] = int(j)  # Convert index to integer

    # Create arrays with OSS and OnSS IDs and distances
    oss_indices = list(oss_indices_dict.values())
    onss_indices = list(onss_indices_dict.values())
    distances = list(distances_dict.values())
    oss_ids = oss_data['OSS_ID'][oss_indices]
    onss_ids = onss_data['OnSS_ID'][onss_indices]
    distances_array = np.column_stack((oss_ids, onss_ids, distances))

    # Save distances to numpy and text files
    np.save(os.path.join(output_folder, 'distances.npy'), distances_array)
    np.savetxt(os.path.join(output_folder, 'distances.txt'), distances_array, fmt='%s', delimiter=',')

# Example usage:
output_folder = r"C:\Users\cflde\Documents\Graduation Project\ArcGIS Pro\BalticSea\Results\datasets"
calculate_distances(output_folder)


