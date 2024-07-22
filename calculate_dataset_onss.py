import arcpy
import os
import numpy as np

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

def gen_dataset(output_folder: str):
    """
    Generates a numpy dataset containing longitude, latitude, AC and DC capacities, and total costs for each OSS_ID.
    """
    
    # Access the current ArcGIS project
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    onss_layer = [layer for layer in map.listLayers() if layer.name.startswith('OnSS')][0]
    
    # Check if any OSSC layer exists
    if not onss_layer:
        arcpy.AddError("No layer starting with 'WTC' found in the current map.")
        return

    # Deselect all currently selected features
    arcpy.SelectLayerByAttribute_management(onss_layer, "CLEAR_SELECTION")

    arcpy.AddMessage(f"Processing layer: {onss_layer.name}")

    # Check if required fields exist in the attribute table
    required_fields = ['ISO','OnSS_ID', 'Longitude', 'Latitude']
    for field in required_fields:
        if field not in [f.name for f in arcpy.ListFields(onss_layer)]:
            arcpy.AddError(f"Required field '{field}' is missing in the attribute table.")
            return

    # Convert attribute table to NumPy array
    array_onss = arcpy.da.FeatureClassToNumPyArray(onss_layer,'*')
    
    # Define data dictionary structure
    dtype = [
        ('OnSS_ID', int),
        ('ISO', 'U2'),  # Changed to 'U2' for 2-letter country codes
        ('Longitude', float),
        ('Latitude', float),
        ('TotalCapacity', int),
    ]
    
    # 3-letter to 2-letter ISO code mapping
    iso_mapping = {
        'DNK': 'DK',
        'EST': 'EE',
        'FIN': 'FI',
        'DEU': 'DE',
        'LVA': 'LV',
        'LTU': 'LT',
        'POL': 'PL',
        'SWE': 'SE'
    }

    # Initialize an empty list to store data dictionaries
    data_list = []

    # Create data dictionaries
    for row in array_onss:
        data_dict = {
            'OnSS_ID': row['OnSS_ID'],
            'ISO': iso_mapping.get(row['ISO'], row['ISO']),  # Convert to 2-letter code
            'Longitude': round(row['Longitude'], 6),
            'Latitude': round(row['Latitude'], 6),
            'TotalCapacity': round(750)
        }
        data_list.append(data_dict)

    # Convert the list of dictionaries to a structured array
    data_array = np.array([(d['OnSS_ID'], d['ISO'], d['Longitude'], d['Latitude'], d['TotalCapacity']) for d in data_list], dtype=dtype)

    # Sort data_array by OnSS_ID
    data_array_sorted = np.sort(data_array, order='OnSS_ID')

    # Save the sorted structured array to a .npy file in the specified folder
    np.save(os.path.join(output_folder, 'onss_data.npy'), data_array_sorted)
    arcpy.AddMessage("Data saved successfully.")

    # Save sorted structured array to a .txt file
    save_structured_array_to_txt(os.path.join(output_folder, 'onss_data.txt'), data_array_sorted)
    arcpy.AddMessage("Data saved successfully.")

if __name__ == "__main__":
    # Prompt the user to input the folder path where they want to save the output files
    output_folder = arcpy.GetParameterAsText(0)
    gen_dataset(output_folder)