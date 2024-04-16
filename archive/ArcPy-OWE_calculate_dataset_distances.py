import numpy as np
import os
#import arcpy

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

def save_structured_array_to_txt(filename, structured_array):
    """
    Saves a structured numpy array to a text file.

    Parameters:
    - filename (str): The path to the file where the array should be saved.
    - structured_array (numpy structured array): The array to save.
    """
    # Open the file in write mode
    with open(filename, 'w') as file:
        # Write header
        header = ', '.join(structured_array.dtype.names)
        file.write(header + '\n')

        # Write data rows
        for row in structured_array:
            row_str = ', '.join(str(value) for value in row)
            file.write(row_str + '\n')

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

    # Initialize dictionaries to store distances, corresponding indices, and export cable indices
    distances_dict = {}
    oss_indices_dict = {}
    onss_indices_dict = {}
    export_cable_indices_dict = {}

    # Initialize counter for export cable indices
    export_cable_index = 0

    # Initialize lists to store indices and distances
    oss_indices = []
    onss_indices = []
    distances = []
    export_cable_indices = []

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
            # If distance is within 300 km, add it to the lists and dictionaries
            if haversine_distance <= 300:
                key = (int(i), int(j))  # Convert indices to integers
                if key not in distances_dict:
                    rounded_distance = np.round(haversine_distance * 1e3)
                    distances_dict[key] = int(rounded_distance)
                    oss_indices_dict[key] = int(i)  # Convert index to integer
                    onss_indices_dict[key] = int(j)  # Convert index to integer

                    # Store export cable index and increment the counter
                    export_cable_indices_dict[key] = export_cable_index
                    export_cable_index += 1

                    # Append indices and distances to lists
                    oss_indices.append(int(i))
                    onss_indices.append(int(j))
                    distances.append(int(rounded_distance))
                    export_cable_indices.append(export_cable_index)

    # Create structured array with OSS and OnSS IDs, distances, and export cable indices
    dtype = [('EC_ID', int), ('OSS_ID', int), ('OnSS_ID', int), ('Distance', int)]
    data_list = [(export_cable_indices[i], oss_data['OSS_ID'][oss_indices[i]], onss_data['OnSS_ID'][onss_indices[i]], distances[i]) for i in range(len(distances))]
    data_array = np.array(data_list, dtype=dtype)

    # Save structured array to .npy file
    np.save(os.path.join(output_folder, 'ec_data.npy'), data_array)
    #arcpy.AddMessage("Data saved successfully.")

    # Save structured array to .txt file
    save_structured_array_to_txt(os.path.join(output_folder, 'ec_data.txt'), data_array)
    #arcpy.AddMessage("Data saved successfully.")

# Example usage:
output_folder = r"C:\Users\cflde\Documents\Graduation Project\ArcGIS Pro\BalticSea\Results\datasets"
calculate_distances(output_folder)


