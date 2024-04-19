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
        numpy.ndarray: Array of Haversine distances in meters.
    """
    # Radius of the Earth in meters
    r = 6371 * 1e3
    
    # Convert latitude and longitude from degrees to radians
    lon1, lat1, lon2, lat2 = np.radians(lon1), np.radians(lat1), np.radians(lon2), np.radians(lat2)

    # Calculate differences in coordinates
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    # Apply Haversine formula
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))

    # Calculate the distance
    distances = c * r 

    return distances

def save_structured_array_to_txt(filename, structured_array):
    """
    Saves a structured numpy array to a text file, properly handling fields that contain lists.

    Parameters:
    - filename (str): The path to the file where the array should be saved.
    - structured_array (numpy structured array): The array to save, which may contain fields with lists.
    """
    with open(filename, 'w') as file:
        # Write header
        header = ', '.join(structured_array.dtype.names)
        file.write(header + '\n')

        # Write data rows
        for row in structured_array:
            row_data = []
            for value in row:
                if isinstance(value, np.ndarray) or isinstance(value, list):
                    # Convert list or ndarray to a string representation
                    list_str = '[' + ', '.join(str(v) for v in value) + ']'
                    row_data.append(list_str)
                else:
                    row_data.append(str(value))
            row_str = ', '.join(row_data)
            file.write(row_str + '\n')

def gen_dataset(output_folder: str):
    """
    Calculate the Haversine distances between OSS and OnSS datasets within 300 km, including calculating
    and storing the total costs and power efficiencies for various capacities in HVAC and HVDC systems.

    Parameters:
        output_folder (str): The folder path where the OSS and OnSS datasets and the results will be saved.
    """
    # Define capacities for which costs are to be calculated
    capacities = np.arange(500, 2500 + 100, 100)  # From 500 MW to 2500 MW, step size 100 MW
    voltage = 400 # kV

    # OSS and OnSS file names
    oss_filename = "oss_data.npy"
    onss_filename = "onss_data.npy"

    # Construct full file paths
    oss_file = os.path.join(output_folder, oss_filename)
    onss_file = os.path.join(output_folder, onss_filename)

    # Load OSS and OnSS data
    oss_data = np.load(oss_file, allow_pickle=True)
    onss_data = np.load(onss_file, allow_pickle=True)

    # Extract coordinates
    oss_coords = oss_data[['Latitude', 'Longitude']]
    onss_coords = onss_data[['Latitude', 'Longitude']]

    # Initialize lists to store results
    results_list = []

    # Initialize counter for export cable indices
    export_cable_index = 0

    # Calculate distances and costs
    for i in range(len(oss_coords)):
        for j in range(len(onss_coords)):
            # Calculate Haversine distance
            haversine_distance = haversine_distance_np(
                oss_coords[i][1],  # oss_lon
                oss_coords[i][0],  # oss_lat
                onss_coords[j][1],  # onss_lon
                onss_coords[j][0]   # onss_lat
            )

            # Check if distance is within 300 km
            if haversine_distance <= 300 * 1e3:
                
                # Add results to the results list
                results_list.append((
                    export_cable_index,
                    oss_data['OSS_ID'][i],
                    onss_data['OnSS_ID'][j],
                    np.round(haversine_distance)
                ))

                # Increment the export cable index
                export_cable_index += 1

    # Define the dtype for the structured array, allowing for object types in costs and efficiencies
    dtype = [
        ('EC_ID', np.int32), 
        ('OSS_ID', np.int32), 
        ('OnSS_ID', np.int32), 
        ('Distance', np.int32)
    ]

    # Create structured array
    data_array = np.array(results_list, dtype=dtype)

    # Save structured array to .npy and .txt files
    np.save(os.path.join(output_folder, 'ec_data.npy'), data_array)
    
    save_structured_array_to_txt(os.path.join(output_folder, 'ec_data.txt'), data_array)

# Example usage:
output_folder = r"C:\Users\cflde\Documents\Graduation Project\ArcGIS Pro\BalticSea\Results\datasets"
gen_dataset(output_folder)

